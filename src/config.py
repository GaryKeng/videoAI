"""
Global configuration for VideoAI auto-editing tool.
"""
import os
from pathlib import Path

# Project paths
HOME = Path.home()
DESKTOP = HOME / "Desktop"
VIDEOAI_HOME = HOME / "VideoAI"
MATERIALS_FOLDER = DESKTOP / "Materials"

# Data directories
DATA_DIR = VIDEOAI_HOME / "data"
PROJECTS_DIR = DATA_DIR / "projects"
MATERIALS_DIR = DATA_DIR / "materials"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = VIDEOAI_HOME / "logs"

# Ensure directories exist
for dir_path in [VIDEOAI_HOME, PROJECTS_DIR, MATERIALS_DIR, EXPORTS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Whisper configuration
WHISPER_MODEL = "large-v3"  # tiny/base/small/medium/large-v3
WHISPER_LANGUAGE = "zh"  # Chinese, or None for auto-detection

# VAD configuration (Silero VAD)
VAD_THRESHOLD = 0.5
VAD_MIN_SPEECH_DURATION = 0.3  # seconds
VAD_MINSilence_duration = 0.5  # seconds
VAD_MAX_PAUSE_DURATION = 0.8  # seconds - pauses longer than this are marked as errors

# Error detection configuration
REPETITION_THRESHOLD = 0.7  # similarity threshold for repetition detection
FILLER_WORDS = {
    "zh": ["嗯", "啊", "这个", "那个", "就是说", "其实", "反正", "大概", "可能"],
    "en": ["um", "uh", "like", "you know", "basically", "actually", "literally"]
}
FILLER_WORD_MIN_COUNT = 2  # minimum consecutive filler words to mark as error
FILLER_WORD_RATE_THRESHOLD = 3  # max filler words per 10 seconds

# OCR matching configuration
MATCH_OVERLAP_THRESHOLD = 0.5  # 50% Jaccard similarity threshold

# Image overlay configuration
IMAGE_OVERLAY_MAX_WIDTH_RATIO = 0.4  # max 40% of video width
IMAGE_OVERLAY_FADE_DURATION = 0.3  # seconds
IMAGE_OVERLAY_POSITION = "center-top"  # center-top, center, center-bottom

# Learning configuration
LEARNING_SIMILARITY_TOP_K = 5
LEARNING_WEIGHT_HIGH = 3
LEARNING_MIN_FREQUENCY = 2  # minimum frequency to apply learning bias

# Video export configuration
OUTPUT_VIDEO_CODEC = "libx264"
OUTPUT_VIDEO_PRESET = "medium"
OUTPUT_AUDIO_CODEC = "aac"

# Database
DB_PATH = VIDEOAI_HOME / "data" / "videoai.db"
CHROMA_DB_PATH = VIDEOAI_HOME / "data" / "chroma_db"
