"""
Preview panel with video playback.
"""
from pathlib import Path
from typing import Union, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class PreviewPanel(QWidget):
    """Video preview panel with playback controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_player: Optional[QMediaPlayer] = None
        self.video_widget: Optional[QVideoWidget] = None
        self.is_playing = False

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Video display area
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: #1a1a1a;")
        self.video_container.setMinimumSize(640, 360)

        container_layout = QVBoxLayout()
        self.video_container.setLayout(container_layout)

        self.placeholder_label = QLabel("No video loaded")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #666;")
        container_layout.addWidget(self.placeholder_label)

        layout.addWidget(self.video_container)

        # Timeline slider
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setMaximum(1000)
        self.timeline_slider.sliderMoved.connect(self.seek)
        layout.addWidget(self.timeline_slider)

        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        # Playback controls
        controls = QHBoxLayout()

        self.play_btn = QPushButton("▶")
        self.play_btn.setMaximumWidth(50)
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setMaximumWidth(50)
        self.stop_btn.clicked.connect(self.stop)
        controls.addWidget(self.stop_btn)

        controls.addStretch()

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls.addWidget(QLabel("🔊"))
        controls.addWidget(self.volume_slider)

        layout.addLayout(controls)

        self.setLayout(layout)

    def load_video(self, video_path: Union[str, Path]):
        """Load video file."""
        from PyQt6.QtMultimedia import QMediaPlayer
        from PyQt6.QtMultimedia import QAudioOutput

        video_path = Path(video_path)
        if not video_path.exists():
            return

        # Create media player if not exists
        if self.media_player is None:
            self.media_player = QMediaPlayer()
            self.video_widget = QVideoWidget()
            audio_output = QAudioOutput()

            self.media_player.setAudioOutput(audio_output)
            self.media_player.setVideoOutput(self.video_widget)

            # Remove placeholder
            if self.placeholder_label:
                self.placeholder_label.hide()

            self.video_container.layout().addWidget(self.video_widget)

            # Connect signals
            self.media_player.positionChanged.connect(self.on_position_changed)
            self.media_player.durationChanged.connect(self.on_duration_changed)

        # Load video
        self.media_player.setSource(video_path)
        self.timeline_slider.setValue(0)

    def toggle_play(self):
        """Toggle play/pause."""
        if self.media_player is None:
            return

        if self.is_playing:
            self.media_player.pause()
            self.play_btn.setText("▶")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸")

        self.is_playing = not self.is_playing

    def stop(self):
        """Stop playback."""
        if self.media_player:
            self.media_player.stop()
            self.play_btn.setText("▶")
            self.is_playing = False

    def seek(self, position: int):
        """Seek to position."""
        if self.media_player:
            duration = self.media_player.duration()
            self.media_player.setPosition(int(position / 1000 * duration))

    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        if self.media_player and self.media_player.audioOutput():
            self.media_player.audioOutput().setVolume(volume / 100)

    def on_position_changed(self, position: int):
        """Handle position change."""
        duration = self.media_player.duration()
        if duration > 0:
            self.timeline_slider.setValue(int(position / duration * 1000))
            self.update_time_label(position, duration)

    def on_duration_changed(self, duration: int):
        """Handle duration change."""
        self.update_time_label(0, duration)

    def update_time_label(self, position: int, duration: int):
        """Update time display label."""
        def format_time(ms: int) -> str:
            seconds = ms // 1000
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes:02d}:{seconds:02d}"

        pos_str = format_time(position)
        dur_str = format_time(duration)
        self.time_label.setText(f"{pos_str} / {dur_str}")
