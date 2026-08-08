"""
utils.py
========
Utility functions for text formatting, logging, and TTS optimization.
"""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BharatSathi")


def sanitize_for_tts(text: str) -> str:
    """
    Strips markdown symbols, bullet points, and unexpected special characters
    to ensure smooth synthesis by TTS engines like Murf.
    """
    if not text:
        return ""

    # Remove bold, italics, code blocks, headers
    cleaned = re.sub(r"[\*\_~`#\-\>]", " ", text)
    
    # Replace numbered lists (e.g., '1. ', '2. ') with simple pauses
    cleaned = re.sub(r"\d+\.\s+", " ", cleaned)

    # Normalize multiple whitespace characters into a single space
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned