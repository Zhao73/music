"""MusicLens - Gradio Web UI for music analysis and cross-language recreation."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from pipeline import analyze
from config import LANGUAGE_OPTIONS


def run_analysis(audio_file, source_lang, target_lang, progress=gr.Progress()):
    """Main analysis function called by the Gradio UI."""
    if audio_file is None:
        return ("Please upload an audio file.",) + ("",) * 8

    def progress_callback(step, fraction):
        progress(fraction, desc=step)

    result = analyze(
        audio_path=audio_file,
        source_language=source_lang if source_lang != "auto" else None,
        target_language=target_lang if target_lang else None,
        progress_callback=progress_callback,
    )

    # Format outputs
    errors = "\n".join(result.errors) if result.errors else ""

    # Basic info
    basic_info = f"Duration: {result.duration}\n"
    if result.lyrics:
        basic_info += f"Detected Language: {result.lyrics.detected_language}\n"
    if result.rhythm:
        basic_info += f"BPM: {result.rhythm.bpm:.0f}\n"
    if result.key:
        basic_info += f"Key: {result.key.key} (confidence: {result.key.confidence:.2f})\n"
    if result.rhythm:
        basic_info += f"Time Signature: {result.rhythm.time_signature}\n"
        basic_info += f"Feel: {result.rhythm.feel}\n"
        basic_info += f"Energy: {result.rhythm.energy_level}\n"

    # Lyrics
    lyrics_text = ""
    if result.lyrics:
        lyrics_text = result.lyrics.full_text
        if result.lyrics.segments:
            lyrics_text += "\n\n--- Timed Segments ---\n"
            for seg in result.lyrics.segments:
                start = f"{seg['start']:.1f}s"
                end = f"{seg['end']:.1f}s"
                lyrics_text += f"[{start} - {end}] {seg['text']}\n"

    # Melody info
    melody_text = ""
    if result.melody:
        melody_text = result.melody.description

    # Structure
    structure_text = ""
    if result.structure:
        structure_text = result.structure.summary + "\n\n"
        for section in result.structure.sections:
            from utils.audio_io import format_time
            start = format_time(section.start_time)
            end = format_time(section.end_time)
            structure_text += f"  {section.label}: {start} - {end}\n"

    # Instruments
    instruments_text = ""
    if result.instruments:
        instruments_text = result.instruments.description

    # Prompts
    suno_prompt = result.prompts.suno_prompt if result.prompts else ""
    generic_prompt = result.prompts.generic_prompt if result.prompts else ""
    translated_prompt = result.prompts.translated_prompt if result.prompts else "No translation requested."

    # Translation
    translation_text = ""
    if result.translation:
        translation_text = result.translation.translated

    return (
        basic_info,
        lyrics_text,
        melody_text,
        structure_text,
        instruments_text,
        suno_prompt,
        generic_prompt,
        translated_prompt,
        translation_text if translation_text else "No translation requested.",
    )


# Build Gradio UI
lang_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items()]
target_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items() if k != "auto"]

with gr.Blocks(
    title="MusicLens - 音乐分析与跨语言复刻",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(
        """
        # 🎵 MusicLens - 音乐分析与跨语言复刻工具
        上传一首音乐，自动分析歌词、音调、节奏、曲式结构，生成 AI 音乐生成提示词。
        支持将歌词翻译为其他语言，用于制作外语版本。

        **使用方法**: 上传音频 → 选择语言 → 点击"开始分析" → 复制生成的提示词到 Suno/Udio 等工具
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                type="filepath",
                label="上传音乐文件 (MP3, WAV, FLAC, etc.)",
            )
            source_lang = gr.Dropdown(
                choices=lang_choices,
                value="auto",
                label="歌曲语言 (默认自动检测)",
            )
            target_lang = gr.Dropdown(
                choices=target_choices,
                value="en",
                label="翻译目标语言",
            )
            analyze_btn = gr.Button("🔍 开始分析", variant="primary", size="lg")

    with gr.Tabs():
        with gr.TabItem("📊 基本信息"):
            basic_output = gr.Textbox(label="音乐基本信息", lines=8, interactive=False)

        with gr.TabItem("📝 歌词"):
            lyrics_output = gr.Textbox(label="识别的歌词 (含时间戳)", lines=20, interactive=False)

        with gr.TabItem("🎵 旋律"):
            melody_output = gr.Textbox(label="旋律分析", lines=5, interactive=False)

        with gr.TabItem("🏗️ 曲式结构"):
            structure_output = gr.Textbox(label="歌曲结构", lines=10, interactive=False)

        with gr.TabItem("🎸 乐器"):
            instruments_output = gr.Textbox(label="检测到的乐器", lines=5, interactive=False)

        with gr.TabItem("✨ Suno 提示词"):
            suno_output = gr.Textbox(
                label="Suno AI 提示词 (可直接复制使用)",
                lines=20,
                interactive=False,
                show_copy_button=True,
            )

        with gr.TabItem("📋 通用提示词"):
            generic_output = gr.Textbox(
                label="通用 AI 音乐生成提示词",
                lines=25,
                interactive=False,
                show_copy_button=True,
            )

        with gr.TabItem("🌍 外语版提示词"):
            translated_prompt_output = gr.Textbox(
                label="翻译后的 AI 音乐生成提示词 (用于制作外语版本)",
                lines=25,
                interactive=False,
                show_copy_button=True,
            )

        with gr.TabItem("🔤 翻译歌词"):
            translation_output = gr.Textbox(
                label="翻译后的歌词",
                lines=20,
                interactive=False,
                show_copy_button=True,
            )

    analyze_btn.click(
        fn=run_analysis,
        inputs=[audio_input, source_lang, target_lang],
        outputs=[
            basic_output,
            lyrics_output,
            melody_output,
            structure_output,
            instruments_output,
            suno_output,
            generic_output,
            translated_prompt_output,
            translation_output,
        ],
    )

    gr.Markdown(
        """
        ---
        **说明**: 本工具仅用于学习研究目的。歌词识别使用 OpenAI Whisper，音频分析使用 librosa。
        生成的提示词可用于 Suno、Udio 等 AI 音乐生成工具来复刻或翻唱歌曲。
        """
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
