"""
Enhanced timeline view with better visualization.
"""
import math
from typing import List, Dict, Optional, Callable, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QSlider, QLabel, QPushButton, QFrame, QMenu
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent

from src.timeline.timeline_builder import TimelineItem
from src.timeline.edit_history import EditHistory


class TimelineRuler(QWidget):
    """Timeline ruler widget showing time markers."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale = 50.0  # pixels per second
        self.offset = 0.0  # scroll offset in seconds
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)

    def paintEvent(self, event):
        """Paint the ruler."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#2a2a2a"))

        width = self.width()
        start_time = self.offset
        end_time = self.offset + (width / self.scale)

        # Draw time markers
        pen = QPen(QColor("#888888"))
        painter.setPen(pen)

        # Major markers every 10 seconds
        major_interval = 10
        # Minor markers every 1 second
        minor_interval = 1

        for t in self._frange(start_time, end_time, minor_interval):
            x = int((t - self.offset) * self.scale)

            if t % major_interval < 0.1:  # Major marker
                painter.drawLine(x, 0, x, 20)
                painter.drawText(x + 3, 15, f"{int(t):02d}:{int(t%60):02d}")
            else:  # Minor marker
                painter.drawLine(x, 0, x, 10)

    def _frange(self, start: float, end: float, step: float) -> List[float]:
        """Generate float range using list comprehension (avoids while-loop GC overhead)."""
        n = int((end - start) / step) + 1
        return [start + i * step for i in range(n)]


class TimelineTrack(QWidget):
    """Timeline track widget for displaying items."""

    def __init__(self, track_type: str = "video", parent=None):
        super().__init__(parent)
        self.track_type = track_type
        self.items: List[Dict] = []
        self.scale = 50.0
        self.offset = 0.0
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)
        self.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")

    def set_items(self, items: List[Dict]):
        """Set track items."""
        self.items = items
        self.update()

    def set_scale(self, scale: float):
        """Set time scale."""
        self.scale = scale
        self.update()

    def set_offset(self, offset: float):
        """Set scroll offset."""
        self.offset = offset
        self.update()

    def paintEvent(self, event):
        """Paint the track."""
        painter = QPainter(self)

        if self.track_type == "video":
            brush = QBrush(QColor("#4a4a8a"))
        else:
            brush = QBrush(QColor("#4a8a4a"))

        pen = QPen(QColor("#666666"))
        painter.setPen(pen)

        for item in self.items:
            start = item.get("start", 0)
            end = item.get("end", 0)
            x = int((start - self.offset) * self.scale)
            width = int((end - start) * self.scale)

            if x + width < 0 or x > self.width():
                continue

            rect = QRect(x, 5, max(width, 10), 50)
            painter.fillRect(rect, brush)
            painter.drawRect(rect)

            # Draw label
            if width > 30:
                source = item.get("source_path", "")
                name = source.split("/")[-1] if source else "Item"
                painter.drawText(x + 5, 35, name[:20])


