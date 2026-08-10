import os
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

You have persistent memory.

Here are memories from previous conversations:

{memories_text}

Use these memories naturally when they are relevant.

If the user tells you an important personal preference,
fact, name, goal, interest, or other useful information,
save it using the save_memory tool.

Do not save passwords, API keys, financial information,
or highly sensitive personal information.

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

Other languages → use their native script.

Always reply in the language the user is speaking.

---------------------------------------------------------
WEATHER TOOL
---------------------------------------------------------

You have access to a weather tool.

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
VOICE BEHAVIOR
---------------------------------------------------------

Be friendly, concise, and natural.

You are a voice assistant, so keep responses relatively
short and conversational.

Do not give unnecessarily long explanations.

The user should feel that you remember them between
conversations.
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

    # Load Silero VAD
    proc.userdata["vad"] = silero.VAD.load()


# ---------------------------------------------------------
# Run LiveKit Agent
# ---------------------------------------------------------

if __name__ == "__main__":

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,

            # Must match frontend LiveKit agent dispatch
            agent_name="day4-memory-agent",
        )
    )