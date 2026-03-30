"""Main analysis pipeline - orchestrates all analyzers."""

from dataclasses import dataclass, field

from utils.audio_io import load_audio, get_duration, format_time
from analyzers.lyrics import extract_lyrics, LyricsResult
from analyzers.melody import extract_melody, MelodyResult
from analyzers.rhythm import extract_rhythm, RhythmResult
from analyzers.key_detector import detect_key, KeyResult
from analyzers.structure import detect_structure, StructureResult
from analyzers.instruments import detect_instruments, InstrumentResult
from translation.translator import translate_lyrics, TranslationResult
from prompt_generator.generator import generate_prompt, PromptResult


@dataclass
class AnalysisResult:
    # Basic info
    duration: str = ""
    duration_seconds: float = 0.0

    # Analysis results
    lyrics: LyricsResult = None
    melody: MelodyResult = None
    rhythm: RhythmResult = None
    key: KeyResult = None
    structure: StructureResult = None
    instruments: InstrumentResult = None

    # Translation
    translation: TranslationResult = None

    # Generated prompts
    prompts: PromptResult = None

    # Status tracking
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def analyze(
    audio_path: str,
    source_language: str = None,
    target_language: str = None,
    progress_callback=None,
) -> AnalysisResult:
    """Run the full analysis pipeline on an audio file.

    Args:
        audio_path: Path to the audio file.
        source_language: Source language code (None for auto-detect).
        target_language: Target language for translation (None to skip).
        progress_callback: Optional callback(step_name, progress_fraction).

    Returns:
        AnalysisResult with all analysis data and generated prompts.
    """
    result = AnalysisResult()

    def update_progress(step, fraction):
        if progress_callback:
            progress_callback(step, fraction)

    # Step 1: Load audio
    update_progress("Loading audio...", 0.05)
    try:
        y, sr = load_audio(audio_path)
        result.duration_seconds = get_duration(y, sr)
        result.duration = format_time(result.duration_seconds)
        result.steps_completed.append("audio_loaded")
    except Exception as e:
        result.errors.append(f"Failed to load audio: {e}")
        return result

    # Step 2: Extract lyrics
    update_progress("Extracting lyrics (Whisper)...", 0.15)
    try:
        lang = source_language if source_language and source_language != "auto" else None
        result.lyrics = extract_lyrics(audio_path, language=lang)
        result.steps_completed.append("lyrics_extracted")
    except Exception as e:
        result.errors.append(f"Lyrics extraction failed: {e}")
        result.lyrics = LyricsResult(full_text="", segments=[], detected_language="")

    # Step 3: Analyze rhythm
    update_progress("Analyzing rhythm and tempo...", 0.35)
    try:
        result.rhythm = extract_rhythm(y, sr)
        result.steps_completed.append("rhythm_analyzed")
    except Exception as e:
        result.errors.append(f"Rhythm analysis failed: {e}")

    # Step 4: Detect key
    update_progress("Detecting musical key...", 0.45)
    try:
        result.key = detect_key(y, sr)
        result.steps_completed.append("key_detected")
    except Exception as e:
        result.errors.append(f"Key detection failed: {e}")

    # Step 5: Extract melody
    update_progress("Extracting melody...", 0.55)
    try:
        result.melody = extract_melody(y, sr)
        result.steps_completed.append("melody_extracted")
    except Exception as e:
        result.errors.append(f"Melody extraction failed: {e}")

    # Step 6: Detect structure
    update_progress("Detecting song structure...", 0.65)
    try:
        lyrics_segs = result.lyrics.segments if result.lyrics else None
        result.structure = detect_structure(y, sr, lyrics_segments=lyrics_segs)
        result.steps_completed.append("structure_detected")
    except Exception as e:
        result.errors.append(f"Structure detection failed: {e}")

    # Step 7: Detect instruments
    update_progress("Detecting instruments...", 0.75)
    try:
        result.instruments = detect_instruments(y, sr)
        result.steps_completed.append("instruments_detected")
    except Exception as e:
        result.errors.append(f"Instrument detection failed: {e}")

    # Step 8: Translate if requested
    translated_text = ""
    if target_language and result.lyrics and result.lyrics.full_text:
        update_progress(f"Translating lyrics to {target_language}...", 0.85)
        try:
            src_lang = result.lyrics.detected_language or source_language or "auto"
            result.translation = translate_lyrics(
                result.lyrics.full_text, src_lang, target_language
            )
            translated_text = result.translation.translated
            result.steps_completed.append("lyrics_translated")
        except Exception as e:
            result.errors.append(f"Translation failed: {e}")

    # Step 9: Generate prompts
    update_progress("Generating AI prompts...", 0.95)
    try:
        vocal_range = "N/A"
        if result.melody:
            vocal_range = f"{result.melody.vocal_range_low} - {result.melody.vocal_range_high}"

        result.prompts = generate_prompt(
            lyrics_text=result.lyrics.full_text if result.lyrics else "",
            translated_text=translated_text,
            bpm=result.rhythm.bpm if result.rhythm else 120.0,
            key=result.key.key if result.key else "Unknown",
            time_signature=result.rhythm.time_signature if result.rhythm else "4/4",
            feel=result.rhythm.feel if result.rhythm else "moderate",
            energy=result.rhythm.energy_level if result.rhythm else "medium",
            instruments=result.instruments.detected if result.instruments else ["Unknown"],
            vocal_range=vocal_range,
            melody_description=result.melody.description if result.melody else "",
            sections=result.structure.sections if result.structure else [],
            source_lang=result.lyrics.detected_language if result.lyrics else "unknown",
            target_lang=target_language,
        )
        result.steps_completed.append("prompts_generated")
    except Exception as e:
        result.errors.append(f"Prompt generation failed: {e}")

    update_progress("Done!", 1.0)
    return result
