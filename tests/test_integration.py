"""
Integration tests for VideoAI.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    VIDEOAI_HOME, MATERIALS_FOLDER, MATERIALS_DIR,
    MATCH_OVERLAP_THRESHOLD
)


class TestConfiguration(unittest.TestCase):
    """Tests for configuration."""

    def test_project_paths_exist(self):
        """Test that project paths are configured."""
        self.assertIsNotNone(VIDEOAI_HOME)
        self.assertIsNotNone(MATERIALS_FOLDER)

    def test_match_threshold(self):
        """Test match threshold is set correctly."""
        self.assertEqual(MATCH_OVERLAP_THRESHOLD, 0.5)


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_module_imports(self):
        """Test that all modules can be imported."""
        # Core modules
        from src.core.speech_recognizer import SpeechRecognizer
        from src.core.vad_detector import VADDetector
        from src.core.error_detector import ErrorDetector
        from src.core.ocr_matcher import OCRMatcher
        from src.core.video_analyzer import VideoAnalyzer

        # Material modules
        from src.material.material_manager import MaterialManager
        from src.material.file_watcher import FileWatcher

        # Timeline modules
        from src.timeline.timeline_builder import TimelineBuilder
        from src.timeline.image_overlayer import ImageOverlayer
        from src.timeline.video_exporter import VideoExporter

        # Learning modules
        from src.learning.learning_engine import LearningEngine

        # Database
        from src.database.models import Project

        # UI
        from src.ui.main_window import MainWindow

    def test_config_paths(self):
        """Test configuration paths."""
        from src.config import (
            PROJECTS_DIR, MATERIALS_DIR, EXPORTS_DIR, LOGS_DIR
        )

        self.assertTrue(PROJECTS_DIR.exists() or PROJECTS_DIR.parent.exists())
        self.assertTrue(MATERIALS_DIR.exists() or MATERIALS_DIR.parent.exists())
        self.assertTrue(EXPORTS_DIR.exists() or EXPORTS_DIR.parent.exists())


class TestWorkflow(unittest.TestCase):
    """Tests for workflow components."""

    def test_timeline_builder_workflow(self):
        """Test timeline builder workflow."""
        from src.timeline.timeline_builder import TimelineBuilder
        from src.core.ocr_matcher import ImageMatch

        builder = TimelineBuilder()
        builder.set_video_duration(60.0)

        # Add video segment
        builder.add_video_segment(0.0, 30.0)
        builder.add_video_segment(30.0, 60.0)

        # Add overlay
        builder.add_image_overlay(10.0, 15.0, "/test/image.png")

        items = builder.get_timeline_data()
        self.assertEqual(len(items), 3)

        overlays = builder.get_overlays()
        self.assertEqual(len(overlays), 1)

    def test_edit_history_workflow(self):
        """Test edit history workflow."""
        from src.timeline.edit_history import EditHistory

        history = EditHistory()

        # Add operation
        history.add_operation(
            "add_overlay",
            data={"item": {"id": 1}},
            inverse_data={"index": 0}
        )

        self.assertTrue(history.can_undo())
        self.assertFalse(history.can_redo())

        # Undo
        undo_data = history.undo()
        self.assertIsNotNone(undo_data)
        self.assertTrue(history.can_redo())

        # Redo
        redo_data = history.redo()
        self.assertIsNotNone(redo_data)
        self.assertEqual(redo_data["item"]["id"], 1)


if __name__ == "__main__":
    unittest.main()
