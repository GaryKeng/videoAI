"""
Video analyzer - coordinates speech recognition, VAD, and error detection.
"""
import logging
from pathlib import Path
from typing import Union, List, Dict, Optional, Tuple
import whisper

from src.core.speech_recognizer import SpeechRecognizer, SubtitleSegment
from src.core.vad_detector import VADDetector, SpeechSegment
from src.core.error_detector import ErrorDetector, ErrorMarker
from src.config import WHISPER_MODEL, WHISPER_LANGUAGE

logger = logging.getLogger(__name__)


class VideoAnalyzer:
    """Coordinate video analysis pipeline."""

    def __init__(
        self,
        whisper_model: str = WHISPER_MODEL,
        whisper_language: str = WHISPER_LANGUAGE
    ):
        self.whisper_model = whisper_model
        self.whisper_language = whisper_language

        self.speech_recognizer = SpeechRecognizer(
            model_name=whisper_model,
            language=whisper_language
        )
        self.vad_detector = VADDetector()
        self.error_detector = ErrorDetector()

        self.subtitle_segments: List[SubtitleSegment] = []
        self.vad_segments: List[SpeechSegment] = []
        self.error_markers: List[ErrorMarker] = []

    def analyze_video(self, video_path: Union[str, Path]) -> Dict:
        """
        Analyze video file - recognize speech, detect VAD, and detect errors.

        Args:
            video_path: Path to video file

        Returns:
            Dict containing:
                - subtitle_segments: List of SubtitleSegment
                - vad_segments: List of SpeechSegment
                - error_markers: List of ErrorMarker
                - video_duration: Total video duration

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If analysis fails
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Analyzing video: {video_path}")

        try:
            # Step 1: Speech Recognition
            logger.info("Step 1: Speech recognition...")
            self.subtitle_segments = self.speech_recognizer.recognize_from_video(str(video_path))

            # Step 2: VAD Detection (requires audio extraction)
            logger.info("Step 2: VAD detection...")
            from src.core.speech_recognizer import extract_audio_from_video
            audio_path = extract_audio_from_video(video_path)
            self.vad_segments = self.vad_detector.get_speech_timestamps(str(audio_path))

            # Step 3: Error Detection
            logger.info("Step 3: Error detection...")
            self.error_markers = self.error_detector.detect_all_errors(
                self.subtitle_segments,
                self.vad_segments
            )

            # Get video duration
            video_duration = self._get_video_duration(video_path)

            results = {
                "subtitle_segments": self.subtitle_segments,
                "vad_segments": self.vad_segments,
                "error_markers": self.error_markers,
                "video_duration": video_duration
            }

            logger.info(f"Analysis complete: {len(self.subtitle_segments)} segments, {len(self.error_markers)} errors found")
            return results

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise RuntimeError(f"Video analysis failed: {e}") from e

    def get_segment_with_errors(self) -> List[Dict]:
        """
        Get subtitle segments with error markers.

        Returns:
            List of dicts with segment info and error flags
        """
        result = []

        for seg in self.subtitle_segments:
            seg_dict = {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "is_pause_error": False,
                "is_repetition_error": False,
                "is_filler_error": False
            }

            for marker in self.error_markers:
                if marker.segment == seg:
                    if marker.error_type == "pause":
                        seg_dict["is_pause_error"] = True
                    elif marker.error_type == "repetition":
                        seg_dict["is_repetition_error"] = True
                    elif marker.error_type == "filler":
                        seg_dict["is_filler_error"] = True

            result.append(seg_dict)

        return result

    def get_error_segments(self) -> List[Dict]:
        """
        Get only error segments.

        Returns:
            List of error segment dicts
        """
        errors = []

        for marker in self.error_markers:
            errors.append({
                "start": marker.segment.start,
                "end": marker.segment.end,
                "text": marker.segment.text,
                "error_type": marker.error_type,
                "confidence": marker.confidence,
                "description": marker.description
            })

        return errors

    def get_good_segments(self) -> List[Dict]:
        """
        Get segments without errors.

        Returns:
            List of good segment dicts
        """
        good_segments = []

        for seg in self.subtitle_segments:
            has_error = any(
                marker.segment == seg for marker in self.error_markers
            )
            if not has_error:
                good_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text
                })

        return good_segments

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using FFprobe."""
        import subprocess

        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception:
            return 0.0
