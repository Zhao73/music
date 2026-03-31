"""MusicLens — Gradio Web UI matched to actual Suno/Udio interface + Music Creator."""

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
    build_suno_lyrics_from_fields,
    build_udio_prompt_from_fields,
)
from inspiration.generator import (
    fully_random,
    random_from_genre,
    random_from_mood,
    mutate_params,
    hit_optimized,
    format_inspiration,
    InspirationResult,
    GENRES,
)
from chart_data.knowledge_base import get_popularity_score, get_chart_patterns, CHART_PATTERNS
from chart_data.analyzer import format_chart_score
from chart_data.fetcher import is_billboard_available, fetch_billboard_hot100


def run_analysis(audio_file, source_lang, target_lang, translation_mode, api_key, progress=gr.Progress()):
    if audio_file is None:
        empty = "Please upload an audio file. / 请上传音乐文件。"
        return (empty,) + ("",) * 15 + ("", None, None, None) + (None,)

    def progress_callback(step, fraction):
        progress(fraction, desc=step)

    mode = "intelligent" if translation_mode == "Intelligent (LLM)" else "simple"

    try:
        result = analyze(
            audio_path=audio_file,
            source_language=source_lang if source_lang != "auto" else None,
            target_language=target_lang if target_lang else None,
            progress_callback=progress_callback,
            translation_mode=mode,
            llm_api_key=api_key or "",
        )
    except Exception as e:
        import traceback
        err_detail = traceback.format_exc()
        error_msg = f"Analysis crashed: {e}\n\n{err_detail}"
        return (error_msg,) + ("",) * 15 + ("", None, None, None) + (None,)

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

    # --- 17. Score / Sheet Music ---
    score_info = ""
    score_xml = None
    score_midi = None
    score_pdf = None
    if result.score and result.score.success:
        score_info = result.score.summary
        score_xml = result.score.musicxml_path if result.score.musicxml_path else None
        score_midi = result.score.midi_path if result.score.midi_path else None
        score_pdf = result.score.pdf_path if result.score.pdf_path else None
    elif result.score and result.score.error:
        score_info = f"Score generation issue: {result.score.error}"

    return (
        info, lyrics, melody, chords, drums, structure,
        vocal, emotion, dynamics, instruments,
        suno_style, suno_lyrics,
        generic, suno_translated, translation, log,
        score_info, score_xml, score_midi, score_pdf,
        result,  # AnalysisResult stored in gr.State for Music Creator
    )


# =========================================================================
# Music Creator helper functions
# =========================================================================

def prefill_creator(analysis_result):
    """Extract fields from AnalysisResult to pre-fill the Music Creator tab."""
    if analysis_result is None:
        return [gr.update()] * 9

    r = analysis_result
    bpm = r.rhythm.bpm if r.rhythm else 120.0
    key = r.key.key if r.key else "C major"
    chord_prog = ""
    if r.chords and hasattr(r.chords, "key_chords") and r.chords.key_chords:
        chord_prog = r.chords.key_chords
    lyrics = r.lyrics.full_text if r.lyrics else ""
    mood = r.emotion.overall_mood if r.emotion else ""
    instruments = r.instruments.detected if r.instruments else []
    vocal_tags = r.vocal_style.style_tags if r.vocal_style else []
    drum_groove = ""
    if r.drum_patterns and hasattr(r.drum_patterns, "groove_type"):
        drum_groove = r.drum_patterns.groove_type
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
        gr.update(value=bpm),
        gr.update(value=key if key in KEY_OPTIONS else "C major"),
        gr.update(value=chord_prog),
        gr.update(value=lyrics),
        gr.update(value=matched_mood),
        gr.update(value=matched_instruments),
        gr.update(value=matched_vocal),
        gr.update(value=matched_drum),
        gr.update(value=language),
    ]


def do_generate_lyria(api_key, bpm, key, chord_prog, lyrics, mood, instruments,
                      vocal_tags, drum_groove, language, genre):
    """Generate music with Lyria and return audio path + prompt preview + status."""
    if not api_key:
        return None, "", "Error: Please enter your Gemini API Key. / 请输入 Gemini API Key。"

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
    """Build Suno v5.5 style + lyrics with metatags for copy-paste."""
    style = build_suno_style_from_fields(
        bpm=bpm, key=key, chord_progression=chord_prog,
        instruments=instruments or None, mood=mood,
        vocal_style_tags=vocal_tags or None, drum_groove=drum_groove,
        language=language, genre=genre,
    )
    # v5.5: Auto-add section structure + energy tags to lyrics
    lyrics_out = build_suno_lyrics_from_fields(
        lyrics=lyrics,
        mood=mood,
        vocal_style_tags=vocal_tags,
    )
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


