"""MusicLens — Gradio Web UI for 95%+ music reproduction analysis."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from pipeline import analyze
from config import LANGUAGE_OPTIONS
from utils.audio_io import format_time


def run_analysis(audio_file, source_lang, target_lang, progress=gr.Progress()):
    if audio_file is None:
        empty = "Please upload an audio file. / 请上传音乐文件。"
        return (empty,) + ("",) * 14

    def progress_callback(step, fraction):
        progress(fraction, desc=step)

    result = analyze(
        audio_path=audio_file,
        source_language=source_lang if source_lang != "auto" else None,
        target_language=target_lang if target_lang else None,
        progress_callback=progress_callback,
    )

    # --- 1. Overview ---
    info = f"Duration: {result.duration}\n"
    info += f"Source Separation: {'Demucs (high quality)' if result.separation_used else 'HPSS fallback'}\n"
    if result.lyrics:
        info += f"Language: {result.lyrics.detected_language}\n"
    if result.rhythm:
        info += f"BPM: {result.rhythm.bpm:.1f}\n"
        info += f"Time Signature: {result.rhythm.time_signature}\n"
        info += f"Feel: {result.rhythm.feel}\n"
        info += f"Energy: {result.rhythm.energy_level}\n"
    if result.key:
        info += f"Key: {result.key.key} (confidence: {result.key.confidence:.2f})\n"
    if result.emotion:
        info += f"Mood: {result.emotion.overall_mood}\n"
        info += f"Mood Tags: {', '.join(result.emotion.mood_tags)}\n"
    if result.instruments:
        info += f"Instruments: {', '.join(result.instruments.detected)}\n"
    if result.chords and result.chords.key_chords:
        info += f"Main Chords: {result.chords.key_chords}\n"
    if result.drum_patterns and result.drum_patterns.groove_type:
        info += f"Drum Groove: {result.drum_patterns.groove_type}\n"
    if result.errors:
        info += f"\nWarnings: {'; '.join(result.errors)}\n"
    info += f"\nSteps completed: {len(result.steps_completed)}/15"

    # --- 2. Lyrics ---
    lyrics = ""
    if result.lyrics:
        lyrics = result.lyrics.full_text
        if result.lyrics.segments:
            lyrics += "\n\n--- Timed Lyrics ---\n"
            for seg in result.lyrics.segments:
                lyrics += f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}\n"

    # --- 3. Melody ---
    melody = ""
    if result.melody:
        melody = result.melody.description + "\n\n"
        melody += "--- Melodic Contour ---\n" + result.melody.contour_per_section + "\n\n"
        melody += "--- Notation ---\n" + result.melody.melody_notation + "\n\n"
        if result.melody.note_events:
            melody += f"--- Note Events (first 30 of {len(result.melody.note_events)}) ---\n"
            for n in result.melody.note_events[:30]:
                bar = "#" * max(1, int(n.velocity_est * 10))
                melody += f"  {n.start_time:6.2f}s {n.note_name:<5} dur={n.duration:.3f}s ({n.duration_type:<20}) |{bar}|\n"
            if len(result.melody.note_events) > 30:
                melody += f"  ... +{len(result.melody.note_events) - 30} more\n"
        if result.melody.intervals:
            melody += f"\n--- Intervals (first 30) ---\n"
            melody += " → ".join(result.melody.intervals[:30])

    # --- 4. Chords ---
    chords = result.chords.description if result.chords else "Not available"

    # --- 5. Drum patterns ---
    drums = result.drum_patterns.description if result.drum_patterns else "Not available"

    # --- 6. Structure ---
    structure = ""
    if result.structure:
        structure = "Structure: " + result.structure.summary + "\n\n"
        for s in result.structure.sections:
            dur = s.end_time - s.start_time
            structure += f"  {s.label:<15} {format_time(s.start_time)} - {format_time(s.end_time)} ({dur:.1f}s)\n"

    # --- 7. Vocal Style ---
    vocal = result.vocal_style.full_description if result.vocal_style else ""

    # --- 8. Emotion ---
    emotion = result.emotion.full_description if result.emotion else ""

    # --- 9. Dynamics ---
    dynamics = result.dynamics.description if result.dynamics else ""

    # --- 10. Instruments ---
    instruments = result.instruments.description if result.instruments else ""

    # --- 11-13. Prompts ---
    suno = result.prompts.suno_prompt if result.prompts else ""
    generic = result.prompts.generic_prompt if result.prompts else ""
    translated = result.prompts.translated_prompt if result.prompts else "No translation requested."

    # --- 14. Translation ---
    translation = result.translation.translated if result.translation else "No translation requested."

    # --- 15. Log ---
    log = f"Steps completed: {', '.join(result.steps_completed)}\n"
    if result.errors:
        log += f"\nErrors/Warnings:\n" + "\n".join(f"  - {e}" for e in result.errors)
    else:
        log += "No errors."

    return (
        info, lyrics, melody, chords, drums, structure,
        vocal, emotion, dynamics, instruments,
        suno, generic, translated, translation, log,
    )


# Build UI
lang_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items()]
target_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items() if k != "auto"]

with gr.Blocks(
    title="MusicLens - 95%+ Music Reproduction",
    theme=gr.themes.Soft(),
    css=".mono textarea { font-family: monospace !important; font-size: 12px !important; }"
) as demo:
    gr.HTML("""
    <div style="text-align:center; margin-bottom:1em;">
        <h1>MusicLens — 95%+ 音乐完整复刻分析</h1>
        <p style="color:#666;">
            Upload → Demucs Separation → 12 Analyzers → Complete Reproduction Prompt → Copy to Suno/Udio<br>
            上传音乐 → Demucs人声分离 → 12项深度分析 → 完整复刻提示词 → 复制到Suno/Udio生成
        </p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(type="filepath", label="Upload Music / 上传音乐")
        with gr.Column(scale=1):
            source_lang = gr.Dropdown(choices=lang_choices, value="auto", label="Song Language / 歌曲语言")
            target_lang = gr.Dropdown(choices=target_choices, value="en", label="Target Language / 目标语言")
            btn = gr.Button("Analyze for Reproduction / 开始完整分析", variant="primary", size="lg")

    with gr.Tabs():
        with gr.TabItem("Overview / 总览"):
            out_info = gr.Textbox(label="Analysis Summary", lines=15, interactive=False)

        with gr.TabItem("Lyrics / 歌词"):
            out_lyrics = gr.Textbox(label="Lyrics + Timestamps", lines=25, interactive=False, show_copy_button=True)

        with gr.TabItem("Melody / 旋律"):
            out_melody = gr.Textbox(label="Melody: Notes, Duration, Intervals", lines=30, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Chords / 和弦"):
            out_chords = gr.Textbox(label="Chord Progression", lines=25, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Drums / 鼓点"):
            out_drums = gr.Textbox(label="Drum Pattern Analysis", lines=25, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Structure / 结构"):
            out_structure = gr.Textbox(label="Song Structure", lines=15, interactive=False)

        with gr.TabItem("Vocal / 演唱"):
            out_vocal = gr.Textbox(label="Vocal Style Analysis", lines=20, interactive=False, show_copy_button=True)

        with gr.TabItem("Emotion / 情感"):
            out_emotion = gr.Textbox(label="Emotion & Mood", lines=25, interactive=False, show_copy_button=True)

        with gr.TabItem("Dynamics / 力度"):
            out_dynamics = gr.Textbox(label="Dynamics & Volume", lines=20, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Instruments / 乐器"):
            out_instruments = gr.Textbox(label="Instruments", lines=8, interactive=False)

        with gr.TabItem("Suno Prompt"):
            out_suno = gr.Textbox(label="Suno Prompt (copy to Suno)", lines=30, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Full Prompt / 完整提示词"):
            out_generic = gr.Textbox(label="Complete Reproduction Prompt", lines=50, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Translated / 外语版"):
            out_translated = gr.Textbox(label="Translated Reproduction Prompt", lines=50, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Translation / 翻译"):
            out_translation = gr.Textbox(label="Translated Lyrics", lines=20, interactive=False, show_copy_button=True)

        with gr.TabItem("Log / 日志"):
            out_log = gr.Textbox(label="Analysis Log", lines=10, interactive=False)

    btn.click(
        fn=run_analysis,
        inputs=[audio_input, source_lang, target_lang],
        outputs=[
            out_info, out_lyrics, out_melody, out_chords, out_drums, out_structure,
            out_vocal, out_emotion, out_dynamics, out_instruments,
            out_suno, out_generic, out_translated, out_translation, out_log,
        ],
    )

    gr.Markdown("""
    ---
    **12 Analysis Modules**: Demucs Separation → Whisper (lyrics) → PYIN (melody+notes) → Beat Tracking (rhythm) →
    Krumhansl-Kessler (key) → Chroma Templates (chords) → Drum Grid (patterns) → Self-Similarity (structure) →
    Spectral (instruments) → Vibrato/Register/Tone (vocal) → Valence-Arousal (emotion) → RMS (dynamics)
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
