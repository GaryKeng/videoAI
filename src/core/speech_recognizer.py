"""
Whisper-based speech recognition module.
"""
import logging
import whisper
import numpy as np
from pathlib import Path
from typing import Union, List, Dict, Optional
from dataclasses import dataclass

from src.config import WHISPER_MODEL, WHISPER_LANGUAGE

logger = logging.getLogger(__name__)


@dataclass
class SubtitleSegment:
    """Subtitle segment with timestamp."""
    start: float  # seconds
    end: float  # seconds
    text: str
    words: Optional[List[Dict]] = None


class SpeechRecognizer:
    """Whisper speech recognizer."""

    def __init__(self, model_name: str = WHISPER_MODEL, language: str = WHISPER_LANGUAGE):
        self.model_name = model_name
        self.language = language
        self.model = None

    def load_model(self):
        """Load Whisper model."""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded successfully")

    def recognize(self, audio_path: Union[str, Path]) -> List[SubtitleSegment]:
        """
        Recognize speech from audio file.

        Args:
            audio_path: Path to audio file

        Returns:
            List of SubtitleSegment objects
        """
        if self.model is None:
            self.load_model()

        audio_path = Path(audio_path)
        logger.info(f"Recognizing speech from: {audio_path}")

        # Load audio
        audio = whisper.load_audio(str(audio_path))
        # Note: No truncation - full audio is processed
        # For very long videos (>30min), consider chunking

        # Transcribe with word-level timestamps
        result = self.model.transcribe(
            audio,
            language=self.language,
            word_timestamps=True,
            verbose=False
        )

        segments = []
        for segment in result["segments"]:
            words = None
            if "words" in segment:
                words = [
                    {
                        "word": w["word"],
                        "start": w["start"],
                        "end": w["end"]
                    }
                    for w in segment["words"]
                ]

            segments.append(SubtitleSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"].strip(),
                words=words
            ))

        logger.info(f"Recognition complete. Found {len(segments)} segments")
        return segments

    def recognize_from_video(self, video_path: Union[str, Path]) -> List[SubtitleSegment]:
        """
        Recognize speech directly from video file.
        Extracts audio and transcribes.

        Args:
            video_path: Path to video file

        Returns:
            List of SubtitleSegment objects
        """
        if self.model is None:
            self.load_model()

        video_path = Path(video_path)
        logger.info(f"Recognizing speech from video: {video_path}")

        # Extract audio from video first
        from src.core.speech_recognizer import extract_audio_from_video
        audio_path = extract_audio_from_video(video_path)

        # Load audio
        audio = whisper.load_audio(str(audio_path))
        # Note: Full audio is processed - no truncation

        # Transcribe
        result = self.model.transcribe(
            audio,
            language=self.language,
            word_timestamps=True,
            verbose=False
        )

        segments = []
        for segment in result["segments"]:
            words = None
            if "words" in segment:
                words = [
                    {
                        "word": w["word"],
                        "start": w["start"],
                        "end": w["end"]
                    }
                    for w in segment["words"]
                ]

            segments.append(SubtitleSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment["text"].strip(),
                words=words
            ))

        logger.info(f"Recognition complete. Found {len(segments)} segments")
        return segments


def extract_audio_from_video(video_path: Union[str, Path], output_path: Union[str, Path] = None) -> Path:
    """
    Extract audio from video using FFmpeg.

    Args:
        video_path: Path to video file
        output_path: Path to output audio file (optional)

    Returns:
        Path to extracted audio file
    """
    import subprocess

    video_path = Path(video_path)
    if output_path is None:
        output_path = video_path.with_suffix(".wav")

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        str(output_path)
    ]

    subprocess.run(cmd, capture_output=True)
    return output_path
