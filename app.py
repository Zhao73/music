"""MusicLens — Gradio Web UI matched to actual Suno/Udio interface."""

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
        return (empty,) + ("",) * 15

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
    info += f"Separation: {'Demucs (high quality)' if result.separation_used else 'HPSS fallback'}\n"
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
    if result.instruments:
        info += f"Instruments: {', '.join(result.instruments.detected)}\n"
    if result.chords and result.chords.key_chords:
        info += f"Main Chords: {result.chords.key_chords}\n"
    if result.drum_patterns and result.drum_patterns.groove_type:
        info += f"Drum Groove: {result.drum_patterns.groove_type}\n"
    if result.errors:
        info += f"\nWarnings: {'; '.join(result.errors)}\n"

    # --- 2. Lyrics ---
    lyrics = ""
    if result.lyrics:
        lyrics = result.lyrics.full_text
        if result.lyrics.segments:
            lyrics += "\n\n--- Timed ---\n"
            for seg in result.lyrics.segments:
                lyrics += f"[{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['text']}\n"

    # --- 3. Melody ---
    melody = ""
    if result.melody:
        melody = result.melody.description + "\n\n"
        melody += "--- Contour ---\n" + result.melody.contour_per_section + "\n\n"
        melody += "--- Notation ---\n" + result.melody.melody_notation + "\n\n"
        if result.melody.note_events:
            melody += f"--- Notes (first 30/{len(result.melody.note_events)}) ---\n"
            for n in result.melody.note_events[:30]:
                bar = "#" * max(1, int(n.velocity_est * 10))
                melody += f"  {n.start_time:6.2f}s {n.note_name:<5} dur={n.duration:.3f}s ({n.duration_type:<20}) |{bar}|\n"

    # --- 4. Chords ---
    chords = result.chords.description if result.chords else ""

    # --- 5. Drums ---
    drums = result.drum_patterns.description if result.drum_patterns else ""

    # --- 6. Structure ---
    structure = ""
    if result.structure:
        structure = result.structure.summary + "\n\n"
        for s in result.structure.sections:
            dur = s.end_time - s.start_time
            structure += f"  {s.label:<15} {format_time(s.start_time)}-{format_time(s.end_time)} ({dur:.1f}s)\n"

    # --- 7. Vocal ---
    vocal = result.vocal_style.full_description if result.vocal_style else ""

    # --- 8. Emotion ---
    emotion = result.emotion.full_description if result.emotion else ""

    # --- 9. Dynamics ---
    dynamics = result.dynamics.description if result.dynamics else ""

    # --- 10. Instruments ---
    instruments = result.instruments.description if result.instruments else ""

    # --- 11-12. SUNO (split: Style + Lyrics) ---
    suno_style = result.prompts.suno_style if result.prompts else ""
    suno_lyrics = result.prompts.suno_lyrics if result.prompts else ""

    # --- 13. Full prompt ---
    generic = result.prompts.generic_prompt if result.prompts else ""

    # --- 14. Translated Suno lyrics ---
    suno_translated = result.prompts.suno_lyrics_translated if result.prompts else "No translation."

    # --- 15. Translation ---
    translation = result.translation.translated if result.translation else "No translation."

    # --- 16. Log ---
    log = f"Steps: {', '.join(result.steps_completed)}\n"
    if result.errors:
        log += "\n".join(f"  - {e}" for e in result.errors)

    return (
        info, lyrics, melody, chords, drums, structure,
        vocal, emotion, dynamics, instruments,
        suno_style, suno_lyrics,
        generic, suno_translated, translation, log,
    )


lang_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items()]
target_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items() if k != "auto"]

