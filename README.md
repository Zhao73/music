# MusicLens - 音乐完整复刻分析与跨语言重制工具

上传一首歌，自动分析出**歌词、每个音符的音高和长短、节奏 BPM、调性、曲式结构、乐器、演唱风格（颤音/语气/力度/声区）、情感走向、音量变化**——生成一段完整的"提示词"，复制到 Suno/Udio 即可高度还原原曲，或一键生成外语翻唱版。

> 本项目仅用于学习研究目的（课程作业）。不需要任何付费 API。

---

## 核心工作流程

```
  音乐文件 (MP3/WAV/...)
       |
       v
  +-----------------------------------------+
  |         MusicLens 完整分析引擎            |
  |                                         |
  |  1. Whisper 歌词识别 (含时间戳)           |
  |  2. 逐音符旋律分析 (音高+长短音+音程)      |
  |  3. BPM / 拍号 / 节奏风格                |
  |  4. 调性检测 (大调/小调)                  |
  |  5. 曲式结构 (前奏→主歌→副歌→桥段→尾声)   |
  |  6. 乐器检测                             |
  |  7. 演唱风格 (颤音/声区/音色/连断音)       |
  |  8. 情感语气 (开心/悲伤/激昂/平静+变化曲线) |
  |  9. 力度音量 (强弱变化/渐强渐弱)           |
  +-----------------------------------------+
       |
       v
  完整复刻提示词 (Suno格式 / Udio格式 / 通用格式)
       |
       +---> 复制到 Suno/Udio → 高度还原原曲
       +---> 翻译歌词 → 外语版提示词 → 生成外语翻唱版
```

---

## 分析能力一览

