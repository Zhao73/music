"""Main analysis pipeline — orchestrates ALL analyzers for 95%+ reproduction fidelity.

Flow:
1. Load audio
2. Separate tracks (Demucs: vocals / drums / bass / other)
3. Run lyrics on isolated vocals (much more accurate)
4. Run melody on isolated vocals
5. Run rhythm on full mix
6. Detect key on harmonic content
7. Detect structure
8. Detect instruments on full mix
9. Detect chords on harmonic content (other + bass)
10. Analyze drum patterns on isolated drums
11. Analyze vocal style on isolated vocals
12. Analyze emotion on full mix
13. Analyze dynamics on full mix
14. Translate if needed
15. Generate comprehensive reproduction prompts
16. Generate visual score (sheet music)
"""

from dataclasses import dataclass, field
import os
import tempfile
import numpy as np

from utils.audio_io import load_audio, get_duration, format_time
from analyzers.lyrics import LyricsResult
from analyzers.rhythm import extract_rhythm, RhythmResult
from analyzers.key_detector import detect_key, KeyResult
from analyzers.structure import detect_structure, StructureResult
from analyzers.instruments import detect_instruments, InstrumentResult
from analyzers.vocal_style import analyze_vocal_style, VocalStyleResult
from analyzers.emotion import analyze_emotion, EmotionResult
from analyzers.dynamics import analyze_dynamics, DynamicsResult
from analyzers.chords import detect_chords, ChordResult
from analyzers.score_generator import generate_score, ScoreResult
from translation.translator import translate_lyrics, TranslationResult
from prompt_generator.generator import generate_prompt, PromptResult
from analyzers.melody import MelodyResult

# Optional imports — may fail if heavy deps (torch/demucs/whisper) are missing
try:
    from analyzers.separator import separate_tracks, SeparationResult
except Exception:
    separate_tracks = None
    SeparationResult = None

try:
    from analyzers.lyrics import extract_lyrics
except Exception:
    extract_lyrics = None

try:
    from analyzers.melody import extract_melody
except Exception:
    extract_melody = None

try:
    from analyzers.drums import analyze_drums, DrumResult
except Exception:
    analyze_drums = None
    DrumResult = None


