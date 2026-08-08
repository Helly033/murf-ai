# Voice for Bharat Challenge 2026 - Day 2: BharatSathi

## Overview
**BharatSathi** is an AI-powered, multilingual voice assistant designed specifically for Indian users. Developed for the **Murf AI Voice for Bharat Challenge 2026**, BharatSathi provides clear, friendly, and safe guidance on education, government services, technology, travel, and everyday queries using natural code-mixed conversations (English, Hindi, and Hinglish).

---

## Day 2 Refactoring & Features
1. **Externalized System Prompt (`prompts.py`)**: Prompts and system instructions are decoupled from execution logic.
2. **Distinct Persona**: BharatSathi acts as a warm, patient, and professional assistant.
3. **Voice Optimization**: Responses are strictly formulated without markdown or complex lists to maintain natural speech flow (80–120 words max).
4. **Code-Mixed Language Support**: Automatically adapts to Hindi, English, or Hinglish based on user input.
5. **Strict Guardrails & Red Team Defense**: Handles requests safely, declining to ask for or process sensitive information (PINs, OTPs, CVVs, medical advice, fake document generation).

---

## Project Structure
```text
voice-for-bharat-day2/
│
├── prompts.py     # System prompt, guardrails, and greeting message
├── agent.py       # LiveKit VoicePipelineAgent configuration
├── main.py        # Worker entry point
├── utils.py       # Sanitization helper functions for TTS output
├── README.md      # Documentation and instructions
└── requirements.txt