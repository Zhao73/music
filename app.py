"""MusicLens - Gradio Web UI for complete music analysis and cross-language recreation."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
from pipeline import analyze, AnalysisResult
from config import (
    LANGUAGE_OPTIONS,
    KEY_OPTIONS,
    MOOD_OPTIONS,
    DRUM_GROOVE_OPTIONS,
    INSTRUMENT_OPTIONS,
    VOCAL_STYLE_OPTIONS,
)
from utils.audio_io import format_time
from music_generation.lyria_client import is_available as lyria_available, generate_music
from music_generation.prompt_builder import (
    build_lyria_prompt,
    build_suno_style_from_fields,
    build_udio_prompt_from_fields,
)


def run_analysis(audio_file, source_lang, target_lang, progress=gr.Progress()):
    """Main analysis function called by the Gradio UI."""
    if audio_file is None:
        empty = "Please upload an audio file."
        return (empty,) + ("",) * 12 + (None,)

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
        result,  # AnalysisResult stored in gr.State for Music Creator
    )


def prefill_creator(analysis_result):
    """Extract fields from AnalysisResult to pre-fill the Music Creator tab."""
    if analysis_result is None:
        return [gr.update()] * 9

    r = analysis_result
    bpm = r.rhythm.bpm if r.rhythm else 120.0
    key = r.key.key if r.key else "C major"
    chord_prog = ""
    if hasattr(r, "chords") and r.chords and hasattr(r.chords, "progression_str"):
        chord_prog = r.chords.progression_str
    lyrics = r.lyrics.full_text if r.lyrics else ""
    mood = r.emotion.overall_mood if r.emotion else ""
    instruments = r.instruments.detected if r.instruments else []
    vocal_tags = r.vocal_style.style_tags if r.vocal_style else []
    drum_groove = ""
    if hasattr(r, "drums") and r.drums and hasattr(r.drums, "groove_type"):
        drum_groove = r.drums.groove_type
    language = LANGUAGE_OPTIONS.get(
        r.lyrics.detected_language if r.lyrics else "", "English"
    )

    # Map detected instruments to checkbox options
    matched_instruments = []
    if instruments:
        inst_lower = " ".join(instruments).lower()
        for opt in INSTRUMENT_OPTIONS:
            opt_low = opt.lower()
            if any(word in inst_lower for word in opt_low.split(" / ")[0].split()):
                matched_instruments.append(opt)

    # Map vocal tags to checkbox options
    matched_vocal = []
    if vocal_tags:
        tags_lower = " ".join(vocal_tags).lower()
        for opt in VOCAL_STYLE_OPTIONS:
            if opt.lower().split("/")[0].strip() in tags_lower or opt.lower() in tags_lower:
                matched_vocal.append(opt)

    # Match mood to dropdown
    matched_mood = ""
    if mood:
        mood_low = mood.lower()
        for opt in MOOD_OPTIONS:
            if any(w in mood_low for w in opt.lower().split(" / ")):
                matched_mood = opt
                break

    # Match drum groove
    matched_drum = ""
    if drum_groove:
        drum_low = drum_groove.lower()
        for opt in DRUM_GROOVE_OPTIONS:
            if any(w in drum_low for w in opt.lower().split(" / ")):
                matched_drum = opt
                break

    return [
        gr.update(value=bpm),           # bpm_slider
        gr.update(value=key if key in KEY_OPTIONS else "C major"),  # key_dropdown
        gr.update(value=chord_prog),    # chord_input
        gr.update(value=lyrics),        # lyrics_input
        gr.update(value=matched_mood),  # mood_dropdown
        gr.update(value=matched_instruments),  # instruments_checkbox
        gr.update(value=matched_vocal),        # vocal_checkbox
        gr.update(value=matched_drum),         # drum_dropdown
        gr.update(value=language),             # language_dropdown
    ]


def do_generate_lyria(api_key, bpm, key, chord_prog, lyrics, mood, instruments,
                      vocal_tags, drum_groove, language, genre):
    """Generate music with Lyria and return audio path + prompt preview + status."""
    if not api_key:
        return None, "", "Error: Please enter your Gemini API Key."

    prompt = build_lyria_prompt(
        bpm=bpm, key=key, chord_progression=chord_prog, lyrics=lyrics,
        instruments=instruments or None, mood=mood,
        vocal_style_tags=vocal_tags or None, drum_groove=drum_groove,
        language=language, genre=genre,
    )

    result = generate_music(prompt, api_key=api_key)
    if result.success:
        return result.audio_path, prompt, f"Generation successful! Duration: {result.duration_seconds:.1f}s"
    else:
        return None, prompt, f"Error: {result.error}"


def do_copy_suno(bpm, key, chord_prog, lyrics, mood, instruments,
                 vocal_tags, drum_groove, language, genre):
    """Build Suno style + lyrics for copy-paste."""
    style = build_suno_style_from_fields(
        bpm=bpm, key=key, chord_progression=chord_prog,
        instruments=instruments or None, mood=mood,
        vocal_style_tags=vocal_tags or None, drum_groove=drum_groove,
        language=language, genre=genre,
    )
    lyrics_out = lyrics.strip() if lyrics else ""
    return style, lyrics_out


def do_copy_udio(bpm, key, chord_prog, lyrics, mood, instruments,
                 vocal_tags, drum_groove, language, genre):
    """Build Udio-format prompt for copy-paste."""
    prompt = build_udio_prompt_from_fields(
        bpm=bpm, key=key, chord_progression=chord_prog, lyrics=lyrics,
        instruments=instruments or None, mood=mood,
        vocal_style_tags=vocal_tags or None, drum_groove=drum_groove,
        language=language, genre=genre,
    )
    return prompt


# Build Gradio UI
lang_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items()]
target_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items() if k != "auto"]
creator_lang_choices = [
    "English", "Chinese", "Japanese", "Korean", "Spanish",
    "French", "German", "Portuguese", "Russian", "Arabic", "Italian", "Thai",
]

with gr.Blocks(
    title="MusicLens - 音乐完整复刻分析 & 创作",
    theme=gr.themes.Soft(),
    css="""
    .main-title { text-align: center; margin-bottom: 0.5em; }
    .subtitle { text-align: center; color: #666; margin-bottom: 1.5em; }
    .prompt-box textarea { font-family: monospace !important; font-size: 13px !important; }
    .creator-section { border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 4px 0; }
    """
) as demo:
    # Shared state for analysis result
    analysis_state = gr.State(value=None)

    gr.HTML("""
    <div class="main-title">
        <h1>MusicLens - 音乐完整复刻分析 & 创作工具</h1>
    </div>
    <div class="subtitle">
        <p>上传音乐 → 自动分析 → 编辑参数 → 直接用 Lyria 生成音乐 / 导出到 Suno·Udio</p>
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
        # =====================================================================
        # TAB: Music Creator / 音乐创作
        # =====================================================================
        with gr.TabItem("Music Creator / 音乐创作"):
            gr.Markdown(
                "**分析完成后参数会自动预填。** 可编辑任意字段，然后用 Lyria 生成或导出到 Suno/Udio。"
            )

            with gr.Row():
                # --- Left column: parameters ---
                with gr.Column(scale=1):
                    api_key_input = gr.Textbox(
                        label="Gemini API Key (for Lyria generation)",
                        type="password",
                        placeholder="Enter your API key...",
                    )
                    genre_input = gr.Textbox(
                        label="Genre / 流派",
                        placeholder="e.g. Pop, Rock, R&B, Electronic...",
                    )
                    bpm_slider = gr.Slider(
                        minimum=40, maximum=220, value=120, step=1,
                        label="BPM / 速度",
                    )
                    key_dropdown = gr.Dropdown(
                        choices=KEY_OPTIONS, value="C major",
                        label="Key / 调性",
                    )
                    chord_input = gr.Textbox(
                        label="Chord Progression / 和弦进行",
                        placeholder="e.g. C - Am - F - G",
                    )
                    drum_dropdown = gr.Dropdown(
                        choices=[""] + DRUM_GROOVE_OPTIONS,
                        value="",
                        label="Drum Groove / 鼓点节奏",
                    )
                    mood_dropdown = gr.Dropdown(
                        choices=[""] + MOOD_OPTIONS,
                        value="",
                        label="Mood / 情绪",
                    )
                    language_dropdown = gr.Dropdown(
                        choices=creator_lang_choices,
                        value="English",
                        label="Language / 演唱语言",
                    )

                # --- Right column: content ---
                with gr.Column(scale=1):
                    lyrics_input = gr.Textbox(
                        label="Lyrics / 歌词",
                        lines=12,
                        placeholder="Paste or edit lyrics here...",
                    )
                    instruments_checkbox = gr.CheckboxGroup(
                        choices=INSTRUMENT_OPTIONS,
                        label="Instruments / 乐器",
                    )
                    vocal_checkbox = gr.CheckboxGroup(
                        choices=VOCAL_STYLE_OPTIONS,
                        label="Vocal Style / 演唱风格",
                    )

            # Pre-fill button
            prefill_btn = gr.Button("Pre-fill from Analysis / 从分析结果预填", variant="secondary")

            # --- Action buttons ---
            with gr.Row():
                generate_btn = gr.Button(
                    "Generate with Lyria / Lyria 生成",
                    variant="primary",
                    size="lg",
                )
                suno_btn = gr.Button("Copy for Suno / 导出 Suno", variant="secondary")
                udio_btn = gr.Button("Copy for Udio / 导出 Udio", variant="secondary")

            # --- Output area ---
            with gr.Row():
                with gr.Column():
                    generated_audio = gr.Audio(
                        label="Generated Audio / 生成的音频",
                        type="filepath",
                        interactive=False,
                    )
                    generation_status = gr.Textbox(
                        label="Status / 状态", interactive=False, lines=2,
                    )
                with gr.Column():
                    prompt_preview = gr.Textbox(
                        label="Lyria Prompt Preview / 提示词预览",
                        lines=8, interactive=False, show_copy_button=True,
                        elem_classes=["prompt-box"],
                    )

            # Suno export outputs
            with gr.Row(visible=False) as suno_export_row:
                pass
            suno_style_output = gr.Textbox(
                label="Suno Style (copy to Style box) / Suno 风格",
                lines=4, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )
            suno_lyrics_output = gr.Textbox(
                label="Suno Lyrics (copy to Lyrics box) / Suno 歌词",
                lines=8, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )
            udio_output = gr.Textbox(
                label="Udio Prompt (copy to Udio) / Udio 提示词",
                lines=8, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )

            # Shared input list for generation/export
            creator_inputs = [
                bpm_slider, key_dropdown, chord_input, lyrics_input,
                mood_dropdown, instruments_checkbox, vocal_checkbox,
                drum_dropdown, language_dropdown, genre_input,
            ]

            # Wire prefill
            prefill_btn.click(
                fn=prefill_creator,
                inputs=[analysis_state],
                outputs=[
                    bpm_slider, key_dropdown, chord_input, lyrics_input,
                    mood_dropdown, instruments_checkbox, vocal_checkbox,
                    drum_dropdown, language_dropdown,
                ],
            )

            # Wire generate
            generate_btn.click(
                fn=do_generate_lyria,
                inputs=[api_key_input] + creator_inputs,
                outputs=[generated_audio, prompt_preview, generation_status],
            )

            # Wire Suno export
            suno_btn.click(
                fn=do_copy_suno,
                inputs=creator_inputs,
                outputs=[suno_style_output, suno_lyrics_output],
            )

            # Wire Udio export
            udio_btn.click(
                fn=do_copy_udio,
                inputs=creator_inputs,
                outputs=[udio_output],
            )

        # =====================================================================
        # Analysis Result Tabs (existing)
        # =====================================================================
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

    # Wire analysis button — outputs include analysis_state
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
            analysis_state,
        ],
    ).then(
        fn=prefill_creator,
        inputs=[analysis_state],
        outputs=[
            bpm_slider, key_dropdown, chord_input, lyrics_input,
            mood_dropdown, instruments_checkbox, vocal_checkbox,
            drum_dropdown, language_dropdown,
        ],
    )

    gr.Markdown(
        """
        ---
        **Analysis Modules / 分析模块**:
        Whisper (lyrics) | librosa PYIN (melody + note timing) | Beat Tracking (rhythm) |
        Krumhansl-Kessler (key) | Self-Similarity (structure) | Spectral (instruments) |
        Vibrato/Dynamics/Register (vocal style) | Valence-Arousal (emotion) | RMS Loudness (dynamics)

        **Music Creator / 音乐创作**: Edit parameters → Generate with Lyria / Export to Suno / Udio

        **REST API**: Run `uvicorn api:app` for programmatic access at `/api/health`, `/api/analyze`, `/api/generate`
        """
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
