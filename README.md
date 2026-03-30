# MusicLens - 音乐分析与跨语言复刻工具

一个用于音乐分析和跨语言音乐复刻的工具。上传一首歌，自动分析歌词、音调、节奏、曲式结构和乐器，生成可直接用于 AI 音乐生成工具（如 Suno、Udio）的完整提示词。支持将歌词翻译为多种语言，轻松制作外语版本。

> 本项目仅用于学习研究目的（课程作业）。

---

## 核心思路 / 工作原理

```
                         MusicLens 工作流程

  +-----------+     +------------------+     +----------------+     +------------------+
  |           |     |                  |     |                |     |                  |
  |  上传音乐  | --> |  自动分析全部信息  | --> |  生成完整提示词  | --> | 复制到Suno/Udio  |
  |  (MP3等)  |     |  歌词/音调/节奏等  |     |  (含翻译版本)   |     |  生成外语版音乐   |
  |           |     |                  |     |                |     |                  |
  +-----------+     +------------------+     +----------------+     +------------------+
```

**简单来说**：把音乐放进去 → 程序自动分析出所有音乐要素 → 输出一段"提示词" → 把提示词粘贴到 Suno/Udio → 就能复刻或生成外语版。

---

## 功能一览

| 功能 | 说明 | 使用的技术 |
|------|------|-----------|
| 歌词识别 | 支持中/英/日/韩等 99 种语言自动识别，输出带时间戳的完整歌词 | OpenAI Whisper (本地运行) |
| 音调/旋律分析 | 提取旋律走向、音域范围（最低音到最高音）、主要音符 | librosa PYIN 算法 |
| 节奏分析 | BPM（每分钟拍数）、拍号（4/4 or 3/4）、节奏风格（快/慢/中等） | librosa beat tracking |
| 调性检测 | 自动检测歌曲调性，如 C major（C大调）、A minor（A小调） | Krumhansl-Kessler 算法 |
| 曲式结构 | 自动切分前奏 Intro → 主歌 Verse → 副歌 Chorus → 桥段 Bridge → 尾声 Outro | 自相似矩阵 + 聚类 |
| 乐器检测 | 识别主要乐器：人声、吉他、钢琴、鼓、贝斯、合成器、弦乐等 | 频谱分析启发式方法 |
| 多语言翻译 | 支持 12 种语言互译（中/英/日/韩/西/法/德/葡/俄/阿/意/泰） | Google Translate (免费) |
| 提示词生成 | 自动生成 Suno 格式、Udio 格式、通用格式的 AI 音乐生成提示词 | 模板引擎 |

---

## 不需要任何 API Key

本项目 **全部使用本地开源工具 + 免费服务**，不需要付费 API：

- 歌词识别：**Whisper** — OpenAI 开源模型，本地运行，不需要 API Key
- 音频分析：**librosa** — Python 音频分析库，本地运行
- 翻译：**Google Translate** — 通过 `deep-translator` 库调用免费接口
- Web 界面：**Gradio** — 本地启动的网页界面

> **关于 Suno / Udio / Lyria API**：
> - Suno 和 Udio **没有官方公开 API**，只能通过网页手动使用
> - Google Lyria (`lyria-3-pro-preview`) 有 API 但处于预览阶段
> - 所以本项目的方案是：**生成提示词 → 你手动复制粘贴到 Suno/Udio 网页** 即可
> - 这是目前最稳定可行的方案

---

## 安装步骤

