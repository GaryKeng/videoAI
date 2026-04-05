"""
Material matcher with advanced matching algorithms.
"""
from typing import List, Dict, Tuple, Optional
import numpy as np

from src.config import MATCH_OVERLAP_THRESHOLD
from src.core.ocr_matcher import OCRMatcher
from src.utils_text import tokenize, calculate_jaccard_similarity


class AdvancedMatcher:
    """Advanced material matching with multiple strategies."""

    def __init__(self, base_matcher: OCRMatcher = None):
        self.base_matcher = base_matcher or OCRMatcher()
        self.match_history: List[Dict] = []

    def match_with_semantic(
        self,
        subtitle_segments: List[Dict],
        image_ocr_results: List[Dict],
        learned_patterns: List[Dict] = None
    ) -> List[Dict]:
        """
        Match with semantic understanding.

        Args:
            subtitle_segments: List of subtitle segments
            image_ocr_results: List of image OCR results
            learned_patterns: Patterns from learning engine

        Returns:
            List of match results with confidence scores
        """
        matches = []

        for segment in subtitle_segments:
            subtitle_text = segment.get("text", "")
            subtitle_start = segment.get("start", 0)
            subtitle_end = segment.get("end", 0)

            best_match = None
            best_score = 0.0
            best_strategy = None

            for img_result in image_ocr_results:
                image_path = img_result.get("image_path", "")
                ocr_text = img_result.get("ocr_text", "")

                if not ocr_text or not subtitle_text:
                    continue

                # Strategy 1: Exact keyword match
                exact_score = self._exact_match_score(subtitle_text, ocr_text)

                # Strategy 2: Partial match (Jaccard)
                jaccard_score = calculate_jaccard_similarity(subtitle_text, ocr_text)

                # Strategy 3: Semantic similarity (simplified)
                semantic_score = self._semantic_similarity(subtitle_text, ocr_text)

                # Combined score with weights
                combined_score = (
                    exact_score * 0.4 +
                    jaccard_score * 0.3 +
                    semantic_score * 0.3
                )

                # Apply learned pattern boost
                if learned_patterns:
                    boost = self._get_pattern_boost(
                        subtitle_text, ocr_text, learned_patterns
                    )
                    combined_score *= boost

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = {
                        "subtitle_text": subtitle_text,
                        "subtitle_start": subtitle_start,
                        "subtitle_end": subtitle_end,
                        "image_path": image_path,
                        "ocr_text": ocr_text,
                        "overlap_score": combined_score,
                        "match_strategy": "semantic"
                    }
                    best_strategy = "semantic"

            if best_match and best_score >= MATCH_OVERLAP_THRESHOLD:
                matches.append(best_match)

        return matches

    def _exact_match_score(self, text1: str, text2: str) -> float:
        """Calculate exact keyword match score."""
        tokens1 = set(tokenize(text1))
        tokens2 = set(tokenize(text2))

        if not tokens1 or not tokens2:
            return 0.0

        # Check for exact overlap
        overlap = tokens1 & tokens2
        if overlap == tokens1 or overlap == tokens2:
            return 1.0

        return len(overlap) / max(len(tokens1), len(tokens2))

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity (simplified version).
        In production, use proper embeddings from sentence-transformers.
        """
        # Simple keyword extraction and comparison
        keywords1 = set(tokenize(text1))
        keywords2 = set(tokenize(text2))

        if not keywords1 or not keywords2:
            return 0.0

        # Category-based matching
        category_keywords = {
            "product": ["产品", "商品", "展示", "介绍"],
            "contact": ["联系", "电话", "邮箱", "地址", "微信"],
            "technology": ["技术", "特点", "优势", "功能"],
            "about": ["公司", "我们", "团队", "介绍"]
        }

        max_similarity = 0.0

        for category, keywords in category_keywords.items():
            has_kw1 = any(kw in keywords1 for kw in keywords)
            has_kw2 = any(kw in keywords2 for kw in keywords)

            if has_kw1 and has_kw2:
                max_similarity = 1.0
                break

            # Partial category match
            common = keywords1 & keywords2
            if common:
                max_similarity = max(max_similarity, len(common) / len(keywords))

        return max_similarity

    def _get_pattern_boost(
        self,
        subtitle_text: str,
        ocr_text: str,
        learned_patterns: List[Dict]
    ) -> float:
        """
        Get boost factor from learned patterns.

        Args:
            subtitle_text: Subtitle text
            ocr_text: OCR text from image
            learned_patterns: Learned patterns from history

        Returns:
            Boost factor (1.0 = no boost, > 1.0 = boost)
        """
        boost = 1.0

        for pattern in learned_patterns:
            pattern_subtitle = pattern.get("subtitle_text", "")
            pattern_ocr = pattern.get("ocr_text", "")

            # Check similarity with pattern
            similarity = calculate_jaccard_similarity(
                subtitle_text, pattern_subtitle
            )

            if similarity > 0.5:
                # Apply frequency-based boost
                frequency = pattern.get("frequency", 1)
                boost = 1.0 + (frequency * 0.1)

                # If pattern was previously adjusted, reduce boost
                if pattern.get("adjustment_type") == "removed":
                    boost *= 0.5

        return boost

    def match_with_temporal(
        self,
        subtitle_segments: List[Dict],
        image_ocr_results: List[Dict],
        window_size: float = 5.0
    ) -> List[Dict]:
        """
        Match with temporal proximity consideration.

        Args:
            subtitle_segments: List of subtitle segments
            image_ocr_results: List of image OCR results
            window_size: Time window to consider for same-subject matches

        Returns:
            List of match results
        """
        matches = []

        # First pass: direct matches
        direct_matches = self.base_matcher.match(
            subtitle_segments, image_ocr_results
        )

        # Second pass: temporal window matching
        for segment in subtitle_segments:
            segment_start = segment.get("start", 0)

            # Find nearby segments
            nearby_segments = [
                s for s in subtitle_segments
                if abs(s.get("start", 0) - segment_start) <= window_size
                and s != segment
            ]

            if nearby_segments:
                # Try to match using nearby segments
                combined_text = segment.get("text", "")
                for nearby in nearby_segments:
                    combined_text += " " + nearby.get("text", "")

                # Match combined text
                for img_result in image_ocr_results:
                    ocr_text = img_result.get("ocr_text", "")
                    score = calculate_jaccard_similarity(combined_text, ocr_text)

                    if score >= MATCH_OVERLAP_THRESHOLD:
                        matches.append({
                            "subtitle_text": combined_text,
                            "subtitle_start": segment_start,
                            "subtitle_end": segment.get("end", 0),
                            "image_path": img_result.get("image_path", ""),
                            "ocr_text": ocr_text,
                            "overlap_score": score,
                            "match_strategy": "temporal"
                        })

        return matches

    def select_best_matches(
        self,
        matches: List[Dict],
        max_overlays_per_segment: int = 3
    ) -> List[Dict]:
        """
        Select best matches when multiple overlays match same segment.

        Args:
            matches: List of all matches
            max_overlays_per_segment: Max overlays per segment

        Returns:
            Filtered list of best matches
        """
        if not matches:
            return []

        # Group by segment
        segment_groups = {}
        for match in matches:
            key = (match["subtitle_start"], match["subtitle_end"])
            if key not in segment_groups:
                segment_groups[key] = []
            segment_groups[key].append(match)

        # Select best from each group
        selected = []
        for key, group in segment_groups.items():
            # Sort by score
            sorted_group = sorted(group, key=lambda x: x.get("overlap_score", 0), reverse=True)

            # Take top N
            for match in sorted_group[:max_overlays_per_segment]:
                selected.append(match)

        return selected
