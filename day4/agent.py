import os
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool
from livekit.plugins import deepgram, google, murf, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import memory


# Load API keys from .env
load_dotenv()

# Initialize SQLite memory database
memory.init_db()


class VoiceAgent(Agent):

    def __init__(self, user_id: str):

        self.user_id = user_id

        # Get memories from previous conversations
        previous_memories = memory.get_memories(user_id)

        if previous_memories:
            memories_text = "\n".join(
                f"- {item}" for item in previous_memories
            )
        else:
            memories_text = "No previous memories are available."

        instructions = f"""
You are a friendly multilingual AI voice assistant.

You have persistent memory.

Here are memories from previous conversations:

{memories_text}

Use these memories naturally when they are relevant.

If the user tells you an important personal preference,
fact, name, goal, interest, or other useful information,
save it using the save_memory tool.

Do not save passwords, API keys, financial information,
or highly sensitive personal information.

LANGUAGE & SCRIPT

Always write every language in its own native script.

- Hindi → Devanagari (नमस्ते)
- Never write Hindi using English/Roman letters.
- Gujarati → Gujarati script.
- English → English.
- Other languages → use their native script.

Always reply in the language the user is speaking.

Be friendly, concise, and natural because you are a
voice assistant.

The user should feel that you remember them between
conversations.
"""

        super().__init__(instructions=instructions)

    @function_tool
    async def save_memory(self, memory_text: str):
        """
        Save useful information about the user for future conversations.
        """

        memory.save_memory(
            self.user_id,
            memory_text
        )

        return f"I'll remember that: {memory_text}"


async def entrypoint(ctx: agents.JobContext):

    # Connect to LiveKit room
    await ctx.connect()

    # Create voice session
    session = AgentSession(

        # Speech-to-text
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        # Gemini LLM
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

    # Create agent
    agent = VoiceAgent(
        user_id=ctx.room.name
    )

    # Start session
    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            audio_enabled=True,
        ),
    )

    # Initial greeting
    await session.generate_reply(
        instructions="""
        Greet the user warmly.
        Introduce yourself as a multilingual AI voice assistant
        with persistent memory.
        Keep the greeting short.
        """
    )


def prewarm(proc: agents.JobProcess):

    # Load Silero VAD
    proc.userdata["vad"] = silero.VAD.load()


if __name__ == "__main__":

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,

            # IMPORTANT:
            # This gives your worker an explicit name
            # so it can be selected in LiveKit Console.
            agent_name="day4-memory-agent",
        )
    )