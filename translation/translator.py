"""Lyrics translation — Simple (Google Translate) or Intelligent (LLM)."""

from dataclasses import dataclass

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False


@dataclass
class TranslationResult:
    original: str
    translated: str
    source_lang: str
    target_lang: str
    mode: str = "simple"  # "simple" or "intelligent"


# Language code mapping for deep-translator
LANG_MAP = {
    "zh": "zh-CN",
    "en": "en",
    "ja": "ja",
    "ko": "ko",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "pt": "pt",
    "ru": "ru",
    "ar": "ar",
    "it": "it",
    "th": "th",
}


def translate_lyrics(
    text: str,
    source_lang: str,
    target_lang: str,
    mode: str = "simple",
    api_key: str = "",
    musical_context=None,
) -> TranslationResult:
    """Translate lyrics with mode routing.

    Args:
        mode: "simple" (Google Translate) or "intelligent" (LLM with musical context)
        api_key: Required for intelligent mode (Gemini API key)
        musical_context: MusicalContext object for intelligent mode
    """
    # Try intelligent mode first if requested
    if mode == "intelligent" and api_key:
        try:
            from translation.llm_translator import translate_lyrics_intelligent
            translated = translate_lyrics_intelligent(
                lyrics=text,
                source_lang=source_lang,
                target_lang=target_lang,
                api_key=api_key,
                musical_context=musical_context,
            )
            return TranslationResult(
                original=text,
                translated=translated,
                source_lang=source_lang,
                target_lang=target_lang,
                mode="intelligent",
            )
        except Exception as e:
            # Fallback to simple mode
            print(f"LLM translation failed, falling back to simple: {e}")

    # Simple mode: Google Translate
    return _translate_simple(text, source_lang, target_lang)


def _translate_simple(text: str, source_lang: str, target_lang: str) -> TranslationResult:
    """Simple translation using Google Translate."""
    if not TRANSLATOR_AVAILABLE:
        raise RuntimeError("deep-translator is not installed. Run: pip install deep-translator")

    src = LANG_MAP.get(source_lang, source_lang)
    tgt = LANG_MAP.get(target_lang, target_lang)

    lines = text.strip().split("\n")
    translated_lines = []

    translator = GoogleTranslator(source=src, target=tgt)

    for line in lines:
        line = line.strip()
        if not line or line.startswith("["):
            translated_lines.append(line)
        else:
            translated = translator.translate(line)
            translated_lines.append(translated if translated else line)

    translated_text = "\n".join(translated_lines)

    return TranslationResult(
        original=text,
        translated=translated_text,
        source_lang=source_lang,
        target_lang=target_lang,
        mode="simple",
    )
