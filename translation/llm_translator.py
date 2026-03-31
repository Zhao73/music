"""LLM-powered intelligent lyrics translation using Google Gemini.

Produces singable translations that preserve syllable count, rhyme,
emotional tone, and musical context — far beyond machine translation.
"""

from dataclasses import dataclass

LLM_AVAILABLE = True
try:
    from google import genai
except ImportError:
    LLM_AVAILABLE = False
    genai = None


@dataclass
class MusicalContext:
    """Musical context for intelligent translation."""
    bpm: float = 120.0
    key: str = ""
    mood: str = ""
    emotional_arc: str = ""
    vocal_style: str = ""
    melody_contour: str = ""
    sections: list = None
    # Per-line syllable counts from original
    syllable_hints: list = None


def _count_syllables_rough(text: str, lang: str = "zh") -> int:
    """Rough syllable count for different languages."""
    text = text.strip()
    if not text:
        return 0
    if lang in ("zh", "ja", "ko"):
        # CJK: roughly 1 syllable per character
        return sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or
                   '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or
                   '\uac00' <= c <= '\ud7af')
    # Western: count vowel groups
    import re
    return max(1, len(re.findall(r'[aeiouyàáâãäåèéêëìíîïòóôõöùúûü]+', text.lower())))


def _annotate_lyrics_with_syllables(lyrics: str, source_lang: str) -> str:
    """Add syllable count annotation to each line."""
    lines = lyrics.strip().split("\n")
    annotated = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("["):
            annotated.append(stripped)
            continue
        count = _count_syllables_rough(stripped, source_lang)
        annotated.append(f"{stripped}  [~{count} syllables]")
    return "\n".join(annotated)


def translate_lyrics_intelligent(
    lyrics: str,
    source_lang: str,
    target_lang: str,
    api_key: str,
    musical_context: MusicalContext = None,
    model: str = "gemini-2.0-flash",
) -> str:
    """Translate lyrics using LLM with full musical context.

    Returns translated lyrics text, or raises on failure.
    """
    if not LLM_AVAILABLE:
        raise RuntimeError("google-genai SDK not installed")
    if not api_key:
        raise ValueError("API key required for intelligent translation")

    ctx = musical_context or MusicalContext()
    annotated = _annotate_lyrics_with_syllables(lyrics, source_lang)

    lang_names = {
        "zh": "Chinese", "en": "English", "ja": "Japanese", "ko": "Korean",
        "es": "Spanish", "fr": "French", "de": "German", "pt": "Portuguese",
        "ru": "Russian", "ar": "Arabic", "it": "Italian", "th": "Thai",
    }
    src_name = lang_names.get(source_lang, source_lang)
    tgt_name = lang_names.get(target_lang, target_lang)

    prompt = f"""You are an expert music lyrics translator and songwriter. Translate the following {src_name} song lyrics into {tgt_name}.

CRITICAL RULES:
1. Each translated line MUST have a similar syllable count to the original (marked in brackets). This is essential for singability.
2. Preserve the rhyme scheme — if the original rhymes AABB, the translation should too.
3. Maintain the emotional tone: {ctx.mood or 'as in original'}
4. Emotional arc of the song: {ctx.emotional_arc or 'follow the original flow'}
5. The translation must be SINGABLE — avoid awkward consonant clusters, prefer open vowels at phrase ends.
6. Preserve ALL section markers like [Verse 1], [Chorus], [Intro] etc. — do NOT translate these.
7. Mark instrumental sections as (instrumental) — do NOT translate these.
8. Capture the MEANING and FEELING, not literal word-for-word translation.
9. Adapt cultural references naturally for {tgt_name} speakers.

SONG CONTEXT:
- BPM: {ctx.bpm:.0f} ({"slow ballad" if ctx.bpm < 80 else "moderate" if ctx.bpm < 120 else "upbeat"})
- Key: {ctx.key}
- Vocal Style: {ctx.vocal_style or 'natural'}
- Melody Direction: {ctx.melody_contour or 'varies'}

ORIGINAL LYRICS ({src_name}) — syllable counts annotated:
{annotated}

OUTPUT REQUIREMENTS:
- Return ONLY the translated lyrics, nothing else.
- Keep the same line-by-line structure.
- Keep all [Section] markers unchanged.
- Do NOT add explanations or notes."""

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    if not response or not response.text:
        raise RuntimeError("Empty response from LLM")

    return response.text.strip()