### 第一步：安装 FFmpeg（音频格式转换必需）

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows - 从 https://ffmpeg.org/download.html 下载并添加到 PATH
```

### 第二步：安装 Python 依赖

```bash
cd music
pip install -r requirements.txt
```

**依赖列表（requirements.txt）**：
```
librosa>=0.10.1          # 音频分析核心库
openai-whisper>=20231117 # 歌词识别
gradio>=4.0              # Web 界面
numpy                    # 数值计算
scipy                    # 科学计算
soundfile                # 音频文件读写
torch                    # PyTorch (Whisper 依赖)
torchaudio               # 音频处理
pydub                    # 音频格式转换
matplotlib               # 可视化
deep-translator          # 多语言翻译
```

> 首次运行时会自动下载 Whisper 模型（约 140MB），请确保网络连接正常。

### 第三步：启动

```bash
python app.py
```

浏览器打开 **http://localhost:7860** 即可使用。

---

## 使用方法

### 方法一：Web 界面（推荐，最简单）

```bash
python app.py
# 浏览器打开 http://localhost:7860
```

**操作步骤**：

1. **上传音乐**：在页面上传你的音乐文件（支持 MP3, WAV, FLAC, OGG, M4A 等）
2. **选择语言**：歌曲语言选择对应语言（如 Chinese），默认自动检测
3. **选择翻译目标语言**：比如要做英文版就选 English，日文版选 Japanese
4. **点击 "开始分析"**：等待 1-3 分钟
5. **查看结果**：在各个标签页查看：

| 标签页 | 内容 |
|--------|------|
| 基本信息 | BPM、调性、拍号、节奏风格、能量等级 |
| 歌词 | 完整歌词 + 每句的起止时间戳 |
| 旋律 | 音域范围、主要音符、旋律走向描述 |
| 曲式结构 | 歌曲段落划分（前奏→主歌→副歌→...） |
| 乐器 | 检测到的乐器列表 |
| **Suno 提示词** | **可直接复制到 Suno 使用的完整提示词** |
| **通用提示词** | 通用格式提示词（适用于任何 AI 音乐工具） |
| **外语版提示词** | **翻译后的提示词，用于生成外语版音乐** |
| 翻译歌词 | 翻译后的歌词全文 |

6. **复制提示词**：点击输出框右上角的复制按钮
7. **粘贴到 Suno/Udio**：在 Suno 或 Udio 的创作页面粘贴，即可生成音乐

### 方法二：Python 代码调用

```python
import sys
sys.path.insert(0, '.')
from pipeline import analyze

# 分析一首中文歌并翻译为英文
result = analyze(
    audio_path="你的歌曲.mp3",
    source_language="zh",    # 可选，None 为自动检测
    target_language="en",    # 翻译目标语言
)

# 查看分析结果
print("歌词:", result.lyrics.full_text)
print("BPM:", result.rhythm.bpm)
print("调性:", result.key.key)
print("结构:", result.structure.summary)
print("乐器:", result.instruments.detected)

# 获取 Suno 提示词（可直接复制使用）
print(result.prompts.suno_prompt)

# 获取外语版提示词
print(result.prompts.translated_prompt)
```

---

## 实战示例

### 示例 1：将中文歌翻唱为英文版

```
1. 上传一首中文歌（如 周杰伦的歌.mp3）
2. 歌曲语言选 "Chinese"
3. 目标语言选 "English"
4. 点击 "开始分析"
5. 分析完成后，切换到 "外语版提示词" 标签页
6. 点击复制按钮，复制全部提示词
7. 打开 Suno (suno.com)，在创作页面粘贴提示词
8. Suno 会生成一首英文版本的歌曲，旋律和节奏与原曲相似
```

### 示例 2：将中文歌翻唱为日文版

```
1. 上传中文歌
2. 歌曲语言选 "Chinese"
3. 目标语言选 "Japanese"
4. 点击分析 → 复制日文版提示词 → 粘贴到 Suno
```

### 示例 3：纯分析（学习歌曲结构）

```
1. 上传任意歌曲
2. 不需要选翻译语言
3. 点击分析
4. 查看各标签页了解：
   - 这首歌的 BPM 是多少
   - 是什么调（大调/小调）
   - 曲式结构怎么安排的（前奏几秒→主歌几秒→副歌几秒）
   - 用了哪些乐器
   - 旋律的音域范围
```

---

## 输出提示词示例

分析完成后，程序会输出类似这样的提示词（以 Suno 格式为例）：

```
[Genre: Pop]
[BPM: 120]
[Key: G major]
[Time Signature: 4/4]
[Mood/Feel: moderate / groovy]
[Energy: medium energy]
[Instruments: Vocals, Piano / Keys, Drums / Percussion, Bass]
[Vocal Range: E3 - G5]
[Language: English]

[Intro]
(instrumental intro)

[Verse 1]
Walking down the street at night
The city lights are shining bright
...

[Chorus]
This is where I want to be
Dancing wild and running free
...

[Verse 2]
...

[Chorus]
...

