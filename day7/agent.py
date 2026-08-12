import os
import uuid
import requests
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    function_tool,
)
from livekit.plugins import deepgram, google, murf, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import memory


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Initialize memory database
# ---------------------------------------------------------

memory.init_db()


# ---------------------------------------------------------
# Voice Agent
# ---------------------------------------------------------

class VoiceAgent(Agent):

    def __init__(self, user_id: str):

        self.user_id = user_id

        # Get previous memories
        previous_memories = memory.get_memories(user_id)

        if previous_memories:
            memories_text = "\n".join(
                f"- {item}" for item in previous_memories
            )
        else:
            memories_text = "No previous memories are available."

        instructions = f"""
You are a friendly multilingual AI voice assistant.

You have persistent memory and a weather tool.

Here are memories from previous conversations:

{memories_text}

Use these memories naturally when relevant.

If the user tells you an important personal preference,
fact, name, goal, interest, or other useful information,
save it using the save_memory tool.

Do not save passwords, API keys, OTPs, PINs, account numbers,
financial credentials, or highly sensitive personal information.

---------------------------------------------------------
LANGUAGE & SCRIPT
---------------------------------------------------------

Always write every language in its own native script.

Hindi → Devanagari script.
Example: नमस्ते

Never write Hindi using English/Roman letters.

Gujarati → Gujarati script.
Example: નમસ્તે

English → English.

Always reply in the language the user is speaking.

---------------------------------------------------------
WEATHER TOOL
---------------------------------------------------------

When the user asks about:

- current weather
- temperature
- weather conditions
- rain
- humidity
- wind
- weather in a city
- today's weather

use the get_weather tool.

Do NOT guess current weather information.

If the user does not provide a city, ask which city
they are asking about.

---------------------------------------------------------
HUMAN HELP / ESCALATION
---------------------------------------------------------

You can request help from a human representative.

Escalate when:

1. The user reports a payment, refund, or order dispute.

2. The user explicitly asks to speak with a human
   representative.

First understand the user's problem.

Before creating a human-help request, explain that you
will share a short summary with a human representative.

Ask for clear permission BEFORE calling create_escalation.

For example:

"I can send a short summary of your issue to a human
representative. It will include what happened, what I
checked, the urgency, your language, and your preferred
follow-up method. May I share this information?"

IMPORTANT:

Never call create_escalation before the user gives
clear permission.

If the user says NO, do not create the request.

If the user says YES, call create_escalation.

Do not send:

- passwords
- OTPs
- PINs
- API keys
- account numbers
- card numbers
- financial credentials
- other sensitive information

Do not send the full conversation.

After create_escalation succeeds:

1. Tell the user the request was created.
2. Give the reference ID.
3. Explain the next step honestly.
4. Do not promise an immediate human response.

---------------------------------------------------------
ESCALATION INFORMATION
---------------------------------------------------------

Collect only useful information.

The summary should contain:

- who needs help
- issue
- what happened
- what the agent already checked
- urgency
- caller language
- preferred follow-up method

Urgency must be:

- low
- medium
- high

Preferred follow-up can be:

- phone
- email
- chat
- not specified

If information is missing, use "not specified".
Never invent information.

---------------------------------------------------------
VOICE BEHAVIOR
---------------------------------------------------------

Be friendly, concise, and natural.

You are a voice assistant, so keep responses short
and conversational.

Do not give unnecessarily long explanations.
"""


        super().__init__(instructions=instructions)


    # -----------------------------------------------------
    # Persistent Memory Tool
    # -----------------------------------------------------

    @function_tool
    async def save_memory(self, memory_text: str):
        """
        Save useful information about the user for
        future conversations.
        """

        memory.save_memory(
            self.user_id,
            memory_text
        )

        return f"I'll remember that: {memory_text}"


    # -----------------------------------------------------
    # Weather Tool
    # -----------------------------------------------------

    @function_tool
    async def get_weather(self, city: str):
        """
        Get current weather information for a city.
        """

        api_key = os.getenv("OPENWEATHER_API_KEY")

        if not api_key:
            return (
                "The weather service is not configured yet. "
                "Please configure the OpenWeather API key."
            )

        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
        }

        try:

            response = requests.get(
                url,
                params=params,
                timeout=10,
            )

            if response.status_code == 404:
                return (
                    f"I couldn't find weather information "
                    f"for {city}."
                )

            if response.status_code != 200:
                return (
                    "I couldn't retrieve the weather right now. "
                    "Please try again."
                )

            data = response.json()

            temperature = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]

            description = data["weather"][0]["description"]

            wind_speed = data.get("wind", {}).get("speed", 0)

            return (
                f"The current weather in {city} is "
                f"{description}. "
                f"The temperature is {temperature:.1f} degrees Celsius, "
                f"it feels like {feels_like:.1f} degrees Celsius, "
                f"humidity is {humidity} percent, "
                f"and wind speed is {wind_speed} meters per second."
            )

        except requests.exceptions.Timeout:

            return (
                "The weather service took too long to respond. "
                "Please try again."
            )

        except requests.exceptions.RequestException:

            return (
                "I couldn't connect to the weather service "
                "right now. Please try again."
            )

        except Exception:

            return (
                "Something went wrong while getting the weather. "
                "Please try again."
            )


    # -----------------------------------------------------
    # Human Escalation Tool
    # -----------------------------------------------------

    @function_tool
    async def create_escalation(
        self,
        who_needs_help: str,
        issue: str,
        what_happened: str,
        what_was_checked: str,
        urgency: str,
        language: str,
        preferred_follow_up: str,
    ):
        """
        Create a human-help request and send a privacy-safe
        summary to Discord.
        """

        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        if not webhook_url:
            return (
                "The human support channel is not configured. "
                "I could not create the request right now."
            )

        # Validate urgency
        urgency = urgency.lower().strip()

        if urgency not in ["low", "medium", "high"]:
            urgency = "medium"

        # Check for sensitive information
        sensitive_terms = [
            "password",
            "otp",
            "one time password",
            "pin",
            "api key",
            "apikey",
            "secret key",
            "account number",
            "card number",
            "credit card",
            "debit card",
        ]

        combined_text = (
            who_needs_help
            + " "
            + issue
            + " "
            + what_happened
            + " "
            + what_was_checked
        ).lower()

        for term in sensitive_terms:
            if term in combined_text:
                return (
                    "I cannot include sensitive information "
                    "in the human-help request. Please provide "
                    "only a general description of the problem."
                )

        # Generate reference ID
        reference_id = (
            f"HELP-{uuid.uuid4().hex[:8].upper()}"
        )

        # Discord message
        discord_message = {
            "content": (
                "🚨 **New Human Help Request**\n\n"
                f"**Reference ID:** {reference_id}\n"
                f"**Who needs help:** {who_needs_help}\n"
                f"**Issue:** {issue}\n"
                f"**What happened:** {what_happened}\n"
                f"**What the agent checked:** {what_was_checked}\n"
                f"**Urgency:** {urgency}\n"
                f"**Caller language:** {language}\n"
                f"**Preferred follow-up:** {preferred_follow_up}"
            )
        }

        # Send to Discord
        try:

            response = requests.post(
                webhook_url,
                json=discord_message,
                timeout=10,
            )

            if response.status_code not in (200, 204):
                return (
                    "I could not create the human-help "
                    "request right now. Please try again later."
                )

            return (
                f"Human-help request created successfully. "
                f"Your reference ID is {reference_id}. "
                f"The request has been sent to the human "
                f"support channel. A human representative "
                f"can follow up using this reference ID."
            )

        except requests.exceptions.RequestException:

            return (
                "I could not connect to the human support "
                "channel right now. Please try again later."
            )


