"""
Tests for timeline module.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.timeline.timeline_builder import TimelineBuilder, TimelineItem
from src.timeline.edit_history import EditHistory


class TestTimelineBuilder(unittest.TestCase):
    """Tests for TimelineBuilder."""

    def setUp(self):
        self.builder = TimelineBuilder()
        self.builder.set_video_duration(60.0)

    def test_add_video_segment(self):
        """Test adding video segment."""
        self.builder.add_video_segment(0.0, 10.0)
        self.assertEqual(len(self.builder.items), 1)

        item = self.builder.items[0]
        self.assertEqual(item.item_type, "video")
        self.assertEqual(item.start, 0.0)
        self.assertEqual(item.end, 10.0)

    def test_add_image_overlay(self):
        """Test adding image overlay."""
        self.builder.add_image_overlay(5.0, 10.0, "/test/image.png")
        self.assertEqual(len(self.builder.items), 1)

        item = self.builder.items[0]
        self.assertEqual(item.item_type, "image_overlay")
        self.assertEqual(item.source_path, "/test/image.png")

    def test_remove_overlay(self):
        """Test removing overlay."""
        self.builder.add_image_overlay(5.0, 10.0, "/test/image.png")
        self.assertEqual(len(self.builder.items), 1)

        self.builder.remove_overlay_at(5.0)
        self.assertEqual(len(self.builder.items), 0)

    def test_get_timeline_data(self):
        """Test getting timeline data."""
        self.builder.add_video_segment(0.0, 30.0)
        self.builder.add_image_overlay(10.0, 20.0, "/test/image.png")

        data = self.builder.get_timeline_data()
        self.assertEqual(len(data), 2)


class TestEditHistory(unittest.TestCase):
    """Tests for EditHistory."""

    def setUp(self):
        self.history = EditHistory(max_history=10)

    def test_add_operation(self):
        """Test adding operation."""
        self.history.add_operation(
            "add_overlay",
            data={"item": {"id": 1}},
            inverse_data={"index": 0}
        )
        self.assertEqual(len(self.history.history), 1)
        self.assertTrue(self.history.can_undo())

    def test_undo_redo(self):
        """Test undo/redo."""
        self.history.add_operation(
            "add_overlay",
            data={"item": {"id": 1}},
            inverse_data={"index": 0}
        )

        undo_data = self.history.undo()
        self.assertIsNotNone(undo_data)
        self.assertTrue(self.history.can_redo())

        redo_data = self.history.redo()
        self.assertIsNotNone(redo_data)
        self.assertEqual(redo_data["item"]["id"], 1)

    def test_can_not_undo(self):
        """Test can_undo returns False when no history."""
        self.assertFalse(self.history.can_undo())

    def test_clear(self):
        """Test clearing history."""
        self.history.add_operation(
            "add_overlay",
            data={"item": {"id": 1}},
            inverse_data={"index": 0}
        )
        self.history.clear()

        self.assertEqual(len(self.history.history), 0)
        self.assertFalse(self.history.can_undo())


if __name__ == "__main__":
    unittest.main()