# =========================================================================
# Inspiration helper functions
# =========================================================================

def do_generate_inspiration(mode, genre, mood_sel, variation, seed_text):
    """Generate inspiration based on selected mode."""
    seed = int(seed_text) if seed_text and seed_text.strip().isdigit() else None

    if mode == "Random Genre":
        result = random_from_genre(genre or "pop", seed=seed)
    elif mode == "Random Mood":
        result = random_from_mood(mood_sel or "happy / energetic", seed=seed)
    elif mode == "Hit Formula":
        result = hit_optimized(genre or "pop", seed=seed)
    elif mode == "Fully Random":
        result = fully_random(seed=seed)
    else:
        result = fully_random(seed=seed)

    display = format_inspiration(result)

    # Build preview prompts
    lyria_preview = build_lyria_prompt(
        bpm=result.bpm, key=result.key, chord_progression=result.chord_progression,
        instruments=result.instruments, mood=result.mood,
        vocal_style_tags=result.vocal_style_tags, drum_groove=result.drum_groove,
        language=result.language, genre=result.genre,
    )
    suno_preview = build_suno_style_from_fields(
        bpm=result.bpm, key=result.key, chord_progression=result.chord_progression,
        instruments=result.instruments, mood=result.mood,
        vocal_style_tags=result.vocal_style_tags, drum_groove=result.drum_groove,
        language=result.language, genre=result.genre,
    )

    return display, f"--- Lyria Prompt ---\n{lyria_preview}\n\n--- Suno Style ---\n{suno_preview}", result


def do_apply_inspiration(inspiration_result):
    """Apply InspirationResult to Music Creator fields."""
    if inspiration_result is None:
        return [gr.update()] * 9
    r = inspiration_result

    # Match mood to dropdown
    matched_mood = ""
    if r.mood:
        for opt in MOOD_OPTIONS:
            if any(w in r.mood.lower() for w in opt.lower().split(" / ")):
                matched_mood = opt
                break

    # Match instruments to checkboxes
    matched_instruments = []
    if r.instruments:
        inst_lower = " ".join(r.instruments).lower()
        for opt in INSTRUMENT_OPTIONS:
            opt_low = opt.lower()
            if any(word in inst_lower for word in opt_low.split(" / ")[0].split()):
                matched_instruments.append(opt)

    # Match vocal tags to checkboxes
    matched_vocal = []
    if r.vocal_style_tags:
        tags_lower = " ".join(r.vocal_style_tags).lower()
        for opt in VOCAL_STYLE_OPTIONS:
            if opt.lower().split("/")[0].strip() in tags_lower or opt.lower() in tags_lower:
                matched_vocal.append(opt)

    # Match drum groove
    matched_drum = ""
    if r.drum_groove:
        for opt in DRUM_GROOVE_OPTIONS:
            if any(w in r.drum_groove.lower() for w in opt.lower().split(" / ")):
                matched_drum = opt
                break

    return [
        gr.update(value=r.bpm),
        gr.update(value=r.key if r.key in KEY_OPTIONS else "C major"),
        gr.update(value=r.chord_progression),
        gr.update(value=""),  # lyrics — not generated
        gr.update(value=matched_mood),
        gr.update(value=matched_instruments),
        gr.update(value=matched_vocal),
        gr.update(value=matched_drum),
        gr.update(value=r.language),
    ]


# =========================================================================
# Chart Insights helper functions
# =========================================================================

def do_score_chart_potential(analysis_result):
    """Score an analysis result against chart patterns."""
    if analysis_result is None:
        return "Please run analysis first. / 请先分析一首音乐。"

    params = {}
    r = analysis_result
    if r.rhythm:
        params["bpm"] = r.rhythm.bpm
    if r.key:
        params["key"] = r.key.key
    if r.chords and r.chords.chord_progression:
        params["chord_progression"] = r.chords.chord_progression
    if r.emotion:
        params["mood"] = r.emotion.overall_mood
    if r.duration_seconds:
        params["duration_seconds"] = r.duration_seconds

    result = get_popularity_score(params)
    return format_chart_score(result)


