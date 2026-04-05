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
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QMouseEvent, QIcon
from pathlib import Path

from src.timeline.timeline_builder import TimelineItem
from src.timeline.edit_history import EditHistory


def get_overlay_icon(overlay_type: str) -> QIcon:
    """Get overlay icon based on type."""
    icon_map = {
        "text": "overlay_text.png",
        "image": "overlay_image.png",
        "shape_rect": "overlay_shape_rect.png",
        "shape_circle": "overlay_shape_circle.png",
        "shape_line": "overlay_shape_line.png",
        "sticker": "overlay_sticker.png",
        "filter": "overlay_filter.png",
        "blend": "overlay_blend.png",
        "animation": "overlay_animation.png",
    }
    icon_name = icon_map.get(overlay_type, "overlay_image.png")
    icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / icon_name
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


# Overlay type colors (CapCut-inspired)
OVERLAY_COLORS = {
    "text": "#4A90D9",      # Blue
    "image": "#50C878",      # Green
    "shape_rect": "#FF6B6B", # Red
    "shape_circle": "#9B59B6", # Purple
    "shape_line": "#E91E63", # Pink
    "sticker": "#F39C12",   # Orange
    "filter": "#1ABC9C",     # Teal
    "blend": "#8E44AD",      # Dark purple
    "animation": "#FFD700",   # Gold
}


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

            if x < 0:
                continue

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
        self.overlay_type = item_data.get("overlay_type", "image")
        
        # Get colors
        self.main_color = QColor(OVERLAY_COLORS.get(self.overlay_type, "#50C878"))
        self.dark_color = self.main_color.darker(130)
        
        self.setMinimumSize(80, 44)
        self.setMaximumHeight(44)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        
        # Tooltip
        self.setToolTip(f"{self.overlay_type.title()} Overlay")
        
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
            delta_time = delta_x / 50.0
            self.item_data["start"] = max(0, self.original_start + delta_time)
            self.item_data["end"] = self.original_end + delta_time
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if self.dragging:
            self.dragging = False
            self.clicked.emit(self.item_data)

    def paintEvent(self, event):
        """Paint the overlay item with CapCut-style design."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Main background with gradient effect
        painter.fillRect(rect, self.main_color)
        
        # Top highlight bar
        highlight_rect = QRect(rect.x(), rect.y(), rect.width(), 3)
        painter.fillRect(highlight_rect, self.main_color.lighter(130))
        
        # Bottom shadow bar
        shadow_rect = QRect(rect.x(), rect.bottom() - 2, rect.width(), 2)
        painter.fillRect(shadow_rect, self.dark_color)
        
        # Draw overlay type icon
        icon = get_overlay_icon(self.overlay_type)
        if not icon.isNull():
            icon_pixmap = icon.pixmap(20, 20)
            painter.drawPixmap(rect.x() + 6, rect.y() + 12, icon_pixmap)
        
        # Draw label
        label_x = rect.x() + 30
        label_y = rect.y() + 16
        name = self.item_data.get("source_path", "Overlay")
        if "/" in name:
            name = name.split("/")[-1][:12]
        else:
            name = name[:12]
        
        painter.setPen(QColor(255, 255, 255, 240))
        font = painter.font()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(label_x, label_y + 12, name)
        
        # Duration indicator
        start = self.item_data.get("start", 0)
        end = self.item_data.get("end", 0)
        duration = end - start
        duration_text = f"{duration:.1f}s"
        painter.setPen(QColor(255, 255, 255, 150))
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(label_x, label_y + 24, duration_text)
        
        # Resize handles on sides
        handle_width = 4
        painter.fillRect(rect.x(), rect.y(), handle_width, rect.height(), QColor(255, 255, 255, 100))
        painter.fillRect(rect.right() - handle_width, rect.y(), handle_width, rect.height(), QColor(255, 255, 255, 100))


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
        video_label = QLabel("Video")
        video_label.setStyleSheet("color: #aaa; padding: 5px; font-weight: 600;")
        content_layout.addWidget(video_label)

        self.video_track = TimelineTrack("video")
        content_layout.addWidget(self.video_track)

        # Overlay track with icon
        overlay_track_widget = QWidget()
        overlay_layout_inner = QHBoxLayout()
        overlay_layout_inner.setContentsMargins(8, 6, 8, 6)
        
        overlay_icon = QLabel()
        icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / "overlay_image.png"
        if icon_path.exists():
            overlay_icon.setPixmap(QIcon(str(icon_path)).pixmap(16, 16))
        overlay_layout_inner.addWidget(overlay_icon)
        
        overlay_label = QLabel("Overlays")
        overlay_label.setStyleSheet("color: #ccc; font-weight: 600; font-size: 12px;")
        overlay_layout_inner.addWidget(overlay_label)
        
        # Add overlay menu button
        self.add_overlay_btn = QPushButton("+ Add")
        self.add_overlay_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90D9;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5BA0E9;
            }
        """)
        self.add_overlay_btn.clicked.connect(self.show_add_overlay_menu)
        overlay_layout_inner.addWidget(self.add_overlay_btn)
        
        overlay_layout_inner.addStretch()
        
        overlay_track_widget.setLayout(overlay_layout_inner)
        overlay_track_widget.setStyleSheet("background-color: #252525; border-radius: 4px;")
        content_layout.addWidget(overlay_track_widget)

        self.overlay_scroll = QScrollArea()
        self.overlay_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.overlay_scroll.setMaximumHeight(54)
        self.overlay_container = QWidget()
        self.overlay_layout = QHBoxLayout()
        self.overlay_layout.addStretch()
        self.overlay_container.setLayout(self.overlay_layout)
        self.overlay_scroll.setWidget(self.overlay_container)
        self.overlay_scroll.setStyleSheet("background-color: #1e1e1e; border: 1px solid #333;")
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

        self.play_btn = QPushButton("Play")
        self.play_btn.setIcon(QIcon(str(Path(__file__).parent.parent.parent / "assets" / "icons" / "open_video.png")))
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

        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        layout.addWidget(self.zoom_in_btn)

        self.zoom_out_btn = QPushButton("Zoom Out")
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
        self.play_btn.setText("Pause" if self.playing else "Play")

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

    def show_add_overlay_menu(self):
        """Show add overlay context menu."""
        menu = QMenu(self)
        
        # Overlay type options with icons
        overlay_types = [
            ("text", "Text Overlay", "overlay_text.png"),
            ("image", "Image Overlay", "overlay_image.png"),
            ("shape_rect", "Rectangle Shape", "overlay_shape_rect.png"),
            ("shape_circle", "Circle Shape", "overlay_shape_circle.png"),
            ("shape_line", "Line Shape", "overlay_shape_line.png"),
            ("sticker", "Sticker", "overlay_sticker.png"),
            ("filter", "Filter Overlay", "overlay_filter.png"),
            ("blend", "Blend Overlay", "overlay_blend.png"),
            ("animation", "Animation", "overlay_animation.png"),
        ]
        
        for overlay_type, label, icon_name in overlay_types:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icons" / icon_name
            action = QAction(label, self)
            if icon_path.exists():
                action.setIcon(QIcon(str(icon_path)))
            action.setData(overlay_type)
            action.triggered.connect(lambda checked, t=overlay_type: self.add_overlay_type(t))
            menu.addAction(action)
        
        menu.exec(self.add_overlay_btn.mapToGlobal(self.add_overlay_btn.rect().bottomLeft()))

    def add_overlay_type(self, overlay_type: str):
        """Add a new overlay of the given type."""
        new_overlay = {
            "type": "image_overlay",
            "overlay_type": overlay_type,
            "start": self.current_time,
            "end": self.current_time + 5.0,  # Default 5 second duration
            "source_path": f"New {overlay_type.title()} Overlay"
        }
        self.add_overlay(new_overlay)
        self.status_bar_msg(f"Added {overlay_type} overlay")

    def status_bar_msg(self, msg: str):
        """Show status message (for backward compatibility)."""
        # This will be connected to main window's status bar if available
        pass

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
