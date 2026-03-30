"""MusicLens - Gradio Web UI for complete music analysis and cross-language recreation."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from pipeline import analyze
from config import LANGUAGE_OPTIONS
from utils.audio_io import format_time


def run_analysis(audio_file, source_lang, target_lang, progress=gr.Progress()):
    """Main analysis function called by the Gradio UI."""
    if audio_file is None:
        empty = "Please upload an audio file."
        return (empty,) + ("",) * 12

    def progress_callback(step, fraction):
        progress(fraction, desc=step)

    result = analyze(
        audio_path=audio_file,
        source_language=source_lang if source_lang != "auto" else None,
        target_language=target_lang if target_lang else None,
        progress_callback=progress_callback,
    )

    # --- 1. Basic Info ---
    basic_info = f"Duration: {result.duration}\n"
    if result.lyrics:
        basic_info += f"Detected Language: {result.lyrics.detected_language}\n"
    if result.rhythm:
        basic_info += f"BPM: {result.rhythm.bpm:.1f}\n"
        basic_info += f"Time Signature: {result.rhythm.time_signature}\n"
        basic_info += f"Feel: {result.rhythm.feel}\n"
        basic_info += f"Energy: {result.rhythm.energy_level}\n"
    if result.key:
        basic_info += f"Key: {result.key.key} (confidence: {result.key.confidence:.2f})\n"
    if result.emotion:
        basic_info += f"Overall Mood: {result.emotion.overall_mood}\n"
        basic_info += f"Mood Tags: {', '.join(result.emotion.mood_tags)}\n"
    if result.instruments:
        basic_info += f"Instruments: {', '.join(result.instruments.detected)}\n"
    if result.errors:
        basic_info += f"\nWarnings: {'; '.join(result.errors)}"

    # --- 2. Lyrics ---
    lyrics_text = ""
    if result.lyrics:
        lyrics_text = result.lyrics.full_text
        if result.lyrics.segments:
            lyrics_text += "\n\n--- Timed Lyrics (per segment) ---\n"
            for seg in result.lyrics.segments:
                lyrics_text += f"[{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}\n"

    # --- 3. Melody (enhanced) ---
    melody_text = ""
    if result.melody:
        melody_text = result.melody.description + "\n\n"
        melody_text += "--- Melodic Contour per Section ---\n"
        melody_text += result.melody.contour_per_section + "\n\n"
        melody_text += "--- Note Sequence (simplified notation) ---\n"
        melody_text += result.melody.melody_notation + "\n\n"
        if result.melody.note_events:
            melody_text += f"--- Detailed Note Events (first 30 of {len(result.melody.note_events)}) ---\n"
            for n in result.melody.note_events[:30]:
                vel_bar = "#" * max(1, int(n.velocity_est * 10))
                melody_text += (
                    f"  {n.start_time:6.2f}s  {n.note_name:<5} "
                    f"dur={n.duration:.3f}s ({n.duration_type:<20}) "
                    f"vel={n.velocity_est:.2f} |{vel_bar}|\n"
                )
            if len(result.melody.note_events) > 30:
                melody_text += f"  ... and {len(result.melody.note_events) - 30} more notes\n"
        if result.melody.intervals:
            melody_text += f"\n--- Interval Sequence (first 30) ---\n"
            melody_text += " → ".join(result.melody.intervals[:30])
            if len(result.melody.intervals) > 30:
                melody_text += f" ... ({len(result.melody.intervals)} total)"

    # --- 4. Structure ---
    structure_text = ""
    if result.structure:
        structure_text = "Song Structure: " + result.structure.summary + "\n\n"
        for section in result.structure.sections:
            dur = section.end_time - section.start_time
            structure_text += (
                f"  {section.label:<15} "
                f"{format_time(section.start_time)} - {format_time(section.end_time)} "
                f"({dur:.1f}s)\n"
            )

    # --- 5. Vocal Style ---
    vocal_text = ""
    if result.vocal_style:
        vocal_text = result.vocal_style.full_description

    # --- 6. Emotion ---
    emotion_text = ""
    if result.emotion:
        emotion_text = result.emotion.full_description

    # --- 7. Dynamics ---
    dynamics_text = ""
    if result.dynamics:
        dynamics_text = result.dynamics.description

    # --- 8. Instruments ---
    instruments_text = ""
    if result.instruments:
        instruments_text = result.instruments.description

    # --- 9-11. Prompts ---
    suno_prompt = result.prompts.suno_prompt if result.prompts else ""
    generic_prompt = result.prompts.generic_prompt if result.prompts else ""
    translated_prompt = result.prompts.translated_prompt if result.prompts else "No translation requested."

    # --- 12. Translation ---
    translation_text = ""
    if result.translation:
        translation_text = result.translation.translated
    else:
        translation_text = "No translation requested."

    # --- 13. Errors ---
    errors_text = "\n".join(result.errors) if result.errors else "No errors."

    return (
        basic_info,
        lyrics_text,
        melody_text,
        structure_text,
        vocal_text,
        emotion_text,
        dynamics_text,
        instruments_text,
        suno_prompt,
        generic_prompt,
        translated_prompt,
        translation_text,
        errors_text,
    )


# Build Gradio UI
lang_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items()]
target_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items() if k != "auto"]

with gr.Blocks(
    title="MusicLens - 音乐完整复刻分析",
    theme=gr.themes.Soft(),
    css="""
    .main-title { text-align: center; margin-bottom: 0.5em; }
    .subtitle { text-align: center; color: #666; margin-bottom: 1.5em; }
    .prompt-box textarea { font-family: monospace !important; font-size: 13px !important; }
    """
) as demo:
    gr.HTML("""
    <div class="main-title">
        <h1>MusicLens - 音乐完整复刻分析工具</h1>
    </div>
    <div class="subtitle">
        <p>上传音乐 → 自动分析歌词 / 音调 / 节奏 / 语气 / 力度 / 情感 / 结构 → 生成 100% 还原提示词 → 复制到 Suno/Udio 生成复刻版或外语版</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                type="filepath",
                label="Upload Music / 上传音乐文件",
            )
        with gr.Column(scale=1):
            source_lang = gr.Dropdown(
                choices=lang_choices,
                value="auto",
                label="Song Language / 歌曲语言",
            )
            target_lang = gr.Dropdown(
                choices=target_choices,
                value="en",
                label="Translation Target / 翻译目标语言",
            )
            analyze_btn = gr.Button(
                "Start Full Analysis / 开始完整分析",
                variant="primary",
                size="lg",
            )

    with gr.Tabs():
        with gr.TabItem("Overview / 总览"):
            basic_output = gr.Textbox(
                label="Basic Info / 基本信息",
                lines=12, interactive=False,
            )

        with gr.TabItem("Lyrics / 歌词"):
            lyrics_output = gr.Textbox(
                label="Lyrics with Timestamps / 歌词 (含时间戳)",
                lines=25, interactive=False, show_copy_button=True,
            )

        with gr.TabItem("Melody / 旋律音调"):
            melody_output = gr.Textbox(
                label="Melody: Notes, Duration, Intervals / 旋律：音符、长短音、音程",
                lines=30, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )

        with gr.TabItem("Structure / 曲式结构"):
            structure_output = gr.Textbox(
                label="Song Structure / 曲式结构",
                lines=15, interactive=False,
            )

        with gr.TabItem("Vocal Style / 演唱风格"):
            vocal_output = gr.Textbox(
                label="Vocal Technique: Vibrato, Dynamics, Register, Tone, Articulation / 演唱技巧分析",
                lines=20, interactive=False, show_copy_button=True,
            )

        with gr.TabItem("Emotion / 情感语气"):
            emotion_output = gr.Textbox(
                label="Emotion & Mood Analysis / 情感与语气分析",
                lines=25, interactive=False, show_copy_button=True,
            )

        with gr.TabItem("Dynamics / 力度音量"):
            dynamics_output = gr.Textbox(
                label="Dynamics & Volume Map / 力度与音量变化",
                lines=20, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )

        with gr.TabItem("Instruments / 乐器"):
            instruments_output = gr.Textbox(
                label="Detected Instruments / 检测到的乐器",
                lines=8, interactive=False,
            )

        with gr.TabItem("Suno Prompt / Suno提示词"):
            suno_output = gr.Textbox(
                label="Suno AI Prompt (copy & paste to Suno) / Suno 提示词（直接复制使用）",
                lines=25, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )

        with gr.TabItem("Full Prompt / 完整提示词"):
            generic_output = gr.Textbox(
                label="Complete Reproduction Prompt / 完整还原提示词",
                lines=40, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )

        with gr.TabItem("Translated / 外语版提示词"):
            translated_prompt_output = gr.Textbox(
                label="Translated Reproduction Prompt / 外语版完整提示词",
                lines=40, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )

        with gr.TabItem("Translation / 翻译歌词"):
            translation_output = gr.Textbox(
                label="Translated Lyrics / 翻译后的歌词",
                lines=20, interactive=False, show_copy_button=True,
            )

        with gr.TabItem("Log / 日志"):
            errors_output = gr.Textbox(
                label="Analysis Log / 分析日志",
                lines=10, interactive=False,
            )

    analyze_btn.click(
        fn=run_analysis,
        inputs=[audio_input, source_lang, target_lang],
        outputs=[
            basic_output,
            lyrics_output,
            melody_output,
            structure_output,
            vocal_output,
            emotion_output,
            dynamics_output,
            instruments_output,
            suno_output,
            generic_output,
            translated_prompt_output,
            translation_output,
            errors_output,
        ],
    )

    gr.Markdown(
        """
        ---
        **Analysis Modules / 分析模块**:
        Whisper (lyrics) | librosa PYIN (melody + note timing) | Beat Tracking (rhythm) |
        Krumhansl-Kessler (key) | Self-Similarity (structure) | Spectral (instruments) |
        Vibrato/Dynamics/Register (vocal style) | Valence-Arousal (emotion) | RMS Loudness (dynamics)

        **How to use / 使用流程**: Upload → Analyze → Copy "Suno Prompt" or "Full Prompt" → Paste into Suno/Udio → Generate
        """
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