def do_fetch_billboard():
    """Fetch current Billboard Hot 100."""
    if not is_billboard_available():
        return "billboard.py not installed. Run: pip install billboard.py"
    tracks = fetch_billboard_hot100()
    if not tracks:
        return "Failed to fetch Billboard data."
    if "error" in tracks[0]:
        return f"Error: {tracks[0]['error']}"

    lines = ["Billboard Hot 100 — Current Chart\n"]
    for t in tracks[:50]:
        lines.append(f"  #{t['rank']:3d} | {t['title']} — {t['artist']} (Weeks: {t.get('weeks', '?')})")
    return "\n".join(lines)


def do_get_chart_summary():
    """Get static chart patterns summary."""
    p = CHART_PATTERNS
    lines = [
        "Chart Hit Patterns (Based on Research)",
        "=" * 45,
        "",
        f"Average BPM: {p['tempo']['mean']:.0f} (sweet spot: {p['tempo']['hit_range'][0]}-{p['tempo']['hit_range'][1]})",
        f"Most Common Keys: {', '.join(p['key']['most_common'][:5])}",
        "",
        "Top Chord Progressions:",
    ]
    for prog in p["chord_progressions"][:5]:
        lines.append(f"  {prog['name']:15s} — {prog['frequency']*100:.0f}% of hits ({', '.join(prog['genres'])})")
    lines.extend([
        "",
        f"Time Signature: 4/4 ({p['time_signature']['4/4']*100:.0f}% of songs)",
        f"Danceability: {p['danceability']['mean']:.2f} avg (hit range: {p['danceability']['hit_range'][0]}-{p['danceability']['hit_range'][1]})",
        f"Energy: {p['energy']['mean']:.2f} avg (hit range: {p['energy']['hit_range'][0]}-{p['energy']['hit_range'][1]})",
        f"Valence: {p['valence']['mean']:.2f} avg (hit range: {p['valence']['hit_range'][0]}-{p['valence']['hit_range'][1]})",
        f"Ideal Duration: {p['duration_seconds']['hit_range'][0]}-{p['duration_seconds']['hit_range'][1]} seconds",
    ])
    return "\n".join(lines)


# =========================================================================
# Build Gradio UI
# =========================================================================

lang_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items()]
target_choices = [(v, k) for k, v in LANGUAGE_OPTIONS.items() if k != "auto"]
creator_lang_choices = [
    "English", "Chinese", "Japanese", "Korean", "Spanish",
    "French", "German", "Portuguese", "Russian", "Arabic", "Italian", "Thai",
]

