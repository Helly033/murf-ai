import asyncio
import json
import logging
import os

from dotenv import load_dotenv
from livekit import api

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
)

from livekit.plugins import deepgram, google, murf, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel


load_dotenv(".env")

# =========================================================
# CONFIGURATION
# =========================================================

OUTBOUND_TRUNK_ID = os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK_ID")

logger = logging.getLogger("outbound-agent")

CALLEE_IDENTITY = "phone-user"

GREETING = (
    "Hello! I'm calling for a quick check-in. "
    "Is this a good time to talk?"
)

SYSTEM_PROMPT = """
You are a friendly multilingual AI voice assistant making an outbound phone call.

You are powered by Murf Falcon for voice generation.

Be natural, friendly, concise, and conversational.

Keep responses short because this is a phone conversation.

Do not repeatedly introduce yourself.

Wait for the caller to finish speaking before responding.

LANGUAGE & SCRIPT:

Always write every language in its own native script.

Hindi → Devanagari script.
Example: नमस्ते

Gujarati → Gujarati script.
Example: નમસ્તે

English → English.

Never write Hindi or Gujarati using English/Roman letters.

Always reply in the language the person is speaking.

If the person asks to stop receiving calls,
politely acknowledge the request.

Keep responses short and natural.
"""


# =========================================================
# AGENT
# =========================================================

class OutboundAgent(Agent):

    def __init__(self, ctx: JobContext):
        super().__init__(
            instructions=SYSTEM_PROMPT
        )
        self.ctx = ctx


# =========================================================
# SERVER
# =========================================================

server = AgentServer()


# =========================================================
# PREWARM
# =========================================================

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


# =========================================================
# GET PHONE NUMBER
# =========================================================

def get_phone_number(ctx: JobContext):

    metadata = ctx.job.metadata

    if not metadata:
        return None

    try:
        data = json.loads(metadata)
        return data.get("phone_number")

    except json.JSONDecodeError:
        return metadata.strip()


# =========================================================
# OUTBOUND AGENT
# =========================================================

@server.rtc_session(agent_name="outbound-agent")
async def outbound_agent(ctx: JobContext):

    phone_number = get_phone_number(ctx)

    if not phone_number:
        logger.error(
            "No phone number found in dispatch metadata."
        )
        ctx.shutdown()
        return

    if not OUTBOUND_TRUNK_ID:
        logger.error(
            "LIVEKIT_SIP_OUTBOUND_TRUNK_ID is not set."
        )
        ctx.shutdown()
        return

    logger.info(
        "Preparing outbound call to %s",
        phone_number
    )

    # -----------------------------------------------------
    # CONNECT
    # -----------------------------------------------------

    await ctx.connect()

    # -----------------------------------------------------
    # AGENT SESSION
    # -----------------------------------------------------

    session = AgentSession(

        # Deepgram STT
        # English temporarily for troubleshooting
        stt=deepgram.STT(
            model="nova-3",
            language="en",
            interim_results=True,
        ),

        # Gemini
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # Murf Falcon
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            text_pacing=False,
        ),

        # Turn detection
        turn_detection=MultilingualModel(),

        # VAD
        vad=ctx.proc.userdata["vad"],

        # Prevent early responses
        preemptive_generation=False,
    )

    # -----------------------------------------------------
    # START SESSION
    # -----------------------------------------------------

    session_started = asyncio.create_task(
        session.start(
            agent=OutboundAgent(ctx),
            room=ctx.room,
            room_options=room_io.RoomOptions(),
        )
    )

    logger.info(
        "Dialing %s",
        phone_number
    )

    # -----------------------------------------------------
    # CREATE SIP CALL
    # -----------------------------------------------------

    try:

        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=OUTBOUND_TRUNK_ID,
                sip_call_to=phone_number,
                participant_identity=CALLEE_IDENTITY,
                participant_name="Phone User",
                wait_until_answered=True,
            )
        )

    except Exception as e:

        logger.error(
            "Outbound call failed: %s",
            e
        )

        session_started.cancel()

        ctx.shutdown()

        return

    # -----------------------------------------------------
    # WAIT FOR SESSION
    # -----------------------------------------------------

    await session_started

    # -----------------------------------------------------
    # GREETING
    # -----------------------------------------------------

    logger.info("Speaking greeting")

    await session.say(
        GREETING,
        allow_interruptions=True,
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    cli.run_app(server)