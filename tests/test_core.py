"""
Tests for core modules.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.ocr_matcher import OCRMatcher
from src.core.error_detector import ErrorDetector
from src.core.speech_recognizer import SubtitleSegment


class TestOCRMatcher(unittest.TestCase):
    """Tests for OCRMatcher."""

    def setUp(self):
        self.matcher = OCRMatcher(overlap_threshold=0.5)

    def test_tokenize(self):
        """Test tokenization."""
        text = "这是测试文本"
        tokens = self.matcher._tokenize(text)
        # New tokenizer splits Chinese into characters
        self.assertIn("测", tokens)
        self.assertIn("试", tokens)

    def test_exact_match(self):
        """Test exact match."""
        subtitle_segments = [
            {"text": "产品展示", "start": 0.0, "end": 2.0}
        ]
        image_ocr_results = [
            {"image_path": "/test/img1.png", "ocr_text": "产品展示"}
        ]

        matches = self.matcher.match(subtitle_segments, image_ocr_results)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].overlap_score, 1.0)

    def test_partial_match(self):
        """Test partial match."""
        subtitle_segments = [
            {"text": "这是产品展示功能", "start": 0.0, "end": 2.0}
        ]
        image_ocr_results = [
            {"image_path": "/test/img1.png", "ocr_text": "产品展示"}
        ]

        matches = self.matcher.match(subtitle_segments, image_ocr_results)
        self.assertGreaterEqual(len(matches), 1)
        self.assertGreaterEqual(matches[0].overlap_score, 0.5)

    def test_no_match(self):
        """Test no match when text differs."""
        subtitle_segments = [
            {"text": "产品展示", "start": 0.0, "end": 2.0}
        ]
        image_ocr_results = [
            {"image_path": "/test/img1.png", "ocr_text": "联系方式"}
        ]

        matches = self.matcher.match(subtitle_segments, image_ocr_results)
        self.assertEqual(len(matches), 0)


class TestErrorDetector(unittest.TestCase):
    """Tests for ErrorDetector."""

    def setUp(self):
        self.detector = ErrorDetector()

    def test_detect_repetition(self):
        """Test repetition detection."""
        segments = [
            SubtitleSegment(start=0.0, end=1.0, text="今天天气很好"),
            SubtitleSegment(start=1.0, end=2.0, text="今天天气很好"),
            SubtitleSegment(start=2.0, end=3.0, text="我们开始吧"),
        ]

        markers = self.detector.detect_repetition_errors(segments)
        self.assertGreaterEqual(len(markers), 1)
        self.assertEqual(markers[0].error_type, "repetition")

    def test_detect_filler_words(self):
        """Test filler word detection."""
        segments = [
            SubtitleSegment(start=0.0, end=1.0, text="嗯嗯嗯今天天气很好"),
        ]

        markers = self.detector.detect_filler_errors(segments)
        self.assertGreaterEqual(len(markers), 1)
        self.assertEqual(markers[0].error_type, "filler")

    def test_normalize_text(self):
        """Test text normalization."""
        text = "今天,天气！很好？"
        normalized = self.detector._normalize_text(text)
        self.assertNotIn(",", normalized)
        self.assertNotIn("！", normalized)


class TestSubtitleSegment(unittest.TestCase):
    """Tests for SubtitleSegment."""

    def test_create_segment(self):
        """Test creating a segment."""
        segment = SubtitleSegment(
            start=0.0,
            end=2.5,
            text="这是一段测试文字"
        )
        self.assertEqual(segment.start, 0.0)
        self.assertEqual(segment.end, 2.5)
        self.assertEqual(segment.text, "这是一段测试文字")


if __name__ == "__main__":
    unittest.main()
