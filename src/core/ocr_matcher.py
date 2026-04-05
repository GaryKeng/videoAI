"""
OCR-based image matching module.
Matches subtitle text with image OCR results.
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from src.config import MATCH_OVERLAP_THRESHOLD


@dataclass
class ImageMatch:
    """Match result between subtitle and image."""
    subtitle_text: str
    subtitle_start: float
    subtitle_end: float
    image_path: str
    ocr_text: str
    overlap_score: float
    matched_words: List[str]


class OCRMatcher:
    """Match subtitle text with image OCR results using Jaccard similarity."""

    def __init__(self, overlap_threshold: float = MATCH_OVERLAP_THRESHOLD):
        self.overlap_threshold = overlap_threshold

    def match(
        self,
        subtitle_segments: List[Dict],
        image_ocr_results: List[Dict]
    ) -> List[ImageMatch]:
        """
        Match subtitle segments with images based on OCR text overlap.

        Args:
            subtitle_segments: List of dicts with keys: text, start, end
            image_ocr_results: List of dicts with keys: image_path, ocr_text

        Returns:
            List of ImageMatch objects
        """
        matches = []

        for segment in subtitle_segments:
            subtitle_text = segment.get("text", "")
            subtitle_start = segment.get("start", 0)
            subtitle_end = segment.get("end", 0)

            best_match = None
            best_score = 0.0

            for img_result in image_ocr_results:
                image_path = img_result.get("image_path", "")
                ocr_text = img_result.get("ocr_text", "")

                if not ocr_text or not subtitle_text:
                    continue

                score, matched_words = self._calculate_overlap(subtitle_text, ocr_text)

                if score >= self.overlap_threshold and score > best_score:
                    best_score = score
                    best_match = ImageMatch(
                        subtitle_text=subtitle_text,
                        subtitle_start=subtitle_start,
                        subtitle_end=subtitle_end,
                        image_path=image_path,
                        ocr_text=ocr_text,
                        overlap_score=score,
                        matched_words=matched_words
                    )

            if best_match:
                matches.append(best_match)

        return matches

    def _calculate_overlap(self, text1: str, text2: str) -> Tuple[float, List[str]]:
        """
        Calculate Jaccard overlap between two texts.

        Args:
            text1: First text (subtitle)
            text2: Second text (OCR result)

        Returns:
            Tuple of (overlap_score, list of matched words)
        """
        # Tokenize
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)

        if not words1 or not words2:
            return 0.0, []

        set1 = set(words1)
        set2 = set(words2)

        intersection = set1 & set2
        union = set1 | set2

        if len(union) == 0:
            return 0.0, []

        score = len(intersection) / len(union)
        return score, list(intersection)

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize Chinese/English text into words.
        """
        # For Chinese: split each character as separate token
        # For English: split by spaces and punctuation
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
        english_words = re.findall(r"[a-zA-Z]+", text)

        # Combine and normalize
        tokens = [c.lower() for c in chinese_chars] + [w.lower() for w in english_words]
        return tokens

    def match_with_learning(
        self,
        subtitle_segments: List[Dict],
        image_ocr_results: List[Dict],
        learned_patterns: List[Dict] = None,
        similarity_top_k: int = 5
    ) -> List[ImageMatch]:
        """
        Match with learning - considers learned patterns from previous edits.

        Args:
            subtitle_segments: List of subtitle segments
            image_ocr_results: List of image OCR results
            learned_patterns: List of learned patterns (from previous user adjustments)
            similarity_top_k: Number of top patterns to consider

        Returns:
            List of ImageMatch objects
        """
        matches = self.match(subtitle_segments, image_ocr_results)

        if not learned_patterns:
            return matches

        # Boost matches that align with learned patterns
        for match in matches:
            for pattern in learned_patterns[:similarity_top_k]:
                # Check if subtitle matches learned pattern
                pattern_subtitle = pattern.get("subtitle_text", "")
                pattern_ocr = pattern.get("ocr_text", "")

                if pattern_subtitle and pattern_ocr:
                    score, _ = self._calculate_overlap(
                        match.subtitle_text, pattern_subtitle
                    )
                    if score > 0.5:
                        # Boost weight based on pattern frequency
                        frequency = pattern.get("frequency", 1)
                        boost = 1.0 + (frequency * 0.1)
                        match.overlap_score *= boost

        # Re-sort by boosted scores
        matches.sort(key=lambda m: m.overlap_score, reverse=True)

        return matches
