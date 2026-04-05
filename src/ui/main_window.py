"""
Enhanced main window with full functionality.
"""
from pathlib import Path
from typing import Optional, List, Dict
import traceback

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QDockWidget, QStatusBar, QMenuBar, QMenu,
    QToolBar, QApplication, QProgressDialog,
    QInputDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QIcon

from src.config import VIDEOAI_HOME, MATERIALS_FOLDER, PROJECTS_DIR, EXPORTS_DIR
from src.project_manager import ProjectManager
from src.core.video_analyzer import VideoAnalyzer
from src.core.ocr_matcher import OCRMatcher
from src.core.segmenter import VideoSegmenter
from src.material.material_manager import MaterialManager
from src.timeline.timeline_builder import TimelineBuilder
from src.timeline.video_exporter import VideoExporter
from src.learning.learning_engine import LearningEngine

from src.ui.preview_panel import PreviewPanel
from src.ui.timeline_view import EnhancedTimelineView
from src.ui.material_library_panel import MaterialLibraryPanel
from src.ui.settings_dialog import SettingsDialog
from src.ui.progress_dialog import AnalysisProgressDialog


class AnalysisWorker(QThread):
    """Worker thread for video analysis."""

    progress = pyqtSignal(str, int, str)
    result = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path

    def run(self):
        """Run analysis."""
        try:
            self.progress.emit("Initializing analyzer...", 10, "")

            analyzer = VideoAnalyzer()
            self.progress.emit("Running speech recognition...", 30, "Using Whisper")

            results = analyzer.analyze_video(self.video_path)
            self.progress.emit("Analysis complete", 100, f"Found {len(results['subtitle_segments'])} segments")

            self.result.emit({
                "subtitles": results["subtitle_segments"],
                "vad_segments": results["vad_segments"],
                "errors": results["error_markers"],
                "duration": results.get("video_duration", 0)
            })

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.project_manager = ProjectManager()
        self.project = None
        self.video_path = None
        self.video_analyzer = None
        self.material_manager = MaterialManager()
        self.ocr_matcher = OCRMatcher()
        self.segmenter = VideoSegmenter()
        self.timeline_builder = TimelineBuilder()
        self.exporter = VideoExporter()
        self.learning_engine = LearningEngine()

        self.analysis_worker: Optional[AnalysisWorker] = None

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("VideoAI Auto-Editing Tool")
        icon_path = VIDEOAI_HOME / "VideoAI_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(1400, 900)

        # Create central widget FIRST (so timeline_view exists before menu_bar)
        central = QWidget()
        main_layout = QVBoxLayout()

        # Preview panel
        self.preview_panel = PreviewPanel()
        main_layout.addWidget(self.preview_panel, stretch=3)

        # Timeline view (must be created before create_menu_bar)
        self.timeline_view = EnhancedTimelineView()
        self.timeline_view.item_clicked.connect(self.on_overlay_clicked)
        main_layout.addWidget(self.timeline_view, stretch=2)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        toolbar = self.create_toolbar()
        self.addToolBar(toolbar)

        # Material library dock
        self.material_panel = MaterialLibraryPanel()
        material_dock = QDockWidget("Materials", self)
        material_dock.setWidget(self.material_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, material_dock)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_project = QAction("New Project", self)
        new_project.setShortcut(QKeySequence.StandardKey.New)
        new_project.triggered.connect(self.new_project)
        file_menu.addAction(new_project)

        open_video = QAction("Open Video", self)
        open_video.setShortcut(QKeySequence.StandardKey.Open)
        open_video.triggered.connect(self.open_video)
        file_menu.addAction(open_video)

        file_menu.addSeparator()

        export = QAction("Export", self)
        export.setShortcut(QKeySequence.StandardKey.Save)
        export.triggered.connect(self.export_video)
        file_menu.addAction(export)

        file_menu.addSeparator()

        settings = QAction("Settings", self)
        settings.setShortcut(QKeySequence("Ctrl+,"))
        settings.triggered.connect(self.show_settings)
        file_menu.addAction(settings)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.timeline_view.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.timeline_view.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        delete_action = QAction("Delete Selected", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("View")

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl+="))
        zoom_in_action.triggered.connect(self.timeline_view.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.timeline_view.zoom_out)
        view_menu.addAction(zoom_out_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self) -> QToolBar:
        """Create toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)

        # New project
        new_proj_btn = QPushButton("📁 New")
        new_proj_btn.clicked.connect(self.new_project)
        toolbar.addWidget(new_proj_btn)

        # Open video
        open_btn = QPushButton("🎬 Open")
        open_btn.clicked.connect(self.open_video)
        toolbar.addWidget(open_btn)

        toolbar.addSeparator()

        # Analyze
        self.analyze_btn = QPushButton("🔍 Analyze")
        self.analyze_btn.clicked.connect(self.analyze_video)
        self.analyze_btn.setEnabled(False)
        toolbar.addWidget(self.analyze_btn)

        # Auto edit
        self.auto_edit_btn = QPushButton("✂️ Auto Edit")
        self.auto_edit_btn.clicked.connect(self.auto_edit)
        self.auto_edit_btn.setEnabled(False)
        toolbar.addWidget(self.auto_edit_btn)

        # Manual match
        self.match_btn = QPushButton("🔗 Match")
        self.match_btn.clicked.connect(self.manual_match)
        self.match_btn.setEnabled(False)
        toolbar.addWidget(self.match_btn)

        toolbar.addSeparator()

        # Export
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.clicked.connect(self.export_video)
        self.export_btn.setEnabled(False)
        toolbar.addWidget(self.export_btn)

        # PyQt6: use QWidget spacer instead of addStretch()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        return toolbar

    def new_project(self):
        """Create new project."""
        project_name, ok = QInputDialog.getText(
            self, "New Project", "Project name:"
        )

        if ok and project_name:
            try:
                self.project = self.project_manager.create_project(project_name)
                self.status_bar.showMessage(f"Created project: {project_name}")
                self.import_materials()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create project: {e}")

        elif ok and not project_name:
            # Use default name
            self.project = self.project_manager.create_project("Untitled Project")
            self.import_materials()

    def open_video(self):
        """Open video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Video",
            str(Path.home() / "Videos"),
            "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )

        if file_path:
            self.video_path = file_path
            self.preview_panel.load_video(file_path)
            self.analyze_btn.setEnabled(True)
            self.status_bar.showMessage(f"Loaded: {Path(file_path).name}")

    def analyze_video(self):
        """Analyze video."""
        if not self.video_path:
            return

        self.analyze_btn.setEnabled(False)
        self.auto_edit_btn.setEnabled(False)

        # Show progress dialog
        self.progress_dlg = AnalysisProgressDialog(self)
        self.progress_dlg.show()

        # Start analysis in worker thread
        self.analysis_worker = AnalysisWorker(self.video_path)
        self.analysis_worker.progress.connect(self.on_analysis_progress)
        self.analysis_worker.result.connect(self.on_analysis_complete)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.start()

    def on_analysis_progress(self, message: str, progress: int, detail: str):
        """Handle analysis progress update."""
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            self.progress_dlg.update_status(message, progress, detail)

    def on_analysis_complete(self, results: Dict):
        """Handle analysis complete."""
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            self.progress_dlg.complete()

        try:
            self.video_analyzer = VideoAnalyzer()

            # Store results
            self.subtitle_segments = results.get("subtitles", [])
            self.error_markers = results.get("errors", [])

            # Enable auto edit
            self.auto_edit_btn.setEnabled(True)
            self.match_btn.setEnabled(True)

            # Update timeline view
            timeline_items = self.build_timeline_items()
            self.timeline_view.set_items(timeline_items)

            # Save to project
            if self.project:
                seg_dicts = [
                    {
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                        "is_pause_error": False,
                        "is_repetition_error": False,
                        "is_filler_error": False
                    }
                    for seg in self.subtitle_segments
                ]
                self.project_manager.save_subtitle_segments(seg_dicts)

            self.status_bar.showMessage(
                f"Analyzed: {len(self.subtitle_segments)} segments, "
                f"{len(self.error_markers)} errors"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process results: {e}")
            traceback.print_exc()

        self.analyze_btn.setEnabled(True)

    def on_analysis_error(self, error: str):
        """Handle analysis error."""
        if hasattr(self, 'progress_dlg') and self.progress_dlg:
            self.progress_dlg.close()

        QMessageBox.critical(self, "Analysis Error", error)
        self.analyze_btn.setEnabled(True)
        self.status_bar.showMessage("Analysis failed")

    def build_timeline_items(self) -> List[Dict]:
        """Build timeline items from analysis results."""
        items = []

        if self.video_path:
            items.append({
                "type": "video",
                "start": 0,
                "end": self.video_analyzer.video_duration if self.video_analyzer else 0,
                "source_path": self.video_path
            })

        return items

    def auto_edit(self):
        """Auto edit video."""
        if not self.video_analyzer:
            return

        self.auto_edit_btn.setEnabled(False)
        self.status_bar.showMessage("Running auto edit...")

        QTimer.singleShot(100, self._run_auto_edit)

    def _run_auto_edit(self):
        """Run auto edit process."""
        try:
            # Get subtitle segments
            segments = self.video_analyzer.get_segment_with_errors()

            # Import materials if not already done
            if not self.materials:
                self.materials = self.material_manager.import_materials(
                    self.project.id if self.project else None
                )
                self.material_panel.set_materials(self.materials)

            # Match with OCR
            matches = self.ocr_matcher.match(segments, self.materials)

            # Build timeline
            self.timeline_builder.clear()
            self.timeline_builder.add_matches(matches)

            # Update timeline view
            timeline_items = self.build_timeline_items()
            for match in matches:
                timeline_items.append({
                    "type": "image_overlay",
                    "start": match.subtitle_start,
                    "end": match.subtitle_end,
                    "source_path": match.image_path
                })

            self.timeline_view.set_items(timeline_items)

            self.export_btn.setEnabled(True)
            self.status_bar.showMessage(f"Auto edit complete: {len(matches)} overlays added")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto edit failed: {e}")
            traceback.print_exc()

        self.auto_edit_btn.setEnabled(True)

    def manual_match(self):
        """Manually match a material to a subtitle."""
        # Get selected material
        material = self.material_panel.get_selected_material()
        if not material:
            QMessageBox.information(self, "Manual Match", "Please select a material first")
            return

        # Could show dialog to select subtitle segment
        self.status_bar.showMessage("Manual match mode: Select a subtitle to match")

    def import_materials(self):
        """Import materials from folder."""
        try:
            self.materials = self.material_manager.import_materials(
                self.project.id if self.project else None
            )
            self.material_panel.set_materials(self.materials)
            self.status_bar.showMessage(f"Imported {len(self.materials)} materials")
        except Exception as e:
            self.status_bar.showMessage(f"Material import error: {e}")

    def on_overlay_clicked(self, item_data: Dict):
        """Handle overlay item clicked."""
        self.status_bar.showMessage(
            f"Overlay: {Path(item_data.get('source_path', '')).name} "
            f"at {item_data.get('start', 0):.1f}s"
        )

    def delete_selected(self):
        """Delete selected item."""
        # Would need to track selected item
        pass

    def export_video(self):
        """Export final video."""
        if not self.video_path:
            return

        output_dir = EXPORTS_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Video",
            str(output_dir / "output.mp4"),
            "Video Files (*.mp4)"
        )

        if output_path:
            self.status_bar.showMessage("Exporting...")
            self.export_btn.setEnabled(False)

            QTimer.singleShot(100, lambda: self._export_video(output_path))

    def _export_video(self, output_path: str):
        """Export video (runs in background)."""
        try:
            # Get timeline items
            timeline_items = self.timeline_view.items

            # Separate video and overlay items
            overlay_items = [
                item for item in timeline_items
                if item.get("type") == "image_overlay"
            ]

            # Export
            success = self.exporter.export_with_overlays(
                self.video_path,
                overlay_items,
                output_path
            )

            if success:
                self.status_bar.showMessage(f"Exported: {output_path}")
                QMessageBox.information(
                    self, "Export Complete",
                    f"Video exported to:\n{output_path}"
                )

                # Update project with output path
                if self.project:
                    self.project_manager.update_output_path(output_path)

                # Learn from final result
                self.learn_from_completion(overlay_items)

            else:
                QMessageBox.critical(self, "Export Failed", "Failed to export video")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
            traceback.print_exc()

        self.export_btn.setEnabled(True)

    def learn_from_completion(self, final_overlays: List[Dict]):
        """Learn from completed video."""
        if not self.project:
            return

        try:
            # Compare AI matches with final result
            ai_matches = [
                {
                    "subtitle_text": seg.text,
                    "ocr_text": "",
                    "image_path": item.get("source_path", "")
                }
                for seg, item in zip(self.subtitle_segments, final_overlays)
                if item.get("type") == "image_overlay"
            ]

            final_matches = [
                {
                    "subtitle_text": seg.text,
                    "ocr_text": "",
                    "image_path": item.get("source_path", "")
                }
                for item in final_overlays
                if item.get("type") == "image_overlay"
            ]

            self.learning_engine.process_completed_video(
                self.project.id,
                ai_matches,
                final_matches
            )

            self.status_bar.showMessage("Learning from adjustments complete")

        except Exception as e:
            self.status_bar.showMessage(f"Learning error: {e}")

    def show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About VideoAI",
            "VideoAI Auto-Editing Tool\n\n"
            "An AI-powered video editing tool that automatically:\n"
            "- Detects and removes filler words\n"
            "- Matches subtitle content with materials\n"
            "- Learns from user adjustments\n\n"
            "Version 1.0"
        )

    def closeEvent(self, event):
        """Handle window close."""
        if self.analysis_worker and self.analysis_worker.isRunning():
            self.analysis_worker.terminate()
            self.analysis_worker.wait()

        event.accept()
