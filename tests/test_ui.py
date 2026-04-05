"""
Tests for UI components.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication

# Test utilities
from src.utils_text import (
    tokenize, calculate_jaccard_similarity, normalize_text,
    extract_keywords, remove_filler_words
)
from src.utils_file import (
    calculate_file_hash, is_valid_video_file, is_valid_image_file,
    get_file_size_human
)


class TestTextUtils(unittest.TestCase):
    """Tests for text utilities."""

    def test_tokenize(self):
        """Test tokenization."""
        text = "这是测试文本"
        tokens = tokenize(text)
        # New tokenizer splits Chinese into characters
        self.assertIn("测", tokens)
        self.assertIn("试", tokens)

    def test_calculate_jaccard_similarity(self):
        """Test Jaccard similarity."""
        text1 = "产品展示功能"
        text2 = "产品展示"
        score = calculate_jaccard_similarity(text1, text2)
        self.assertGreater(score, 0.3)

    def test_normalize_text(self):
        """Test text normalization."""
        text = "这是,测试！文本？"
        normalized = normalize_text(text)
        self.assertNotIn(",", normalized)
        self.assertNotIn("！", normalized)

    def test_extract_keywords(self):
        """Test keyword extraction."""
        text = "这是产品展示功能介绍"
        keywords = extract_keywords(text, max_keywords=3)
        self.assertLessEqual(len(keywords), 3)

    def test_remove_filler_words(self):
        """Test filler word removal."""
        text = "嗯这个那个就是说产品"
        cleaned = remove_filler_words(text)
        self.assertNotIn("嗯", cleaned)
        self.assertNotIn("这个", cleaned)


class TestFileUtils(unittest.TestCase):
    """Tests for file utilities."""

    def test_is_valid_video_file(self):
        """Test video file validation."""
        self.assertTrue(is_valid_video_file("test.mp4"))
        self.assertTrue(is_valid_video_file("test.mov"))
        self.assertFalse(is_valid_video_file("test.txt"))
        self.assertFalse(is_valid_video_file("test.jpg"))

    def test_is_valid_image_file(self):
        """Test image file validation."""
        self.assertTrue(is_valid_image_file("test.png"))
        self.assertTrue(is_valid_image_file("test.jpg"))
        self.assertFalse(is_valid_image_file("test.mp4"))
        self.assertFalse(is_valid_image_file("test.txt"))


class TestSubtitleExport(unittest.TestCase):
    """Tests for subtitle export."""

    def test_export_srt(self):
        """Test SRT export."""
        from src.timeline.subtitle_export import export_srt

        segments = [
            {"start": 0.0, "end": 2.5, "text": "第一段字幕"},
            {"start": 2.5, "end": 5.0, "text": "第二段字幕"}
        ]

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False) as f:
            output_path = Path(f.name)

        try:
            export_srt(segments, output_path)
            self.assertTrue(output_path.exists())

            # Check content
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("1", content)
            self.assertIn("00:00:00,000", content)
            self.assertIn("第一段字幕", content)
        finally:
            output_path.unlink()

    def test_import_srt(self):
        """Test SRT import."""
        from src.timeline.subtitle_export import import_srt

        srt_content = """1
00:00:00,000 --> 00:00:02,500
第一段字幕

2
00:00:02,500 --> 00:00:05,000
第二段字幕
"""

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".srt", delete=False, mode="w") as f:
            f.write(srt_content)
            srt_path = Path(f.name)

        try:
            segments = import_srt(srt_path)
            self.assertEqual(len(segments), 2)
            self.assertEqual(segments[0]["text"], "第一段字幕")
        finally:
            srt_path.unlink()


if __name__ == "__main__":
    # Create QApplication for PyQt tests
    app = QApplication([])
    unittest.main()
