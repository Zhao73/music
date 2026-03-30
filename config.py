"""Global configuration for MusicLens."""

import os

# ==============================================================
# Audio Analysis Config
# ==============================================================

# Whisper model size: "tiny", "base", "small", "medium", "large"
WHISPER_MODEL_SIZE = "large"

# Default sample rate for audio processing
SAMPLE_RATE = 22050

# Supported audio formats
SUPPORTED_FORMATS = [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".wma", ".aac"]

# Language codes for translation
LANGUAGE_OPTIONS = {
    "auto": "Auto Detect",
    "zh": "Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "it": "Italian",
    "th": "Thai",
}

# ==============================================================
# Lyria Music Generation Config
# ==============================================================

LYRIA_MODEL = "lyria-3-pro-preview"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ==============================================================
# Music Creator UI Options
# ==============================================================

KEY_OPTIONS = [
    "C major", "C minor", "C# major", "C# minor",
    "D major", "D minor", "D# major", "D# minor",
    "E major", "E minor",
    "F major", "F minor", "F# major", "F# minor",
    "G major", "G minor", "G# major", "G# minor",
    "A major", "A minor", "A# major", "A# minor",
    "B major", "B minor",
]

MOOD_OPTIONS = [
    "happy / energetic",
    "peaceful / content",
    "excited / uplifting",
    "powerful / dramatic",
    "calm / ambient",
    "sad / melancholic",
    "angry / intense",
    "tense / anxious",
    "somber / reflective",
    "romantic / emotional",
    "mysterious / dark",
    "playful / fun",
    "epic / cinematic",
    "neutral / moderate",
]

DRUM_GROOVE_OPTIONS = [
    "straight 4/4 rock",
    "straight 8th notes",
    "straight 16th notes",
    "shuffle / swing",
    "half-time",
    "double-time",
    "6/8 ballad",
    "Latin / bossa nova",
    "funk groove",
    "trap hi-hat",
    "sparse percussion",
    "no drums",
]

INSTRUMENT_OPTIONS = [
    "Vocals",
    "Piano / Keys",
    "Acoustic Guitar",
    "Electric Guitar",
    "Bass",
    "Drums / Percussion",
    "Strings",
    "Synthesizer / Electronic",
    "Brass (Trumpet, Sax)",
    "Flute / Woodwinds",
    "Violin / Cello",
    "Organ",
    "Harp",
    "Ukulele",
    "Mandolin",
]

VOCAL_STYLE_OPTIONS = [
    "vibrato-rich",
    "straight-tone",
    "breathy",
    "bright",
    "warm",
    "dynamic",
    "falsetto/head-voice",
    "chest-voice-dominant",
    "legato",
    "rhythmic-articulation",
    "raspy/gritty",
    "smooth",
    "powerful belting",
    "whisper/soft",
]