class OverlayItemWidget(QWidget):
    """Widget representing an overlay item on the timeline."""

    clicked = pyqtSignal(dict)

    def __init__(self, item_data: Dict, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.setMinimumSize(100, 50)
        self.setMaximumHeight(50)
        self.dragging = False
        self.drag_start_x = 0
        self.original_start = 0
        self.original_end = 0

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_start_x = event.position().x()
            self.original_start = self.item_data.get("start", 0)
            self.original_end = self.item_data.get("end", 0)

    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        if self.dragging:
            delta_x = event.position().x() - self.drag_start_x
            delta_time = delta_x / 50.0  # Assuming scale of 50 pixels per second
            self.item_data["start"] = max(0, self.original_start + delta_time)
            self.item_data["end"] = self.original_end + delta_time
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if self.dragging:
            self.dragging = False
            self.clicked.emit(self.item_data)

    def paintEvent(self, event):
        """Paint the overlay item."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#4a8a4a"))

        # Draw border
        pen = QPen(QColor("#2a5a2a"))
        painter.setPen(pen)
        painter.drawRect(self.rect())


class EnhancedTimelineView(QWidget):
    """Enhanced timeline view with interactive editing."""

    item_clicked = pyqtSignal(dict)
    item_moved = pyqtSignal(dict, dict)  # old_data, new_data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: List[Dict] = []
        self.edit_history = EditHistory()
        self.scale = 50.0  # pixels per second
        self.current_time = 0.0
        self.playing = False

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(False)

        # Timeline content
        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Ruler
        self.ruler = TimelineRuler()
        content_layout.addWidget(self.ruler)

        # Video track
        video_label = QLabel("🎬 Video")
        video_label.setStyleSheet("color: #aaa; padding: 5px;")
        content_layout.addWidget(video_label)

        self.video_track = TimelineTrack("video")
        content_layout.addWidget(self.video_track)

        # Overlay track
        overlay_label = QLabel("🖼️ Overlays")
        overlay_label.setStyleSheet("color: #aaa; padding: 5px;")
        content_layout.addWidget(overlay_label)

        self.overlay_scroll = QScrollArea()
        self.overlay_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.overlay_container = QWidget()
        self.overlay_layout = QHBoxLayout()
        self.overlay_layout.addStretch()
        self.overlay_container.setLayout(self.overlay_layout)
        self.overlay_scroll.setWidget(self.overlay_container)
        content_layout.addWidget(self.overlay_scroll)

        content.setLayout(content_layout)
        scroll.setWidget(content)

        # Set minimum width
        scroll.setMinimumWidth(800)

        # Controls
        controls = self.create_controls()
        content_layout.addWidget(controls)

        layout.addWidget(scroll)
        self.setLayout(layout)

    def create_controls(self) -> QWidget:
        """Create playback controls."""
        controls = QWidget()
        layout = QHBoxLayout()

        self.play_btn = QPushButton("▶")
        self.play_btn.clicked.connect(self.toggle_play)
        layout.addWidget(self.play_btn)

        self.current_time_label = QLabel("00:00:00")
        layout.addWidget(self.current_time_label)

        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setMinimum(10)
        self.scale_slider.setMaximum(200)
        self.scale_slider.setValue(50)
        self.scale_slider.setMaximumWidth(150)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        layout.addWidget(QLabel("Scale:"))
        layout.addWidget(self.scale_slider)

        layout.addStretch()

        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("🔍-")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        layout.addWidget(self.zoom_out_btn)

        return controls

    def set_items(self, items: List[Dict]):
        """Set timeline items."""
        self.items = items

        # Update video track
        video_items = [item for item in items if item.get("type") == "video"]
        self.video_track.set_items(video_items)

        # Update overlay track
        self.update_overlay_display()

    def update_overlay_display(self):
        """Update overlay items display."""
        # Clear existing
        while self.overlay_layout.count() > 1:
            item = self.overlay_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add overlay widgets
        for i, item in enumerate(self.items):
            if item.get("type") == "image_overlay":
                widget = OverlayItemWidget(item)
                widget.clicked.connect(self.on_overlay_clicked)
                self.overlay_layout.insertWidget(i, widget)

        self.overlay_layout.addStretch()

    def on_overlay_clicked(self, item_data: Dict):
        """Handle overlay item clicked."""
        self.item_clicked.emit(item_data)

    def toggle_play(self):
        """Toggle playback."""
        self.playing = not self.playing
        self.play_btn.setText("⏸" if self.playing else "▶")

    def on_scale_changed(self, value: int):
        """Handle scale slider changed."""
        self.scale = float(value)
        self.ruler.scale = self.scale
        self.video_track.set_scale(self.scale)

    def zoom_in(self):
        """Zoom in timeline."""
        self.scale = min(200, self.scale * 1.2)
        self.scale_slider.setValue(int(self.scale))

    def zoom_out(self):
        """Zoom out timeline."""
        self.scale = max(10, self.scale / 1.2)
        self.scale_slider.setValue(int(self.scale))

    def add_overlay(self, item: Dict):
        """Add an overlay item."""
        old_items = [item.copy() for item in self.items]
        self.items.append(item)

        # Record in history
        self.edit_history.add_operation(
            "add_overlay",
            data={"item": item},
            inverse_data={"item": item, "index": len(self.items) - 1}
        )

        self.update_overlay_display()

    def remove_overlay(self, index: int):
        """Remove an overlay item."""
        if 0 <= index < len(self.items):
            removed_item = self.items[index]
            old_items = [item.copy() for item in self.items]

            self.items.pop(index)

            # Record in history
            self.edit_history.add_operation(
                "remove_overlay",
                data={"index": index, "item": removed_item},
                inverse_data={"index": index, "item": removed_item}
            )

            self.update_overlay_display()

    def move_overlay(self, old_data: Dict, new_data: Dict):
        """Move an overlay item."""
        self.item_moved.emit(old_data, new_data)

    def undo(self):
        """Undo last operation."""
        inverse_data = self.edit_history.undo()
        if inverse_data:
            # Apply inverse operation
            pass

    def redo(self):
        """Redo next operation."""
        data = self.edit_history.redo()
        if data:
            # Apply operation
            pass
