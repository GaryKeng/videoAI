"""
Video thumbnail widget for PyQt6.
"""
from pathlib import Path
from typing import Union, Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor


class ThumbnailWidget(QWidget):
    """Widget to display video thumbnail."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnail_path: Optional[str] = None
        self.video_path: Optional[str] = None
        self.timestamp: float = 0

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(160, 90)
        self.image_label.setMaximumSize(160, 90)
        self.image_label.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")

        layout.addWidget(self.image_label)

        self.setLayout(layout)

    def load_thumbnail(self, thumbnail_path: Union[str, Path], video_path: Union[str, Path] = None):
        """
        Load thumbnail from file.

        Args:
            thumbnail_path: Path to thumbnail image
            video_path: Optional path to video (for regeneration)
        """
        thumbnail_path = Path(thumbnail_path)

        if thumbnail_path.exists():
            self.thumbnail_path = str(thumbnail_path)
            self.video_path = str(video_path) if video_path else None

            pixmap = QPixmap(str(thumbnail_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    160, 90,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)

    def set_video(self, video_path: Union[str, Path], timestamp: float = 0):
        """
        Set video and generate thumbnail.

        Args:
            video_path: Path to video file
            timestamp: Timestamp in seconds
        """
        from src.timeline.video_utils import create_thumbnail

        self.video_path = str(video_path)
        self.timestamp = timestamp

        video_path = Path(video_path)
        thumbnail_path = video_path.with_suffix(".thumb.jpg")

        if thumbnail_path.exists():
            self.load_thumbnail(thumbnail_path, video_path)
        else:
            try:
                create_thumbnail(video_path, thumbnail_path, timestamp)
                self.load_thumbnail(thumbnail_path, video_path)
            except Exception:
                self.image_label.setText("No Preview")

    def clear(self):
        """Clear thumbnail."""
        self.thumbnail_path = None
        self.video_path = None
        self.image_label.clear()
        self.image_label.setText("No Preview")


class ThumbnailStrip(QWidget):
    """Strip of thumbnails for timeline navigation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnails: list = []
        self.max_thumbnails: int = 10

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        from PyQt6.QtWidgets import QScrollArea, QHBoxLayout

        self.scroll_area = QScrollArea()
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setMinimumHeight(110)

        container = QWidget()
        self.thumbnail_layout = QHBoxLayout()
        self.thumbnail_layout.setSpacing(5)
        container.setLayout(self.thumbnail_layout)

        self.scroll_area.setWidget(container)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)

        self.setLayout(main_layout)

    def add_thumbnail(self, thumbnail_path: Union[str, Path] = None, video_path: Union[str, Path] = None):
        """Add thumbnail to strip."""
        thumb_widget = ThumbnailWidget()

        if thumbnail_path and Path(thumbnail_path).exists():
            thumb_widget.load_thumbnail(thumbnail_path)
        elif video_path:
            thumb_widget.set_video(video_path)

        self.thumbnail_layout.addWidget(thumb_widget)
        self.thumbnails.append(thumb_widget)

        # Limit number of thumbnails
        while len(self.thumbnails) > self.max_thumbnails:
            widget = self.thumbnails.pop(0)
            self.thumbnail_layout.removeWidget(widget)
            widget.deleteLater()

    def clear(self):
        """Clear all thumbnails."""
        for widget in self.thumbnails:
            self.thumbnail_layout.removeWidget(widget)
            widget.deleteLater()
        self.thumbnails.clear()
