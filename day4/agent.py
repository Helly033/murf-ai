
import os
import requests
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


WEATHER TOOL

You have access to a weather tool that provides live
weather information.

When the user asks about current weather, temperature,
humidity, wind, rain, or weather conditions for a city,
use the get_weather tool.

Do not guess or invent weather information.

Always use the tool for current weather information.

If the weather service fails, clearly tell the user that
the latest weather information is temporarily unavailable.

Mention that the weather information comes from Open-Meteo
when appropriate.


GENERAL BEHAVIOR

Be friendly, concise, and natural because you are a
voice assistant.

The user should feel that you remember them between
conversations.
"""

        super().__init__(instructions=instructions)


    # ---------------------------------------------------------
    # DAY 4 TOOL: SAVE MEMORY
    # ---------------------------------------------------------

    @function_tool
    async def save_memory(self, memory_text: str):
        """
        Save useful information about the user for future
        conversations.
        """

        memory.save_memory(
            self.user_id,
            memory_text
        )

        return f"I'll remember that: {memory_text}"


    # ---------------------------------------------------------
    # DAY 5 TOOL: GET WEATHER
    # ---------------------------------------------------------

    @function_tool
    async def get_weather(self, city: str) -> str:
        """
        Get the current weather for a city.

        Use this tool whenever the user asks about current
        weather, temperature, humidity, wind, rain, or weather
        conditions for a specific city.

        The tool uses live weather data from Open-Meteo.
        """

        try:

            # -------------------------------------------------
            # STEP 1: Find latitude and longitude of the city
            # -------------------------------------------------

            geocode_url = (
                "https://geocoding-api.open-meteo.com/v1/search"
            )

            geocode_params = {
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            }

            geocode_response = requests.get(
                geocode_url,
                params=geocode_params,
                timeout=10,
            )

            if geocode_response.status_code != 200:

                return (
                    "I couldn't access the location service "
                    "right now. Please try again later."
                )

            geocode_data = geocode_response.json()

            if not geocode_data.get("results"):

                return (
                    f"I couldn't find weather information "
                    f"for {city}. Please provide a valid city name."
                )

            location = geocode_data["results"][0]

            latitude = location["latitude"]
            longitude = location["longitude"]

            city_name = location.get("name", city)
            country = location.get("country", "")


            # -------------------------------------------------
            # STEP 2: Get current weather
            # -------------------------------------------------

            weather_url = (
                "https://api.open-meteo.com/v1/forecast"
            )

            weather_params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,"
                    "relative_humidity_2m,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            }

            weather_response = requests.get(
                weather_url,
                params=weather_params,
                timeout=10,
            )

            if weather_response.status_code != 200:

                return (
                    "I couldn't access the latest weather data "
                    "right now. Please try again later."
                )

            weather_data = weather_response.json()

            current = weather_data["current"]

            temperature = current["temperature_2m"]
            humidity = current["relative_humidity_2m"]
            wind_speed = current["wind_speed_10m"]
            weather_code = current["weather_code"]
            observation_time = current["time"]


            # -------------------------------------------------
            # STEP 3: Convert weather code to description
            # -------------------------------------------------

            weather_descriptions = {

                0: "clear sky",

                1: "mainly clear",

                2: "partly cloudy",

                3: "overcast",

                45: "foggy",

                48: "foggy",

                51: "light drizzle",

                53: "moderate drizzle",

                55: "heavy drizzle",

                61: "light rain",

                63: "moderate rain",

                65: "heavy rain",

                71: "light snow",

                73: "moderate snow",

                75: "heavy snow",

                80: "light rain showers",

                81: "moderate rain showers",

                82: "heavy rain showers",

                95: "thunderstorm",

                96: "thunderstorm with hail",

                99: "thunderstorm with heavy hail",
            }

            condition = weather_descriptions.get(
                weather_code,
                "unknown weather conditions"
            )


            # -------------------------------------------------
            # STEP 4: Return natural spoken result
            # -------------------------------------------------

            return (
                f"The current weather in "
                f"{city_name}, {country} is "
                f"{temperature} degrees Celsius with "
                f"{condition}. "

                f"Humidity is {humidity} percent and "
                f"wind speed is {wind_speed} kilometers "
                f"per hour. "

                f"The latest observation time is "
                f"{observation_time}. "

                f"Source: Open-Meteo."
            )


        # -----------------------------------------------------
        # Handle API/network errors
        # -----------------------------------------------------

        except requests.RequestException:

            return (
                "I'm sorry, I couldn't access the latest "
                "weather data right now. "
                "Please try again later."
            )


        # -----------------------------------------------------
        # Handle unexpected errors
        # -----------------------------------------------------

        except Exception:

            return (
                "I'm sorry, something went wrong while "
                "getting the weather. Please try again later."
            )


# =============================================================
# LIVEKIT ENTRYPOINT
# =============================================================

async def entrypoint(ctx: agents.JobContext):

    # Connect to LiveKit room
    await ctx.connect()


    # ---------------------------------------------------------
    # Create voice session
    # ---------------------------------------------------------

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


    # ---------------------------------------------------------
    # Create agent
    # ---------------------------------------------------------

    agent = VoiceAgent(
        user_id=ctx.room.name
    )


    # ---------------------------------------------------------
    # Start session
    # ---------------------------------------------------------

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            audio_enabled=True,
        ),
    )


    # ---------------------------------------------------------
    # Initial greeting
    # ---------------------------------------------------------

    await session.generate_reply(
        instructions="""
        Greet the user warmly.

        Introduce yourself as a multilingual AI voice assistant
        with persistent memory and live weather information.

        Keep the greeting short.
        """
    )


# =============================================================
# PREWARM
# =============================================================

def prewarm(proc: agents.JobProcess):

    # Load Silero VAD
    proc.userdata["vad"] = silero.VAD.load()


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    agents.cli.run_app(
        agents.WorkerOptions(

            entrypoint_fnc=entrypoint,

            prewarm_fnc=prewarm,

            # Agent name used in LiveKit Console
            agent_name="day4-memory-agent",
        )
    )
