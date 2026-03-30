# MusicLens - 音乐分析与跨语言复刻工具

一个用于音乐分析和跨语言音乐复刻的工具。上传一首歌，自动分析歌词、音调、节奏、曲式结构和乐器，生成可直接用于 AI 音乐生成工具（如 Suno、Udio）的完整提示词。支持将歌词翻译为多种语言，轻松制作外语版本。

> ⚠️ 本项目仅用于学习研究目的。

## 功能特点

- **歌词识别**: 基于 OpenAI Whisper，支持中文、英语、日语等 99 种语言自动识别
- **音调分析**: 提取旋律走向、音域范围、主要音符
- **节奏分析**: BPM 检测、拍号识别、节奏风格判定
- **调性检测**: 自动检测歌曲调性（如 C major, A minor）
- **曲式结构**: 自动识别前奏、主歌、副歌、桥段、尾声
- **乐器检测**: 识别主要乐器类型
- **提示词生成**: 自动生成 Suno/Udio 格式的 AI 音乐生成提示词
- **多语言翻译**: 支持 12 种语言互译，一键生成外语版提示词

## 安装

### 1. 环境要求

- Python 3.10+
- FFmpeg（用于音频格式转换）

### 2. 安装 FFmpeg

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows - 从 https://ffmpeg.org/download.html 下载
```

### 3. 安装 Python 依赖

```bash
cd music
pip install -r requirements.txt
```

> 注意：首次运行时会自动下载 Whisper 模型（约 140MB），请确保网络连接。

## 使用方法

### 方法一：Web 界面（推荐）

```bash
python app.py
```

然后在浏览器打开 `http://localhost:7860`

**操作步骤：**
1. 在页面上传你的音乐文件（支持 MP3, WAV, FLAC, OGG, M4A 等格式）
2. 选择歌曲语言（默认自动检测，如果是中文歌可以选择 Chinese）
3. 选择翻译目标语言（如 English, Japanese 等）
4. 点击 **"开始分析"** 按钮
5. 等待分析完成（大约 1-3 分钟，取决于歌曲长度）
6. 在各个标签页查看分析结果：
   - **基本信息**: BPM、调性、拍号等
   - **歌词**: 完整歌词及时间戳
   - **旋律**: 音域和旋律走向
   - **曲式结构**: 歌曲段落划分
   - **乐器**: 检测到的乐器
   - **Suno 提示词**: 可直接复制到 Suno AI 使用
   - **通用提示词**: 通用格式的提示词
   - **外语版提示词**: 翻译后的提示词，用于制作外语版
   - **翻译歌词**: 翻译后的歌词文本

### 方法二：命令行使用

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

# 查看结果
print("歌词:", result.lyrics.full_text)
print("BPM:", result.rhythm.bpm)
print("调性:", result.key.key)
print("结构:", result.structure.summary)
print("乐器:", result.instruments.detected)

# 获取 Suno 提示词
print(result.prompts.suno_prompt)

# 获取翻译后的提示词
print(result.prompts.translated_prompt)
```

## 使用场景示例

### 场景：将中文歌翻唱为英文版

1. 上传一首中文歌（如 `.mp3` 文件）
2. 歌曲语言选择 "Chinese"，目标语言选择 "English"
3. 点击分析
4. 复制 **"外语版提示词"** 标签页的内容
5. 粘贴到 Suno AI (https://suno.com) 的创作页面
6. Suno 会根据提示词生成英文版本的歌曲

### 场景：分析歌曲用于学习

1. 上传任意歌曲
2. 查看 **基本信息** 了解 BPM、调性等
3. 查看 **曲式结构** 了解歌曲的段落安排
4. 查看 **旋律** 了解音域范围

## 项目结构

```
music/
├── app.py                  # Gradio Web 界面入口
├── pipeline.py             # 分析流水线（核心调度）
├── config.py               # 全局配置
├── requirements.txt        # Python 依赖
│
├── analyzers/              # 各分析模块
│   ├── lyrics.py           # 歌词识别 (Whisper)
│   ├── melody.py           # 旋律分析 (PYIN)
│   ├── rhythm.py           # 节奏分析
│   ├── key_detector.py     # 调性检测
│   ├── structure.py        # 曲式结构检测
│   └── instruments.py      # 乐器检测
│
├── translation/            # 翻译模块
│   └── translator.py       # 多语言翻译
│
├── prompt_generator/       # 提示词生成
│   ├── generator.py        # 提示词组装
│   └── templates.py        # 提示词模板
│
├── utils/                  # 工具函数
│   └── audio_io.py         # 音频加载与转换
│
├── tests/                  # 测试
└── samples/                # 示例音频 (gitignored)
```

## 技术栈

| 功能 | 技术 |
|------|------|
| 歌词识别 | OpenAI Whisper |
| 音频分析 | librosa |
| 旋律提取 | PYIN (librosa) |
| 调性检测 | Krumhansl-Kessler 算法 |
| 翻译 | Google Translate (deep-translator) |
| Web 界面 | Gradio |

## 配置

编辑 `config.py` 可以调整以下设置：

- `WHISPER_MODEL_SIZE`: Whisper 模型大小
  - `"tiny"` - 最快，准确率一般
  - `"base"` - 默认，速度和准确率平衡
  - `"small"` - 更准确，需要更多内存
  - `"medium"` - 高准确率，推荐有 GPU 时使用
  - `"large"` - 最高准确率，需要 GPU

## 已知限制

1. **歌词识别**：背景音乐较重时，歌词识别准确率会下降
2. **曲式结构**：自动识别可能不完全准确，尤其是对于非标准结构的歌曲
3. **乐器检测**：基于频谱分析的启发式方法，仅能识别大类乐器
4. **翻译质量**：机器翻译为直译，不是可唱的歌词翻译
5. **处理时间**：4 分钟歌曲大约需要 1-3 分钟分析（取决于硬件）

## License

MIT - 仅供学习使用
