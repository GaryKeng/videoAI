"""
Progress tracking for long-running operations.
"""
from typing import Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class ProgressTracker(QObject):
    """Track progress of operations with callback support."""

    progress = pyqtSignal(str, int, str)  # message, percentage, detail
    started = pyqtSignal()
    completed = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_step = 0
        self.total_steps = 100
        self.steps_description = []

    def set_total_steps(self, total: int):
        """Set total number of steps."""
        self.total_steps = max(1, total)
        self.current_step = 0

    def set_steps_description(self, descriptions: list):
        """Set descriptions for each step."""
        self.steps_description = descriptions

    def update(self, message: str = None, percentage: int = None, detail: str = None):
        """Emit progress update."""
        if percentage is None:
            percentage = int(self.current_step / self.total_steps * 100)

        if message is None and self.steps_description:
            if self.current_step < len(self.steps_description):
                message = self.steps_description[self.current_step]

        self.progress.emit(message or "", percentage, detail or "")

    def step(self, detail: str = None):
        """Advance one step."""
        self.current_step += 1
        percentage = int(self.current_step / self.total_steps * 100)
        message = None
        if self.steps_description and self.current_step < len(self.steps_description):
            message = self.steps_description[self.current_step]
        self.update(message, percentage, detail)

    def start(self):
        """Mark as started."""
        self.current_step = 0
        self.started.emit()

    def complete(self):
        """Mark as completed."""
        self.current_step = self.total_steps
        self.completed.emit()

    def fail(self, error_message: str):
        """Mark as failed."""
        self.failed.emit(error_message)


class ModelDownloadProgress:
    """Track AI model download progress."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.downloaded_bytes = 0
        self.total_bytes = 0

    def update(self, downloaded: int, total: int):
        """Update download progress."""
        self.downloaded_bytes = downloaded
        self.total_bytes = total
        percentage = int(downloaded / total * 100) if total > 0 else 0
        print(f"Downloading {self.model_name}: {percentage}% ({downloaded}/{total} bytes)")

    def is_complete(self) -> bool:
        """Check if download is complete."""
        return self.total_bytes > 0 and self.downloaded_bytes >= self.total_bytes


class WhisperProgressCallback:
    """Callback for Whisper transcription progress."""

    def __init__(self, tracker: ProgressTracker = None):
        self.tracker = tracker
        self.callback = None

    def set_progress_callback(self, callback: Callable):
        """Set callback function called during transcription."""
        self.callback = callback

    def __call__(self, processed: int, total: int):
        """Called by Whisper during transcription."""
        percentage = int(processed / total * 100) if total > 0 else 0
        message = f"Transcribing... {percentage}%"

        if self.tracker:
            self.tracker.update(message, percentage)
        elif self.callback:
            self.callback(processed, total, percentage)
        else:
            print(f"Transcribing: {percentage}%")
