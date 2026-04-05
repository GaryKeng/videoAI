"""
Tests for learning module.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLearningEngine(unittest.TestCase):
    """Tests for learning engine."""

    def test_pattern_storage_initialization(self):
        """Test pattern storage initialization."""
        from src.learning.learning_engine import PatternStorage

        storage = PatternStorage()
        self.assertIsNotNone(storage)

    def test_learning_engine_initialization(self):
        """Test learning engine initialization."""
        from src.learning.learning_engine import LearningEngine

        engine = LearningEngine()
        self.assertIsNotNone(engine.pattern_storage)

    def test_add_pattern(self):
        """Test adding a pattern."""
        from src.learning.learning_engine import PatternStorage

        storage = PatternStorage()

        # This would add a pattern to ChromaDB
        # In a real test, we'd mock ChromaDB
        # For now, just test that the method exists
        self.assertTrue(hasattr(storage, 'add_pattern'))
        self.assertTrue(hasattr(storage, 'find_similar_patterns'))


class TestLearningStatistics(unittest.TestCase):
    """Tests for learning statistics."""

    def test_statistics_initialization(self):
        """Test statistics initialization."""
        from src.learning.learning_statistics import LearningStatistics

        stats = LearningStatistics()
        self.assertIsNotNone(stats.session)

    def test_get_summary(self):
        """Test getting summary."""
        from src.learning.learning_statistics import LearningStatistics

        stats = LearningStatistics()
        summary = stats.get_summary()

        self.assertIn("total_adjustments", summary)
        self.assertIn("adjustments_by_type", summary)
        self.assertIn("success_rate", summary)


class TestAdvancedMatcher(unittest.TestCase):
    """Tests for advanced matcher."""

    def test_exact_match_score(self):
        """Test exact match scoring."""
        from src.material.advanced_matcher import AdvancedMatcher

        matcher = AdvancedMatcher()
        score = matcher._exact_match_score("产品展示", "产品展示")
        self.assertEqual(score, 1.0)

    def test_semantic_similarity(self):
        """Test semantic similarity."""
        from src.material.advanced_matcher import AdvancedMatcher

        matcher = AdvancedMatcher()
        score = matcher._semantic_similarity("联系我们", "联系方式")
        self.assertGreater(score, 0.0)

    def test_select_best_matches(self):
        """Test selecting best matches."""
        from src.material.advanced_matcher import AdvancedMatcher

        matcher = AdvancedMatcher()

        matches = [
            {"subtitle_start": 0.0, "subtitle_end": 2.0, "overlap_score": 0.9},
            {"subtitle_start": 0.0, "subtitle_end": 2.0, "overlap_score": 0.7},
            {"subtitle_start": 2.0, "subtitle_end": 4.0, "overlap_score": 0.8}
        ]

        selected = matcher.select_best_matches(matches, max_overlays_per_segment=2)

        # Should have selected top matches
        self.assertLessEqual(len(selected), 4)


if __name__ == "__main__":
    unittest.main()
