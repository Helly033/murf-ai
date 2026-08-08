"""
main.py
=======
Entry point for the Murf AI Voice for Bharat Challenge Agent (Day 2).
"""

import asyncio
from livekit.agents import JobContext, WorkerOptions, cli
from agent import BharatSathiAgent
from utils import logger


async def entrypoint(ctx: JobContext):
    """
    LiveKit job worker entrypoint.
    """
    logger.info(f"Connecting BharatSathi to Room: {ctx.room.name}")
    await ctx.connect()
    
    # Initialize and run agent
    sathi_agent = BharatSathiAgent(ctx)
    await sathi_agent.start()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )