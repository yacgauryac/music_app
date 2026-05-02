"""Configuration de l'application — charge les variables d'environnement."""

import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SUNO_API_KEY = os.getenv("SUNO_API_KEY", "")
DEFAULT_REVERB = os.getenv("DEFAULT_REVERB", "medium")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "fr")

CLAUDE_MODEL = "claude-sonnet-4-20250514"
SAMPLE_RATE = 44100
CHANNELS = 1
EXPORT_BITRATE = "320k"
