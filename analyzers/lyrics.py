"""Lyrics extraction using OpenAI Whisper."""

from dataclasses import dataclass, field

from config import WHISPER_MODEL_SIZE


@dataclass
class LyricsResult:
    full_text: str
    segments: list[dict] = field(default_factory=list)
    detected_language: str = ""


_model = None
WHISPER_AVAILABLE = True

try:
    import whisper
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None


def _get_model():
    global _model
    if not WHISPER_AVAILABLE:
        raise RuntimeError(
            "openai-whisper is not installed. "
            "Install it with: pip install openai-whisper"
        )
    if _model is None:
        _model = whisper.load_model(WHISPER_MODEL_SIZE)
    return _model


def extract_lyrics(audio_path: str, language: str = None) -> LyricsResult:
    """Transcribe lyrics from an audio file.

    Args:
        audio_path: Path to the audio file.
        language: Language code (e.g., 'zh', 'en'). None for auto-detect.

    Returns:
        LyricsResult with full text, timed segments, and detected language.
    """
    model = _get_model()

    options = {}
    if language and language != "auto":
        options["language"] = language

    result = model.transcribe(audio_path, **options)

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
        })

    return LyricsResult(
        full_text=result["text"].strip(),
        segments=segments,
        detected_language=result.get("language", ""),
    )
