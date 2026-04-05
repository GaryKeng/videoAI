# VideoAI Auto-Editing Tool

An AI-powered video editing tool for Mac that automatically processes oral video content.

## Features

- **AI Speech Recognition**: Using OpenAI's Whisper for accurate transcription
- **Voice Activity Detection**: Using Silero VAD to detect speech segments
- **Error Detection**: Automatically detects pauses, repetitions, and filler words
- **Material Matching**: OCR-based matching of subtitle text with material images
- **Image Overlay**: Automatically overlay matched images on video timeline
- **Self-Learning**: Learns from user adjustments to improve future matches
- **FFmpeg Export**: High-quality video export

## Quick Start (一键安装)

```bash
# 方法 1: Git 克隆
git clone https://github.com/GaryKeng/videoAI.git
cd videoAI
./install.sh

# 方法 2: 直接下载
# 访问 https://github.com/GaryKeng/videoAI
# 点击 Code → Download ZIP
# 解压后运行 install.sh
```

## System Requirements

| 要求 | 说明 |
|------|------|
| macOS | 10.14+ (Mojave 或更高) |
| Python | 3.9+ |
| FFmpeg | 自动检测并提示安装 |

## Installation (手动)

1. Clone or download the project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure FFmpeg is installed:
   ```bash
   brew install ffmpeg
   ```

## Usage

1. Place your material images (PNG/JPG) in `~/Desktop/Materials/`

2. Run the application:
   ```bash
   python3 src/main.py
   ```

3. Click **New Project** to create a project

4. Click **Open Video** to load your oral video

5. Click **Analyze** to run AI analysis

6. Click **Auto Edit** to automatically match materials and build timeline

7. Manually adjust as needed

8. Click **Export** to save the final video

## First Run Setup

首次运行会自动下载 AI 模型：
- **Whisper large-v3**: ~800MB (语音识别)
- **EasyOCR models**: ~100MB (OCR 文字识别)
- **Silero VAD**: ~9MB (语音活动检测)

这些模型只需下载一次，后续使用无需联网。

## Project Structure

```
VideoAI/
├── install.sh               # 一键安装脚本
├── requirements.txt         # Python 依赖
├── README.md               # 说明文档
├── src/
│   ├── main.py             # 程序入口
│   ├── config.py           # 全局配置
│   ├── core/              # AI 核心模块
│   │   ├── speech_recognizer.py  # Whisper 语音识别
│   │   ├── vad_detector.py       # Silero VAD
│   │   ├── error_detector.py     # 错误检测
│   │   ├── ocr_matcher.py        # OCR 匹配
│   │   └── video_analyzer.py     # 视频分析
│   ├── material/           # 素材管理
│   ├── timeline/           # 时间线与导出
│   ├── learning/           # 自我进化
│   ├── database/           # 数据库
│   └── ui/                 # PyQt6 界面
└── tests/                  # 单元测试
```

## Configuration

编辑 `src/config.py` 调整参数：
- Whisper 模型大小 (tiny/base/small/medium/large-v3)
- VAD 阈值
- 错误检测灵敏度
- 匹配重合度阈值 (默认 50%)
- 输出视频质量

## License

MIT License
