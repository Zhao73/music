"""Lyrics translation using deep-translator (Google Translate, free)."""

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
) -> TranslationResult:
    """Translate lyrics while preserving line structure."""
    if not TRANSLATOR_AVAILABLE:
        raise RuntimeError("deep-translator is not installed. Run: pip install deep-translator")

    src = LANG_MAP.get(source_lang, source_lang)
    tgt = LANG_MAP.get(target_lang, target_lang)

    # Split by lines to preserve structure
    lines = text.strip().split("\n")
    translated_lines = []

    translator = GoogleTranslator(source=src, target=tgt)

    for line in lines:
        line = line.strip()
        if not line or line.startswith("["):
            # Preserve empty lines and section markers
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
    )