with gr.Blocks(
    title="MusicLens",
    theme=gr.themes.Soft(),
    css=".mono textarea { font-family: monospace !important; font-size: 12px !important; }"
) as demo:
    gr.HTML("""
    <div style="text-align:center; margin-bottom:1em;">
        <h1>MusicLens — 音乐完整复刻分析</h1>
        <p style="color:#666;">
            Upload → Demucs Separation → 12 Analyzers → Copy Style + Lyrics to Suno<br>
            上传音乐 → 人声分离 → 12项分析 → 复制 Style 和 Lyrics 分别粘贴到 Suno 的两个框
        </p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(type="filepath", label="Upload Music / 上传音乐")
        with gr.Column(scale=1):
            source_lang = gr.Dropdown(choices=lang_choices, value="auto", label="Song Language / 歌曲语言")
            target_lang = gr.Dropdown(choices=target_choices, value="en", label="Target Language / 目标语言")
            btn = gr.Button("Analyze / 开始分析", variant="primary", size="lg")

    with gr.Tabs():
        # ===== SUNO TAB (MOST IMPORTANT) =====
        with gr.TabItem("Suno — Copy These / Suno用"):
            gr.HTML("""
            <div style="background:#fff3cd; padding:12px; border-radius:8px; margin-bottom:12px;">
                <b>Suno 使用方法（3步）:</b><br>
                1. 打开 Suno → 选择 <b>カスタム / Custom</b> 模式<br>
                2. 复制下面的 <b>"Style"</b> → 粘贴到 Suno 的 <b>"スタイル"</b> 框<br>
                3. 复制下面的 <b>"Lyrics"</b> → 粘贴到 Suno 的 <b>"歌詞"</b> 框<br>
                4. 点击 <b>"作成する / Create"</b> 生成！
            </div>
            """)
            with gr.Row():
                with gr.Column():
                    gr.HTML("<h3>Step 1: Style → 粘贴到 Suno「スタイル」框</h3>")
                    out_suno_style = gr.Textbox(
                        label="Suno Style (copy this → paste into Suno Style box)",
                        lines=5, interactive=False, show_copy_button=True,
                        elem_classes=["mono"],
                    )
                with gr.Column():
                    gr.HTML("<h3>Step 2: Lyrics → 粘贴到 Suno「歌詞」框</h3>")
                    out_suno_lyrics = gr.Textbox(
                        label="Suno Lyrics (copy this → paste into Suno Lyrics box)",
                        lines=20, interactive=False, show_copy_button=True,
                    )

        with gr.TabItem("Suno Translated / Suno外语版"):
            gr.HTML("""
            <div style="background:#d4edda; padding:12px; border-radius:8px; margin-bottom:12px;">
                <b>外语翻唱:</b> Style 不变，只替换 Lyrics 为下面的翻译版歌词
            </div>
            """)
            gr.HTML("<p><b>Style: 同上（复制 Suno 标签页的 Style）</b></p>")
            out_suno_translated = gr.Textbox(
                label="Translated Lyrics for Suno / 翻译歌词（粘贴到 Suno 歌詞框）",
                lines=20, interactive=False, show_copy_button=True,
            )

        # ===== ANALYSIS TABS =====
        with gr.TabItem("Overview / 总览"):
            out_info = gr.Textbox(label="Summary", lines=15, interactive=False)

        with gr.TabItem("Lyrics / 歌词"):
            out_lyrics = gr.Textbox(label="Lyrics", lines=25, interactive=False, show_copy_button=True)

        with gr.TabItem("Melody / 旋律"):
            out_melody = gr.Textbox(label="Melody", lines=30, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Chords / 和弦"):
            out_chords = gr.Textbox(label="Chords", lines=25, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Drums / 鼓点"):
            out_drums = gr.Textbox(label="Drums", lines=25, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Structure / 结构"):
            out_structure = gr.Textbox(label="Structure", lines=15, interactive=False)

        with gr.TabItem("Vocal / 演唱"):
            out_vocal = gr.Textbox(label="Vocal Style", lines=20, interactive=False, show_copy_button=True)

        with gr.TabItem("Emotion / 情感"):
            out_emotion = gr.Textbox(label="Emotion", lines=25, interactive=False, show_copy_button=True)

        with gr.TabItem("Dynamics / 力度"):
            out_dynamics = gr.Textbox(label="Dynamics", lines=20, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Instruments / 乐器"):
            out_instruments = gr.Textbox(label="Instruments", lines=8, interactive=False)

        with gr.TabItem("Full Prompt / 完整提示词"):
            out_generic = gr.Textbox(label="Complete Prompt", lines=50, interactive=False, show_copy_button=True, elem_classes=["mono"])

        with gr.TabItem("Translation / 翻译"):
            out_translation = gr.Textbox(label="Translated Lyrics", lines=20, interactive=False, show_copy_button=True)

        with gr.TabItem("Log"):
            out_log = gr.Textbox(label="Log", lines=10, interactive=False)

    btn.click(
        fn=run_analysis,
        inputs=[audio_input, source_lang, target_lang],
        outputs=[
            out_info, out_lyrics, out_melody, out_chords, out_drums, out_structure,
            out_vocal, out_emotion, out_dynamics, out_instruments,
            out_suno_style, out_suno_lyrics,
            out_generic, out_suno_translated, out_translation, out_log,
        ],
    )

    gr.Markdown("""
    ---
    **How to use with Suno**: Open Suno → Custom mode → Copy **Style** to Style box → Copy **Lyrics** to Lyrics box → Create
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
