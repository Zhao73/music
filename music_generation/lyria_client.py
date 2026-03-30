"""Google Lyria 3 Pro API client for music generation.

Wraps the google-genai SDK to generate music from text prompts.
Gracefully degrades if the SDK is not installed or no API key is set.
"""

import os
import tempfile
import base64
from dataclasses import dataclass

from config import LYRIA_MODEL, GEMINI_API_KEY


@dataclass
class GenerationResult:
    audio_path: str = ""          # Path to generated audio file
    duration_seconds: float = 0.0
    success: bool = False
    error: str = ""
    mime_type: str = ""


def is_available(api_key: str = None) -> bool:
    """Check if Lyria generation is available (SDK installed + API key)."""
    try:
        from google import genai  # noqa: F401
    except ImportError:
        return False

    key = api_key or GEMINI_API_KEY
    return bool(key)


def generate_music(prompt: str, api_key: str = None) -> GenerationResult:
    """Generate music using Google Lyria 3 Pro.

    Args:
        prompt: Text prompt describing the music to generate.
        api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.

    Returns:
        GenerationResult with path to generated audio file.
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        return GenerationResult(
            error="No API key provided. Set GEMINI_API_KEY environment variable or enter it in the UI.",
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return GenerationResult(
            error="google-genai package not installed. Run: pip install google-genai",
        )

    try:
        client = genai.Client(api_key=key)

        response = client.models.generate_content(
            model=LYRIA_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
            ),
        )

        # Extract audio data from response
        if not response.candidates:
            return GenerationResult(error="No response from Lyria API.")

        parts = response.candidates[0].content.parts
        if not parts:
            return GenerationResult(error="Empty response from Lyria API.")

        audio_part = None
        for part in parts:
            if hasattr(part, "inline_data") and part.inline_data:
                audio_part = part
                break

        if not audio_part:
            return GenerationResult(error="No audio data in Lyria response.")

        inline_data = audio_part.inline_data
        mime_type = getattr(inline_data, "mime_type", "audio/wav")
        audio_bytes = inline_data.data

        # Handle base64 encoding if needed
        if isinstance(audio_bytes, str):
            audio_bytes = base64.b64decode(audio_bytes)

        # Determine file extension from mime type
        ext_map = {
            "audio/wav": ".wav",
            "audio/wave": ".wav",
            "audio/x-wav": ".wav",
            "audio/mp3": ".mp3",
            "audio/mpeg": ".mp3",
            "audio/ogg": ".ogg",
            "audio/flac": ".flac",
        }
        ext = ext_map.get(mime_type, ".wav")

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False, prefix="lyria_") as f:
            f.write(audio_bytes)
            audio_path = f.name

        # Estimate duration (rough: file_size / bytes_per_second)
        # More accurate would be to read the actual audio, but this is fast
        duration_est = len(audio_bytes) / (48000 * 2 * 2)  # 48kHz, 16-bit, stereo

        return GenerationResult(
            audio_path=audio_path,
            duration_seconds=duration_est,
            success=True,
            mime_type=mime_type,
        )

    except Exception as e:
        return GenerationResult(error=f"Lyria API error: {str(e)}")
