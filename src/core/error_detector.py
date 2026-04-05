"""
Error detection module for pause, repetition, and filler word detection.
"""
import re
from typing import List, Tuple
from dataclasses import dataclass

from src.core.speech_recognizer import SubtitleSegment
from src.core.vad_detector import SpeechSegment
from src.config import REPETITION_THRESHOLD, FILLER_WORDS, FILLER_WORD_MIN_COUNT


@dataclass
class ErrorMarker:
    """Error marker for a subtitle segment."""
    segment: SubtitleSegment
    error_type: str  # "pause", "repetition", "filler"
    confidence: float  # 0.0 to 1.0
    description: str


class ErrorDetector:
    """Detect errors in subtitle segments."""

    def __init__(
        self,
        repetition_threshold: float = REPETITION_THRESHOLD,
        filler_words: dict = None
    ):
        self.repetition_threshold = repetition_threshold
        self.filler_words = filler_words or FILLER_WORDS

    def detect_pause_errors(
        self,
        subtitle_segments: List[SubtitleSegment],
        vad_segments: List[SpeechSegment] = None
    ) -> List[ErrorMarker]:
        """
        Detect pause errors based on VAD segments.

        Args:
            subtitle_segments: List of subtitle segments
            vad_segments: List of VAD speech segments

        Returns:
            List of ErrorMarker for pause errors
        """
        if vad_segments is None or len(vad_segments) < 2:
            return []

        markers = []

        # Find long pauses between VAD segments
        for i in range(len(vad_segments) - 1):
            current_end = vad_segments[i].end
            next_start = vad_segments[i + 1].start
            pause_duration = next_start - current_end

            # If pause is > 0.8s, mark any subtitle in that range
            if pause_duration > 0.8:
                for seg in subtitle_segments:
                    if seg.start >= current_end and seg.end <= next_start:
                        markers.append(ErrorMarker(
                            segment=seg,
                            error_type="pause",
                            confidence=min(pause_duration / 2.0, 1.0),
                            description=f"Long pause ({pause_duration:.1f}s)"
                        ))

        return markers

    def detect_repetition_errors(self, subtitle_segments: List[SubtitleSegment]) -> List[ErrorMarker]:
        """
        Detect repetition errors in subtitle segments.

        Args:
            subtitle_segments: List of subtitle segments

        Returns:
            List of ErrorMarker for repetition errors
        """
        markers = []

        for i in range(len(subtitle_segments) - 1):
            current_text = self._normalize_text(subtitle_segments[i].text)
            next_text = self._normalize_text(subtitle_segments[i + 1].text)

            if not current_text or not next_text:
                continue

            similarity = self._calculate_similarity(current_text, next_text)

            if similarity >= self.repetition_threshold:
                markers.append(ErrorMarker(
                    segment=subtitle_segments[i + 1],
                    error_type="repetition",
                    confidence=similarity,
                    description=f"Repetition of previous segment (similarity: {similarity:.2f})"
                ))

        return markers

    def detect_filler_errors(self, subtitle_segments: List[SubtitleSegment]) -> List[ErrorMarker]:
        """
        Detect filler word errors (嗯、啊、this、that, etc).

        Args:
            subtitle_segments: List of subtitle segments

        Returns:
            List of ErrorMarker for filler errors
        """
        markers = []
        all_filler = set(self.filler_words.get("zh", []) + self.filler_words.get("en", []))

        for seg in subtitle_segments:
            text = seg.text
            filler_count = 0
            matched_fillers = []

            for filler in all_filler:
                count = text.count(filler)
                if count > 0:
                    filler_count += count
                    matched_fillers.append(filler * count)

            if filler_count >= FILLER_WORD_MIN_COUNT:
                markers.append(ErrorMarker(
                    segment=seg,
                    error_type="filler",
                    confidence=min(filler_count / 5.0, 1.0),
                    description=f"Filler words: {', '.join(matched_fillers)}"
                ))

        return markers

    def detect_all_errors(
        self,
        subtitle_segments: List[SubtitleSegment],
        vad_segments: List[SpeechSegment] = None
    ) -> List[ErrorMarker]:
        """
        Detect all types of errors.

        Args:
            subtitle_segments: List of subtitle segments
            vad_segments: List of VAD speech segments

        Returns:
            List of all ErrorMarkers
        """
        pause_errors = self.detect_pause_errors(subtitle_segments, vad_segments)
        repetition_errors = self.detect_repetition_errors(subtitle_segments)
        filler_errors = self.detect_filler_errors(subtitle_segments)

        return pause_errors + repetition_errors + filler_errors

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Remove punctuation and spaces
        text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
        return text.lower()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using Jaccard index.
        """
        if not text1 or not text2:
            return 0.0

        set1 = set(text1)
        set2 = set(text2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union
