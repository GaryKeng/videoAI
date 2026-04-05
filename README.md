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

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.9+
- FFmpeg

## Installation

1. Clone or download the project
2. Install dependencies:
   ```bash
   cd VideoAI
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
   python src/main.py
   ```

3. Click "New Project" to create a project

4. Click "Open Video" to load your oral video

5. Click "Analyze" to run AI analysis

6. Click "Auto Edit" to automatically match materials and build timeline

7. Manually adjust as needed

8. Click "Export" to save the final video

## Project Structure

```
VideoAI/
├── src/
│   ├── config.py              # Configuration
│   ├── main.py               # Entry point
│   ├── core/                 # Core AI modules
│   │   ├── speech_recognizer.py
│   │   ├── vad_detector.py
│   │   ├── error_detector.py
│   │   ├── ocr_matcher.py
│   │   └── video_analyzer.py
│   ├── material/             # Material management
│   ├── timeline/             # Timeline and export
│   ├── learning/             # Self-learning engine
│   ├── database/             # Data models
│   └── ui/                   # PyQt6 UI
├── data/                     # Project data
├── tests/                    # Tests
└── requirements.txt
```

## Configuration

Edit `src/config.py` to adjust:
- Whisper model size
- VAD thresholds
- Error detection settings
- Match thresholds
- Output settings

## License

MIT License