with gr.Blocks(
    title="MusicLens",
    theme=gr.themes.Soft(),
    css="""
    .mono textarea { font-family: monospace !important; font-size: 12px !important; }
    .prompt-box textarea { font-family: monospace !important; font-size: 13px !important; }
    """
) as demo:
    analysis_state = gr.State(value=None)

    gr.HTML("""
    <div style="text-align:center; margin-bottom:1em;">
        <h1>MusicLens — 音乐完整复刻分析 & 创作</h1>
        <p style="color:#666;">
            Upload → Demucs Separation → 12 Analyzers → Copy to Suno / Generate with Lyria<br>
            上传音乐 → 人声分离 → 12项分析 → 复制到 Suno·Udio / 直接用 Lyria 生成音乐
        </p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(type="filepath", label="Upload Music / 上传音乐")
        with gr.Column(scale=1):
            source_lang = gr.Dropdown(choices=lang_choices, value="auto", label="Song Language / 歌曲语言")
            target_lang = gr.Dropdown(choices=target_choices, value="en", label="Target Language / 目标语言")
            with gr.Accordion("Translation Settings / 翻译设置", open=False):
                translation_mode = gr.Radio(
                    choices=["Simple (Google)", "Intelligent (LLM)"],
                    value="Simple (Google)",
                    label="Translation Mode / 翻译模式",
                    info="Intelligent 模式用 Gemini LLM 智能翻译，保留音节、押韵、情感",
                )
                gemini_api_key = gr.Textbox(
                    label="Gemini API Key",
                    type="password",
                    placeholder="Intelligent 模式需要 API Key (aistudio.google.com 免费获取)",
                )
            btn = gr.Button("Analyze / 开始分析", variant="primary", size="lg")

    with gr.Tabs():
        # =====================================================================
        # TAB: Suno (most important for copy-paste workflow)
        # =====================================================================
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
                        lines=18, interactive=False, show_copy_button=True,
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

        # =====================================================================
        # TAB: Music Creator / 音乐创作
        # =====================================================================
        with gr.TabItem("Music Creator / 音乐创作"):
            gr.Markdown(
                "**分析完成后参数会自动预填。** 可编辑任意字段，然后用 Lyria 生成或导出到 Suno/Udio。\n\n"
                "**Parameters auto-fill after analysis.** Edit any field, then generate with Lyria or export to Suno/Udio."
            )

            with gr.Row():
                # --- Left column: parameters ---
                with gr.Column(scale=1):
                    api_key_input = gr.Textbox(
                        label="Gemini API Key (for Lyria generation)",
                        type="password",
                        placeholder="Same key as Translation Settings / 与翻译设置共用",
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
                    variant="primary", size="lg",
                )
                creator_suno_btn = gr.Button("Copy for Suno / 导出 Suno", variant="secondary")
                creator_udio_btn = gr.Button("Copy for Udio / 导出 Udio", variant="secondary")

            # --- Output area ---
            with gr.Row():
                with gr.Column():
                    generated_audio = gr.Audio(
                        label="Generated Audio / 生成的音频",
                        type="filepath", interactive=False,
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

            # Suno/Udio export outputs
            creator_suno_style_out = gr.Textbox(
                label="Suno Style (copy to Style box) / Suno 风格",
                lines=4, interactive=False, show_copy_button=True,
                elem_classes=["prompt-box"],
            )
            creator_suno_lyrics_out = gr.Textbox(
                label="Suno Lyrics (copy to Lyrics box) / Suno 歌词",
                lines=8, interactive=False, show_copy_button=True,
            )
            creator_udio_out = gr.Textbox(
                label="Udio Prompt / Udio 提示词",
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
            creator_suno_btn.click(
                fn=do_copy_suno,
                inputs=creator_inputs,
                outputs=[creator_suno_style_out, creator_suno_lyrics_out],
            )

            # Wire Udio export
            creator_udio_btn.click(
                fn=do_copy_udio,
                inputs=creator_inputs,
                outputs=[creator_udio_out],
            )

        # =====================================================================
        # TAB: Inspiration / 灵感
        # =====================================================================
        with gr.TabItem("Inspiration / 灵感"):
            gr.Markdown(
                "**随机生成音乐参数，获取创作灵感。** 生成的参数可一键应用到 Music Creator。\n\n"
                "**Generate random musically-valid parameters for creative inspiration.**"
            )

            inspiration_state = gr.State(value=None)

            with gr.Row():
                with gr.Column(scale=1):
                    insp_mode = gr.Radio(
                        choices=["Fully Random", "Random Genre", "Random Mood", "Hit Formula"],
                        value="Fully Random",
                        label="Mode / 模式",
                    )
                    insp_genre = gr.Dropdown(
                        choices=[""] + GENRES,
                        value="pop",
                        label="Genre (for Random Genre / Hit Formula)",
                    )
                    insp_mood = gr.Dropdown(
                        choices=[""] + MOOD_OPTIONS,
                        value="",
                        label="Mood (for Random Mood)",
                    )
                    insp_variation = gr.Slider(
                        minimum=0, maximum=100, value=30, step=5,
                        label="Variation % (for Mutate)",
                        visible=False,
                    )
                    insp_seed = gr.Textbox(
                        label="Seed (optional, for reproducibility)",
                        placeholder="Leave empty for random",
                    )
                    with gr.Row():
                        insp_generate_btn = gr.Button("Generate Inspiration / 生成灵感", variant="primary")
                        insp_apply_btn = gr.Button("Apply to Creator / 应用到创作", variant="secondary")

                with gr.Column(scale=1):
                    insp_output = gr.Textbox(
                        label="Generated Parameters / 生成的参数",
                        lines=15, interactive=False,
                        elem_classes=["mono"],
                    )
                    insp_prompt_preview = gr.Textbox(
                        label="Prompt Preview / 提示词预览",
                        lines=12, interactive=False, show_copy_button=True,
                        elem_classes=["prompt-box"],
                    )

            # Wire inspiration generation
            insp_generate_btn.click(
                fn=do_generate_inspiration,
                inputs=[insp_mode, insp_genre, insp_mood, insp_variation, insp_seed],
                outputs=[insp_output, insp_prompt_preview, inspiration_state],
            )

            # Wire apply to creator
            insp_apply_btn.click(
                fn=do_apply_inspiration,
                inputs=[inspiration_state],
                outputs=[
                    bpm_slider, key_dropdown, chord_input, lyrics_input,
                    mood_dropdown, instruments_checkbox, vocal_checkbox,
                    drum_dropdown, language_dropdown,
                ],
            )

        # =====================================================================
        # TAB: Chart Insights / 排行榜分析
        # =====================================================================
        with gr.TabItem("Chart Insights / 排行榜分析"):
            gr.Markdown(
                "**了解热门歌曲的共同特征，评估你的音乐的排行榜潜力。**\n\n"
                "**Understand what makes songs chart — score your music's hit potential.**"
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Your Song's Chart Potential / 排行榜潜力")
                    chart_score_btn = gr.Button("Score My Song / 评估我的音乐", variant="primary")
                    chart_score_output = gr.Textbox(
                        label="Chart Score / 排行榜评分",
                        lines=18, interactive=False,
                        elem_classes=["mono"],
                    )

                with gr.Column(scale=1):
                    gr.Markdown("### Chart Patterns / 排行榜规律")
                    chart_patterns_btn = gr.Button("Show Chart Patterns / 显示排行榜规律", variant="secondary")
                    chart_patterns_output = gr.Textbox(
                        label="Chart Patterns / 排行榜数据",
                        lines=18, interactive=False,
                        elem_classes=["mono"],
                    )

            with gr.Accordion("Live Billboard Data / 实时排行榜 (Optional)", open=False):
                gr.Markdown("Requires `billboard.py`: `pip install billboard.py`")
                billboard_btn = gr.Button("Fetch Billboard Hot 100 / 获取 Billboard 榜单")
                billboard_output = gr.Textbox(
                    label="Billboard Hot 100",
                    lines=25, interactive=False,
                    elem_classes=["mono"],
                )

            # Wire chart buttons
            chart_score_btn.click(
                fn=do_score_chart_potential,
                inputs=[analysis_state],
                outputs=[chart_score_output],
            )
            chart_patterns_btn.click(
                fn=do_get_chart_summary,
                inputs=[],
                outputs=[chart_patterns_output],
            )
            billboard_btn.click(
                fn=do_fetch_billboard,
                inputs=[],
                outputs=[billboard_output],
            )

        # =====================================================================
        # Analysis Result Tabs
        # =====================================================================
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

        with gr.TabItem("Score / 乐谱"):
            gr.Markdown(
                "**自动生成的可视化乐谱** — 包含旋律五线谱、和弦标记、鼓谱。\n\n"
                "下载 MusicXML 可导入 MuseScore/Finale/Sibelius 编辑，MIDI 可直接播放。"
            )
            out_score_info = gr.Textbox(label="Score Info / 乐谱信息", lines=5, interactive=False)
            with gr.Row():
                out_score_xml = gr.File(label="Download MusicXML / 下载 MusicXML（可导入 MuseScore）", interactive=False)
                out_score_midi = gr.File(label="Download MIDI / 下载 MIDI（可播放）", interactive=False)
                out_score_pdf = gr.File(label="Download PDF/PNG / 下载乐谱图片", interactive=False)

        with gr.TabItem("Log"):
            out_log = gr.Textbox(label="Log", lines=10, interactive=False)

    # Wire analysis button — outputs include score files + analysis_state
    btn.click(
        fn=run_analysis,
        inputs=[audio_input, source_lang, target_lang, translation_mode, gemini_api_key],
        outputs=[
            out_info, out_lyrics, out_melody, out_chords, out_drums, out_structure,
            out_vocal, out_emotion, out_dynamics, out_instruments,
            out_suno_style, out_suno_lyrics,
            out_generic, out_suno_translated, out_translation, out_log,
            out_score_info, out_score_xml, out_score_midi, out_score_pdf,
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

    gr.Markdown("""
    ---
    **How to use with Suno**: Open Suno → Custom mode → Copy **Style** to Style box → Copy **Lyrics** to Lyrics box → Create

    **Music Creator**: Edit parameters → Generate with Lyria / Export to Suno / Udio

    **Inspiration**: Generate random musically-valid parameters → Apply to Creator → Generate

    **Chart Insights**: Score your music's chart potential → Get improvement suggestions

    **REST API**: Run `uvicorn api:app` for programmatic access at `/api/health`, `/api/analyze`, `/api/generate`, `/api/inspire`, `/api/charts/*`
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)