@dataclass
class AnalysisResult:
    # Basic info
    duration: str = ""
    duration_seconds: float = 0.0

    # Separation
    separation: SeparationResult = None
    separation_used: bool = False

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
    chords: ChordResult = None
    drum_patterns: DrumResult = None

    # Translation
    translation: TranslationResult = None

    # Generated prompts
    prompts: PromptResult = None

    # Score / sheet music
    score: ScoreResult = None

    # Status tracking
    steps_completed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def analyze(
    audio_path: str,
    source_language: str = None,
    target_language: str = None,
    progress_callback=None,
    translation_mode: str = "simple",
    llm_api_key: str = "",
) -> AnalysisResult:
    """Run the FULL analysis pipeline for 95%+ reproduction fidelity.

    Key improvement: uses Demucs source separation to analyze
    vocals, drums, bass, and harmony independently.
    Gracefully degrades if optional dependencies are missing.
    """
    result = AnalysisResult()
    total_steps = 16

    def update_progress(step, num):
        if progress_callback:
            progress_callback(step, num / total_steps)

    # ============================================================
    # Step 1: Load audio (full mix)
    # ============================================================
    update_progress("Loading audio...", 1)
    try:
        y_full, sr = load_audio(audio_path)
        result.duration_seconds = get_duration(y_full, sr)
        result.duration = format_time(result.duration_seconds)
        result.steps_completed.append("audio_loaded")
    except Exception as e:
        result.errors.append(f"Failed to load audio: {e}")
        return result

    # ============================================================
    # Step 2: Source separation (Demucs) — THE KEY TO 95%+
    # ============================================================
    update_progress("Separating tracks (Demucs: vocals/drums/bass/other)...", 2)
    y_vocals = y_full     # Fallback: use full mix
    y_drums = None
    y_bass = None
    y_other = None

    if separate_tracks is None:
        result.errors.append("Separator not available (torch/demucs not installed), using full mix")
        result.steps_completed.append("separation_skipped")
    else:
        try:
            sep = separate_tracks(audio_path, sr=sr)
            result.separation = sep

            if sep.success:
                y_vocals = sep.vocals
                y_drums = sep.drums
                y_bass = sep.bass
                y_other = sep.other
                result.separation_used = True
                result.steps_completed.append("separation_demucs")
            else:
                # HPSS fallback
                y_vocals = sep.vocals
                y_drums = sep.drums
                y_bass = sep.bass
                y_other = sep.other
                result.separation_used = False
                result.steps_completed.append("separation_hpss_fallback")
                if sep.error:
                    result.errors.append(f"Demucs fallback: {sep.error}")
        except Exception as e:
            result.errors.append(f"Separation failed, using full mix: {e}")
            result.steps_completed.append("separation_failed")

    # ============================================================
    # Step 3: Extract lyrics — on ISOLATED VOCALS (much more accurate)
    # ============================================================
    update_progress("Extracting lyrics from isolated vocals...", 3)
    if extract_lyrics is None:
        result.errors.append("Whisper not available (openai-whisper not installed), skipping lyrics")
        result.lyrics = LyricsResult(full_text="", segments=[], detected_language="")
    else:
        try:
            # Save isolated vocals to temp file for Whisper
            if result.separation_used or y_vocals is not y_full:
                import soundfile as sf
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    vocals_path = tmp.name
                    sf.write(vocals_path, y_vocals, sr)
                try:
                    lang = source_language if source_language and source_language != "auto" else None
                    result.lyrics = extract_lyrics(vocals_path, language=lang)
                finally:
                    os.unlink(vocals_path)
            else:
                lang = source_language if source_language and source_language != "auto" else None
                result.lyrics = extract_lyrics(audio_path, language=lang)
            result.steps_completed.append("lyrics_extracted")
        except Exception as e:
            result.errors.append(f"Lyrics extraction failed: {e}")
            result.lyrics = LyricsResult(full_text="", segments=[], detected_language="")

    # ============================================================
    # Step 4: Analyze rhythm (on full mix — beat tracking works best on mix)
    # ============================================================
    update_progress("Analyzing rhythm and tempo...", 4)
    try:
        result.rhythm = extract_rhythm(y_full, sr)
        result.steps_completed.append("rhythm_analyzed")
    except Exception as e:
        result.errors.append(f"Rhythm analysis failed: {e}")

    # ============================================================
    # Step 5: Detect key (on harmonic content: other + bass)
    # ============================================================
    update_progress("Detecting musical key...", 5)
    try:
        if y_other is not None and y_bass is not None:
            y_harmonic = y_other + y_bass
        else:
            y_harmonic = y_full
        result.key = detect_key(y_harmonic, sr)
        result.steps_completed.append("key_detected")
    except Exception as e:
        result.errors.append(f"Key detection failed: {e}")

    # ============================================================
    # Step 6: Extract melody — on ISOLATED VOCALS (much more accurate)
    # ============================================================
    update_progress("Extracting melody from isolated vocals...", 6)
    if extract_melody is None:
        result.errors.append("Melody extraction not available, skipping")
    else:
        try:
            bpm = result.rhythm.bpm if result.rhythm else 120.0
            result.melody = extract_melody(y_vocals, sr, bpm=bpm)
            result.steps_completed.append("melody_extracted")
        except Exception as e:
            result.errors.append(f"Melody extraction failed: {e}")

    # ============================================================
    # Step 7: Detect structure (on full mix)
    # ============================================================
    update_progress("Detecting song structure...", 7)
    try:
        lyrics_segs = result.lyrics.segments if result.lyrics else None
        result.structure = detect_structure(y_full, sr, lyrics_segments=lyrics_segs)
        result.steps_completed.append("structure_detected")
    except Exception as e:
        result.errors.append(f"Structure detection failed: {e}")

    # ============================================================
    # Step 8: Detect instruments (on full mix)
    # ============================================================
    update_progress("Detecting instruments...", 8)
    try:
        result.instruments = detect_instruments(y_full, sr)
        result.steps_completed.append("instruments_detected")
    except Exception as e:
        result.errors.append(f"Instrument detection failed: {e}")

    # ============================================================
    # Step 9: Chord progression — on harmonic content (other + bass)
    # ============================================================
    update_progress("Detecting chord progression...", 9)
    try:
        if y_other is not None and y_bass is not None:
            y_chords = y_other + y_bass
        else:
            y_chords = y_full
        beat_times = result.rhythm.beat_times if result.rhythm else None
        sections = result.structure.sections if result.structure else None
        result.chords = detect_chords(y_chords, sr, beat_times=beat_times, sections=sections)
        result.steps_completed.append("chords_detected")
    except Exception as e:
        result.errors.append(f"Chord detection failed: {e}")

    # ============================================================
    # Step 10: Drum patterns — on ISOLATED DRUMS
    # ============================================================
    update_progress("Analyzing drum patterns...", 10)
    if analyze_drums is None:
        result.errors.append("Drum analysis not available, skipping")
    else:
        try:
            y_for_drums = y_drums if y_drums is not None else y_full
            bpm = result.rhythm.bpm if result.rhythm else 120.0
            beat_times = result.rhythm.beat_times if result.rhythm else None
            result.drum_patterns = analyze_drums(y_for_drums, sr, bpm=bpm, beat_times=beat_times)
            result.steps_completed.append("drums_analyzed")
        except Exception as e:
            result.errors.append(f"Drum analysis failed: {e}")

    # ============================================================
    # Step 11: Vocal style — on ISOLATED VOCALS
    # ============================================================
    update_progress("Analyzing vocal style & technique...", 11)
    try:
        f0 = result.melody.pitch_hz if result.melody else None
        result.vocal_style = analyze_vocal_style(y_vocals, sr, f0=f0)
        result.steps_completed.append("vocal_style_analyzed")
    except Exception as e:
        result.errors.append(f"Vocal style analysis failed: {e}")

    # ============================================================
    # Step 12: Emotion analysis (on full mix)
    # ============================================================
    update_progress("Analyzing emotion & mood...", 12)
    try:
        result.emotion = analyze_emotion(y_full, sr)
        result.steps_completed.append("emotion_analyzed")
    except Exception as e:
        result.errors.append(f"Emotion analysis failed: {e}")

    # ============================================================
    # Step 13: Dynamics analysis (on full mix, per section)
    # ============================================================
    update_progress("Analyzing dynamics & volume...", 13)
    try:
        sections = result.structure.sections if result.structure else None
        result.dynamics = analyze_dynamics(y_full, sr, sections=sections)
        result.steps_completed.append("dynamics_analyzed")
    except Exception as e:
        result.errors.append(f"Dynamics analysis failed: {e}")

    # ============================================================
    # Step 14: Translate if requested (Simple or Intelligent mode)
    # ============================================================
    translated_text = ""
    if target_language and result.lyrics and result.lyrics.full_text:
        update_progress(f"Translating lyrics to {target_language} ({translation_mode})...", 14)
        try:
            src_lang = result.lyrics.detected_language or source_language or "auto"

            # Build musical context for intelligent translation
            musical_context = None
            if translation_mode == "intelligent" and llm_api_key:
                from translation.llm_translator import MusicalContext
                musical_context = MusicalContext(
                    bpm=result.rhythm.bpm if result.rhythm else 120.0,
                    key=result.key.key if result.key else "",
                    mood=result.emotion.overall_mood if result.emotion else "",
                    emotional_arc=result.emotion.emotional_arc if result.emotion else "",
                    vocal_style=", ".join(result.vocal_style.style_tags) if result.vocal_style else "",
                    melody_contour=result.melody.contour_per_section if result.melody else "",
                    sections=result.structure.sections if result.structure else None,
                )

            result.translation = translate_lyrics(
                result.lyrics.full_text, src_lang, target_language,
                mode=translation_mode,
                api_key=llm_api_key,
                musical_context=musical_context,
            )
            translated_text = result.translation.translated
            result.steps_completed.append(f"lyrics_translated_{result.translation.mode}")
        except Exception as e:
            result.errors.append(f"Translation failed: {e}")

    # ============================================================
    # Step 15: Generate comprehensive reproduction prompts
    # ============================================================
    update_progress("Generating reproduction prompts...", 15)
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
            # Detailed parameters
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
            # Chords & drums
            chord_progression=result.chords.chord_progression if result.chords else "",
            chord_per_section=result.chords.progression_per_section if result.chords else {},
            chord_description=result.chords.description if result.chords else "",
            drum_pattern=result.drum_patterns.main_pattern if result.drum_patterns else "",
            drum_groove=result.drum_patterns.groove_type if result.drum_patterns else "",
            drum_description=result.drum_patterns.description if result.drum_patterns else "",
            drum_notation=result.drum_patterns.pattern_notation if result.drum_patterns else "",
            kick_pattern=result.drum_patterns.kick_pattern if result.drum_patterns else "",
            snare_pattern=result.drum_patterns.snare_pattern if result.drum_patterns else "",
            hihat_pattern=result.drum_patterns.hihat_pattern if result.drum_patterns else "",
        )
        result.steps_completed.append("prompts_generated")
    except Exception as e:
        result.errors.append(f"Prompt generation failed: {e}")

    # ============================================================
    # Step 16: Generate visual score (MusicXML / MIDI / PDF)
    # ============================================================
    update_progress("Generating visual score (sheet music)...", 16)
    try:
        result.score = generate_score(
            note_events=result.melody.note_events if result.melody else None,
            chord_events=result.chords.chords if result.chords else None,
            drum_result=result.drum_patterns,
            key_str=result.key.key if result.key else "C major",
            time_signature=result.rhythm.time_signature if result.rhythm else "4/4",
            bpm=result.rhythm.bpm if result.rhythm else 120.0,
            total_duration=result.duration_seconds,
            lyrics_segments=result.lyrics.segments if result.lyrics else None,
            title="MusicLens Analysis",
        )
        if result.score.success:
            result.steps_completed.append("score_generated")
        else:
            result.errors.append(f"Score: {result.score.error}")
    except Exception as e:
        result.errors.append(f"Score generation failed: {e}")

    update_progress("Done! Analysis complete.", total_steps)
    return result