# ---------------------------------------------------------
# LiveKit Entrypoint
# ---------------------------------------------------------

async def entrypoint(ctx: agents.JobContext):

    # Connect to LiveKit room
    await ctx.connect()

    # -----------------------------------------------------
    # Create voice session
    # -----------------------------------------------------

    session = AgentSession(

        # Multilingual Speech-to-Text
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        # Gemini
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        # Murf Falcon TTS
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            text_pacing=True,
        ),

        # Multilingual turn detection
        turn_detection=MultilingualModel(),

        # Voice activity detection
        vad=ctx.proc.userdata["vad"],

        # Generate responses early
        preemptive_generation=True,
    )

    # -----------------------------------------------------
    # Create agent
    # -----------------------------------------------------

    agent = VoiceAgent(
        user_id=ctx.room.name
    )

    # -----------------------------------------------------
    # Start session
    # -----------------------------------------------------

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            audio_enabled=True,
        ),
    )

    # -----------------------------------------------------
    # Initial greeting
    # -----------------------------------------------------

    await session.generate_reply(
        instructions="""
Greet the user warmly.

Introduce yourself as a multilingual AI voice assistant
with persistent memory and a weather tool.

Keep the greeting short and natural.

Do not explain the technical implementation.
"""
    )


# ---------------------------------------------------------
# Prewarm
# ---------------------------------------------------------

def prewarm(proc: agents.JobProcess):

    proc.userdata["vad"] = silero.VAD.load()


# ---------------------------------------------------------
# Run LiveKit Agent
# ---------------------------------------------------------

if __name__ == "__main__":

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,

            # Keep the same agent name used by your frontend
            agent_name="day4-memory-agent",
        )
    )