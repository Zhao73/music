"""Main analysis pipeline - orchestrates ALL analyzers for maximum reproduction fidelity."""

from dataclasses import dataclass, field

from utils.audio_io import load_audio, get_duration, format_time
from analyzers.lyrics import extract_lyrics, LyricsResult
from analyzers.melody import extract_melody, MelodyResult
from analyzers.rhythm import extract_rhythm, RhythmResult
from analyzers.key_detector import detect_key, KeyResult
from analyzers.structure import detect_structure, StructureResult
from analyzers.instruments import detect_instruments, InstrumentResult
from analyzers.vocal_style import analyze_vocal_style, VocalStyleResult
from analyzers.emotion import analyze_emotion, EmotionResult
from analyzers.dynamics import analyze_dynamics, DynamicsResult
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
    vocal_style: VocalStyleResult = None
    emotion: EmotionResult = None
    dynamics: DynamicsResult = None

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
    """Run the FULL analysis pipeline for maximum reproduction fidelity.

    Analyzes: lyrics, melody (with note timing), rhythm, key, structure,
    instruments, vocal style/technique, emotion/mood, dynamics/volume.
    """
    result = AnalysisResult()
    total_steps = 12

    def update_progress(step, num):
        if progress_callback:
            progress_callback(step, num / total_steps)

    # Step 1: Load audio
    update_progress("Loading audio...", 1)
    try:
        y, sr = load_audio(audio_path)
        result.duration_seconds = get_duration(y, sr)
        result.duration = format_time(result.duration_seconds)
        result.steps_completed.append("audio_loaded")
    except Exception as e:
        result.errors.append(f"Failed to load audio: {e}")
        return result

    # Step 2: Extract lyrics
    update_progress("Extracting lyrics (Whisper)...", 2)
    try:
        lang = source_language if source_language and source_language != "auto" else None
        result.lyrics = extract_lyrics(audio_path, language=lang)
        result.steps_completed.append("lyrics_extracted")
    except Exception as e:
        result.errors.append(f"Lyrics extraction failed: {e}")
        result.lyrics = LyricsResult(full_text="", segments=[], detected_language="")

    # Step 3: Analyze rhythm (needed by melody for duration classification)
    update_progress("Analyzing rhythm and tempo...", 3)
    try:
        result.rhythm = extract_rhythm(y, sr)
        result.steps_completed.append("rhythm_analyzed")
    except Exception as e:
        result.errors.append(f"Rhythm analysis failed: {e}")

    # Step 4: Detect key
    update_progress("Detecting musical key...", 4)
    try:
        result.key = detect_key(y, sr)
        result.steps_completed.append("key_detected")
    except Exception as e:
        result.errors.append(f"Key detection failed: {e}")

    # Step 5: Extract melody (enhanced with note timing)
    update_progress("Extracting melody (note-by-note)...", 5)
    try:
        bpm = result.rhythm.bpm if result.rhythm else 120.0
        result.melody = extract_melody(y, sr, bpm=bpm)
        result.steps_completed.append("melody_extracted")
    except Exception as e:
        result.errors.append(f"Melody extraction failed: {e}")

    # Step 6: Detect structure
    update_progress("Detecting song structure...", 6)
    try:
        lyrics_segs = result.lyrics.segments if result.lyrics else None
        result.structure = detect_structure(y, sr, lyrics_segments=lyrics_segs)
        result.steps_completed.append("structure_detected")
    except Exception as e:
        result.errors.append(f"Structure detection failed: {e}")

    # Step 7: Detect instruments
    update_progress("Detecting instruments...", 7)
    try:
        result.instruments = detect_instruments(y, sr)
        result.steps_completed.append("instruments_detected")
    except Exception as e:
        result.errors.append(f"Instrument detection failed: {e}")

    # Step 8: Vocal style analysis
    update_progress("Analyzing vocal style & technique...", 8)
    try:
        f0 = result.melody.pitch_hz if result.melody else None
        result.vocal_style = analyze_vocal_style(y, sr, f0=f0)
        result.steps_completed.append("vocal_style_analyzed")
    except Exception as e:
        result.errors.append(f"Vocal style analysis failed: {e}")

    # Step 9: Emotion analysis
    update_progress("Analyzing emotion & mood...", 9)
    try:
        result.emotion = analyze_emotion(y, sr)
        result.steps_completed.append("emotion_analyzed")
    except Exception as e:
        result.errors.append(f"Emotion analysis failed: {e}")

    # Step 10: Dynamics analysis
    update_progress("Analyzing dynamics & volume...", 10)
    try:
        sections = result.structure.sections if result.structure else None
        result.dynamics = analyze_dynamics(y, sr, sections=sections)
        result.steps_completed.append("dynamics_analyzed")
    except Exception as e:
        result.errors.append(f"Dynamics analysis failed: {e}")

    # Step 11: Translate if requested
    translated_text = ""
    if target_language and result.lyrics and result.lyrics.full_text:
        update_progress(f"Translating lyrics to {target_language}...", 11)
        try:
            src_lang = result.lyrics.detected_language or source_language or "auto"
            result.translation = translate_lyrics(
                result.lyrics.full_text, src_lang, target_language
            )
            translated_text = result.translation.translated
            result.steps_completed.append("lyrics_translated")
        except Exception as e:
            result.errors.append(f"Translation failed: {e}")

    # Step 12: Generate comprehensive prompts
    update_progress("Generating reproduction prompts...", 12)
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
            melody_contour=result.melody.contour_per_section if result.melody else "",
            melody_notation=result.melody.melody_notation if result.melody else "",
            sections=result.structure.sections if result.structure else [],
            source_lang=result.lyrics.detected_language if result.lyrics else "unknown",
            target_lang=target_language,
            # New detailed parameters
            mood=result.emotion.overall_mood if result.emotion else "",
            mood_tags=result.emotion.mood_tags if result.emotion else [],
            emotional_arc=result.emotion.emotional_arc if result.emotion else "",
            energy_curve=result.emotion.energy_curve_description if result.emotion else "",
            vocal_style_tags=result.vocal_style.style_tags if result.vocal_style else [],
            vibrato_desc=result.vocal_style.vibrato_description if result.vocal_style else "",
            register_desc=result.vocal_style.register_description if result.vocal_style else "",
            tone_desc=result.vocal_style.tone_description if result.vocal_style else "",
            articulation_desc=result.vocal_style.articulation_description if result.vocal_style else "",
            dynamics_marking=result.dynamics.loudness_units if result.dynamics else "",
            dynamic_range=f"{result.dynamics.dynamic_range_db:.1f} dB" if result.dynamics else "",
            volume_map=result.dynamics.volume_map_text if result.dynamics else "",
            dynamic_events=result.dynamics.markings if result.dynamics else [],
            rhythm_description=result.rhythm.description if result.rhythm else "",
            lyrics_segments=result.lyrics.segments if result.lyrics else [],
        )
        result.steps_completed.append("prompts_generated")
    except Exception as e:
        result.errors.append(f"Prompt generation failed: {e}")

    update_progress("Done!", total_steps)
    return result
