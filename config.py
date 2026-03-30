"""Global configuration for MusicLens."""

# Whisper model size: "tiny", "base", "small", "medium", "large"
# "base" is recommended for CPU, "medium" or "large" for GPU
WHISPER_MODEL_SIZE = "base"

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
