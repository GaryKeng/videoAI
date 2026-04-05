"""
Progress dialog for long-running operations.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QApplication
)
from PyQt6.QtCore import Qt, QTimer


class ProgressDialog(QDialog):
    """Progress dialog for AI operations."""

    def __init__(self, title: str = "Processing", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.cancelled = False

        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet("color: #888;")
        layout.addWidget(self.detail_label)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)

    def update_status(self, message: str, progress: int = None, detail: str = None):
        """
        Update progress status.

        Args:
            message: Status message
            progress: Progress percentage (0-100)
            detail: Detailed status text
        """
        self.status_label.setText(message)

        if progress is not None:
            self.progress_bar.setValue(progress)

        if detail is not None:
            self.detail_label.setText(detail)

        QApplication.processEvents()

    def set_progress(self, current: int, total: int, message: str = None):
        """
        Set progress as ratio.

        Args:
            current: Current step
            total: Total steps
            message: Optional message
        """
        if total > 0:
            percentage = int(current / total * 100)
            self.progress_bar.setValue(percentage)

        if message:
            self.status_label.setText(message)

        QApplication.processEvents()

    def cancel(self):
        """Handle cancel."""
        self.cancelled = True
        self.close()

    def is_cancelled(self) -> bool:
        """Check if cancelled."""
        return self.cancelled


class AnalysisProgressDialog(ProgressDialog):
    """Progress dialog specialized for video analysis."""

    STEPS = [
        "Loading video...",
        "Extracting audio...",
        "Running speech recognition...",
        "Detecting voice activity...",
        "Analyzing errors...",
        "Building timeline...",
        "Matching materials...",
        "Finalizing..."
    ]

    def __init__(self, parent=None):
        super().__init__("Analyzing Video", parent)
        self.current_step = 0

    def next_step(self, detail: str = None):
        """Advance to next step."""
        if self.current_step < len(self.STEPS):
            self.update_status(
                self.STEPS[self.current_step],
                detail=detail
            )
            self.current_step += 1
        QApplication.processEvents()

    def set_step(self, step: int, detail: str = None):
        """Set specific step."""
        self.current_step = step
        if step < len(self.STEPS):
            self.update_status(self.STEPS[step], detail=detail)
        QApplication.processEvents()

    def complete(self):
        """Mark as complete."""
        self.progress_bar.setValue(100)
        self.status_label.setText("Analysis complete!")
        QTimer.singleShot(500, self.close)