[Outro]
...
```

**直接复制这段文字到 Suno/Udio 的创作框**，就能生成对应的音乐。

---

## 项目结构

```
music/
├── app.py                  # Gradio Web 界面入口（启动这个文件）
├── pipeline.py             # 分析流水线（核心调度，串联所有分析器）
├── config.py               # 全局配置（Whisper 模型大小、语言列表等）
├── requirements.txt        # Python 依赖列表
├── README.md               # 本文件
│
├── analyzers/              # 分析模块（每个文件负责一项分析）
│   ├── lyrics.py           # 歌词识别 — 使用 Whisper 模型
│   ├── melody.py           # 旋律分析 — 使用 PYIN 算法提取音高
│   ├── rhythm.py           # 节奏分析 — BPM、拍号、节奏风格
│   ├── key_detector.py     # 调性检测 — Krumhansl-Kessler 算法
│   ├── structure.py        # 曲式结构 — 自相似矩阵 + 聚类分割
│   └── instruments.py      # 乐器检测 — 频谱特征分析
│
├── translation/            # 翻译模块
│   └── translator.py       # 调用 Google Translate 翻译歌词
│
├── prompt_generator/       # 提示词生成模块
│   ├── generator.py        # 将分析结果组装成完整提示词
│   └── templates.py        # Suno/Udio/通用 提示词模板
│
├── utils/                  # 工具函数
│   └── audio_io.py         # 音频文件加载、格式转换
│
├── tests/                  # 测试目录
└── samples/                # 示例音频存放目录 (不上传到 git)
```

### 数据流向图

```
音乐文件 (MP3/WAV/...)
    |
    v
audio_io.py — 加载音频，统一转为 WAV 格式
    |
    |---> lyrics.py -------- Whisper 识别歌词 + 时间戳
    |---> melody.py -------- PYIN 提取旋律音高、音域
    |---> rhythm.py -------- 检测 BPM、拍号、节奏风格
    |---> key_detector.py --- 检测调性 (C大调/A小调等)
    |---> structure.py ------ 切分曲式结构 (主歌/副歌等)
    |---> instruments.py ---- 识别乐器种类
    |
    v
pipeline.py — 汇总所有分析结果
    |
    |---> translator.py ---- 翻译歌词 (如果选择了目标语言)
    |
    v
generator.py — 根据模板生成完整提示词
    |
    v
app.py (Gradio 界面) — 展示结果，提供复制按钮
    |
    v
用户复制提示词 → 粘贴到 Suno/Udio → 生成音乐
```

---

## 配置说明

编辑 `config.py` 可以调整设置：

### Whisper 模型大小

| 模型 | 大小 | 速度 | 准确率 | 推荐场景 |
|------|------|------|--------|---------|
| `"tiny"` | 39MB | 最快 | 一般 | 快速测试 |
| `"base"` | 74MB | 快 | 良好 | **默认推荐（CPU）** |
| `"small"` | 244MB | 中等 | 较好 | 有较好 CPU 时 |
| `"medium"` | 769MB | 较慢 | 很好 | **有 GPU 时推荐** |
| `"large"` | 1.5GB | 最慢 | 最好 | 有高端 GPU 时 |

修改方法：打开 `config.py`，修改 `WHISPER_MODEL_SIZE = "base"` 为你想要的值。

### 支持的音频格式

MP3, WAV, FLAC, OGG, M4A, WMA, AAC

### 支持的翻译语言

中文、英语、日语、韩语、西班牙语、法语、德语、葡萄牙语、俄语、阿拉伯语、意大利语、泰语

---

## 常见问题

### Q: 分析需要多长时间？
一首 4 分钟的歌大约需要 1-3 分钟，主要取决于 Whisper 模型大小和你的硬件（有 GPU 会快很多）。

### Q: 为什么歌词识别不准？
背景音乐太重会影响识别。可以尝试：
- 使用更大的 Whisper 模型（如 `"medium"` 或 `"large"`）
- 手动指定歌曲语言而不是用自动检测

### Q: 生成的提示词能 100% 复刻原曲吗？
不能 100% 一样，但能保留原曲的主要特征（BPM、调性、结构、风格）。AI 音乐生成工具本身有随机性。

### Q: 翻译的歌词能直接唱吗？
机器翻译是直译，不保证押韵和节奏匹配。如果需要可唱的歌词，建议在翻译结果基础上手动调整，或使用 ChatGPT/Claude 等大模型做意译。

### Q: 需要 GPU 吗？
不需要，CPU 就能运行。但有 GPU 的话 Whisper 会快很多，建议用 NVIDIA 显卡 + CUDA。

### Q: 支持哪些 AI 音乐生成工具？
目前生成的提示词适用于：
- **Suno** (suno.com) — 最推荐，支持歌词 + 风格描述
- **Udio** (udio.com) — 也支持类似格式
- 其他支持文本描述的 AI 音乐工具均可使用通用提示词

---

## 已知限制

1. **歌词识别**：背景音乐较重时准确率下降（Whisper 的固有限制）
2. **曲式结构**：自动识别是近似的，非标准结构歌曲可能不准
3. **乐器检测**：基于频谱启发式方法，只能识别大类（如"吉他"而非"Fender Stratocaster"）
4. **翻译质量**：机器直译，不是音乐性的意译
5. **处理时间**：无 GPU 时较慢，4 分钟歌曲约需 1-3 分钟

---

## License

MIT - 仅供学习使用
