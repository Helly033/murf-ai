"""
agent.py
========
Defines the LiveKit VoicePipelineAgent and session orchestration for BharatSathi.
"""

import logging
from livekit.agents import JobContext, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, deepgram, silero, murf

from prompts import SYSTEM_PROMPT, GREETING_TEXT
from utils import sanitize_for_tts, logger


class BharatSathiAgent:
    """
    Encapsulates the BharatSathi Voice Pipeline Agent configuration.
    """

    def __init__(self, ctx: JobContext):
        self.ctx = ctx

    async def start(self):
        logger.info("Initializing BharatSathi Voice Pipeline Agent...")

        # Initialize the voice pipeline with STT, LLM, TTS, and VAD plugins
        initial_ctx = llm.ChatContext().append(
            role="system",
            text=SYSTEM_PROMPT,
        )

        agent = VoicePipelineAgent(
            vad=silero.VAD.load(),
            stt=deepgram.STT(model="nova-2", language="multi"),
            llm=openai.LLM(model="gpt-4o-mini", temperature=0.6),
            tts=murf.TTS(),  # Integrates Murf AI TTS plugin
            chat_ctx=initial_ctx,
            allow_interruptions=True,
        )

        # Hook to clean text prior to voice synthesis
        @agent.on("user_speech_committed")
        def on_user_speech(msg: llm.ChatMessage):
            logger.info(f"User Speech Recognized: {msg.content}")

        @agent.on("agent_speech_committed")
        def on_agent_speech(msg: llm.ChatMessage):
            logger.info(f"BharatSathi Response: {msg.content}")

        # Start the agent in the LiveKit room
        agent.start(self.ctx.room)

        # Send initial spoken greeting to the user
        await agent.say(sanitize_for_tts(GREETING_TEXT), allow_interruptions=True)