| 分析维度 | 具体内容 | 技术实现 |
|---------|---------|---------|
| **歌词** | 完整歌词 + 每句起止时间戳，支持99种语言自动识别 | OpenAI Whisper |
| **旋律/音高** | 逐音符：音名(C4, A#3等)、频率Hz、起止时间 | librosa PYIN |
| **长短音** | 每个音符的持续时长，分类为：短音(staccato) / 中等 / 长音 / 持续音 | onset/offset 分析 |
| **音程** | 相邻音符之间的音程关系 (+M3, -P5, +octave等) | MIDI 距离计算 |
| **节奏** | BPM(精确到小数)、拍号(4/4 or 3/4)、节奏风格(快/慢/中) | beat tracking |
| **调性** | 调性(如 C major, A minor) + 置信度 | Krumhansl-Kessler |
| **曲式结构** | 自动切分：Intro→Verse→Chorus→Bridge→Outro + 每段时间范围 | 自相似矩阵+聚类 |
| **乐器** | 人声、鼓、贝斯、吉他(电/木)、钢琴、合成器、弦乐 | 频谱分析 |
| **颤音(Vibrato)** | 颤音频率(Hz)、幅度(cents)、出现比例 | f0抖动FFT分析 |
| **声区** | 胸声/头声/假声的比例分布 | MIDI音高分区 |
| **音色** | 气声感(breathiness)、明亮度(brightness)、鼻音(nasality) | 频谱特征 |
| **连断音** | legato(连音)vs staccato(断音)的比例 | onset间隔分析 |
| **情感/语气** | 整体情绪 + 10秒分段情绪变化曲线 + 情感弧线 | 效价-唤醒模型 |
| **力度/音量** | 力度标记(pp~ff)、动态范围dB、渐强/渐弱事件、每段音量图 | RMS分析 |
| **翻译** | 歌词翻译为12种语言(中/英/日/韩/西/法/德/葡/俄/阿/意/泰) | Google Translate |

---

## 不需要任何 API Key

全部本地运行 + 免费服务：
- **Whisper** — 本地运行，不需要 OpenAI API Key
- **librosa** — 本地音频分析库
- **Google Translate** — 免费翻译接口
- **Gradio** — 本地 Web 界面

> **Suno / Udio 没有公开 API**，本项目生成提示词后，你手动复制粘贴到它们的网页即可。

---

## 安装步骤

### 1. 安装 FFmpeg

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows — 从 https://ffmpeg.org/download.html 下载并添加到 PATH
```

### 2. 安装 Python 依赖

```bash
cd music
pip install -r requirements.txt
```

### 3. 启动

```bash
python app.py
```

浏览器打开 **http://localhost:7860**

> 首次运行自动下载 Whisper 模型 (~140MB)，需要网络。

---

## 使用方法

### Web 界面操作（推荐）

1. **上传音乐**：支持 MP3, WAV, FLAC, OGG, M4A 等
2. **选择歌曲语言**：默认自动检测，中文歌可手动选 Chinese
3. **选择翻译目标语言**：如 English, Japanese 等
4. **点击 "Start Full Analysis / 开始完整分析"**
5. **等待 1-3 分钟**（取决于歌曲长度和硬件）
6. **查看各标签页**：

| 标签页 | 内容 |
|--------|------|
| **Overview** | BPM、调性、拍号、情绪、乐器等总览 |
| **Lyrics** | 完整歌词 + 每句时间戳 |
| **Melody** | 逐音符分析：音名、长短、力度、音程序列、旋律简谱 |
| **Structure** | 曲式结构图：每段的起止时间 |
| **Vocal Style** | 颤音分析、声区分布、音色特征、连断音比例 |
| **Emotion** | 整体情绪 + 10秒分段情绪时间线 + 情感弧线 |
| **Dynamics** | 力度标记时间线 + 每段音量图 + 渐强渐弱事件 |
| **Instruments** | 检测到的乐器列表 |
| **Suno Prompt** | **可直接复制到 Suno 的提示词** |
| **Full Prompt** | **包含所有分析细节的完整还原提示词** |
| **Translated** | **外语版完整提示词（用于制作翻唱）** |
| **Translation** | 翻译后的歌词全文 |

7. **点击复制按钮** → 粘贴到 Suno/Udio 的创作页面 → 生成音乐

### Python 代码调用

```python
import sys
sys.path.insert(0, '.')
from pipeline import analyze

result = analyze(
    audio_path="song.mp3",
    source_language="zh",
    target_language="en",
)

# 歌词
print(result.lyrics.full_text)

# BPM / 调性
print(f"BPM: {result.rhythm.bpm}, Key: {result.key.key}")

# 逐音符旋律
for note in result.melody.note_events[:10]:
    print(f"{note.start_time:.2f}s {note.note_name} dur={note.duration:.3f}s ({note.duration_type})")

# 演唱风格
print(result.vocal_style.full_description)

# 情感
print(result.emotion.full_description)

# 力度
print(result.dynamics.description)

# 复制这个到 Suno
print(result.prompts.suno_prompt)

# 外语版提示词
print(result.prompts.translated_prompt)
```

---

## 实战示例

### 示例：中文歌 → 英文翻唱版

```
1. 上传中文歌 MP3
2. 语言选 "Chinese"，目标语言选 "English"
3. 点击分析，等待完成
4. 切换到 "Translated / 外语版提示词" 标签页
5. 点击复制按钮
6. 打开 suno.com，粘贴整段提示词
7. Suno 生成英文版，保持原曲的 BPM、调性、结构、情感
```

---

## 输出示例

### Suno 提示词示例

```
[Genre: Pop Ballad]
[BPM: 78]
[Key: G major]
[Time Signature: 4/4]
[Mood: sad / melancholic]
[Feel: slow / ballad]
[Energy: low energy / calm]
[Instruments: Vocals, Piano / Keys, Strings]
[Vocal Range: D3 - G5]
[Language: Chinese]
[Vocal Style: vibrato-rich, warm, legato, chest-voice-dominant]
[Dynamics: Moderate loudness (typical pop/rock)]

[Intro] (0.0s - 15.2s)
(instrumental)

[Verse 1] (15.2s - 45.8s)
...lyrics here...

[Chorus] (45.8s - 78.3s)
...lyrics here...
```

### 完整提示词包含的详细信息

```
=== COMPLETE MUSIC REPRODUCTION PROMPT ===

## Basic Musical Parameters
- BPM: 78
- Key: G major
- Time Signature: 4/4
- Genre: Pop Ballad

## Mood & Emotion
- Overall Mood: sad / melancholic
- Emotional Arc: progressively brighter; energy builds to climax in the middle

## Vocal Style & Technique
- Vibrato: Strong vibrato (5.8 Hz, ~45 cents), present in 62% of vocal
- Register: Mixed voice: 58% chest, 42% head voice
- Tone Quality: warm/dark timbre, slightly breathy
- Articulation: Predominantly legato (78%). Smooth, connected phrasing.

## Dynamics & Volume
- Dynamic Range: 24.5 dB
- Volume Map:
  [00:00-00:15] mp (mezzo-piano)    steady    |====|
  [00:15-00:45] mf (mezzo-forte)    crescendo |========|
  [00:45-01:18] f (forte)           steady    |============|
  ...

## Melody (first 50 notes)
C4- D4. E4 E4 G4--- A4! G4- E4 D4. C4- ...
```

---

## 项目结构

```
music/
├── app.py                      # Gradio Web UI 入口
├── pipeline.py                 # 分析流水线（串联全部 12 个分析步骤）
├── config.py                   # 全局配置
├── requirements.txt            # 依赖
│
├── analyzers/                  # 分析模块 (9 个分析器)
│   ├── lyrics.py               # 歌词识别 (Whisper)
│   ├── melody.py               # 旋律：逐音符音高 + 长短音 + 音程
│   ├── rhythm.py               # 节奏：BPM + 拍号 + 风格
│   ├── key_detector.py         # 调性检测
│   ├── structure.py            # 曲式结构切分
│   ├── instruments.py          # 乐器检测
│   ├── vocal_style.py          # 演唱风格：颤音/声区/音色/连断音
│   ├── emotion.py              # 情感语气：效价-唤醒模型 + 情感弧线
│   └── dynamics.py             # 力度音量：强弱标记 + 渐强渐弱 + 音量图
│
├── translation/
│   └── translator.py           # 多语言翻译 (12种语言)
│
├── prompt_generator/
│   ├── generator.py            # 将全部分析结果组装为提示词
│   └── templates.py            # Suno / Udio / 通用提示词模板
│
├── utils/
│   └── audio_io.py             # 音频加载与格式转换
│
├── tests/
└── samples/                    # 示例音频 (gitignored)
```

### 数据流向

```
音乐文件
  |
  v
audio_io.py (加载 + 转WAV)
  |
  +---> lyrics.py --------- 歌词 + 时间戳
  +---> rhythm.py --------- BPM + 拍号
  +---> key_detector.py ---- 调性
  +---> melody.py ---------- 逐音符(音名+时长+力度+音程)
  +---> structure.py ------- 曲式结构
  +---> instruments.py ----- 乐器
  +---> vocal_style.py ----- 颤音+声区+音色+连断音
  +---> emotion.py --------- 情绪+语气+情感弧线
  +---> dynamics.py -------- 力度+音量图+渐强渐弱
  |
  v
pipeline.py (汇总全部结果)
  |
  +---> translator.py ------ 翻译歌词
  |
  v
generator.py (组装完整提示词)
  |
  v
Gradio UI (展示 + 复制按钮)
  |
  v
用户复制 → 粘贴到 Suno/Udio → 生成还原版/外语版音乐
```

---

## 配置

编辑 `config.py`：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `WHISPER_MODEL_SIZE` | `"base"` | Whisper 模型: tiny/base/small/medium/large |

| 模型 | 大小 | 速度 | 准确率 | 推荐场景 |
|------|------|------|--------|---------|
| tiny | 39MB | 最快 | 一般 | 快速测试 |
| **base** | **74MB** | **快** | **良好** | **CPU 默认推荐** |
| small | 244MB | 中等 | 较好 | 有较好 CPU |
| medium | 769MB | 较慢 | 很好 | **有 GPU 推荐** |
| large | 1.5GB | 最慢 | 最好 | 高端 GPU |

---

## 常见问题

**Q: 能 100% 还原原曲吗？**
分析端能捕捉到音乐的所有主要特征（BPM、调性、旋律、结构、情感、演唱风格等）。但 AI 音乐生成工具（Suno/Udio）本身有随机性，所以生成结果是"高度近似"而非"完全相同"。提示词越详细，还原度越高。

**Q: 需要 GPU 吗？**
不需要，CPU 可运行。有 NVIDIA GPU + CUDA 会快很多。

**Q: 支持什么格式？**
MP3, WAV, FLAC, OGG, M4A, WMA, AAC。

**Q: 歌词不准怎么办？**
1. 用更大的 Whisper 模型 (medium/large)
2. 手动指定歌曲语言而不是自动检测

**Q: 翻译歌词能直接唱吗？**
机器翻译是直译。要可唱的歌词建议用 ChatGPT/Claude 在翻译基础上做意译调整。

---

## License

MIT - 仅供学习使用
