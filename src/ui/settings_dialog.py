"""
Settings dialog for configuring application options.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt

from src.config import (
    WHISPER_MODEL, WHISPER_LANGUAGE,
    VAD_THRESHOLD, VAD_MAX_PAUSE_DURATION,
    REPETITION_THRESHOLD, MATCH_OVERLAP_THRESHOLD,
    IMAGE_OVERLAY_MAX_WIDTH_RATIO
)


class SettingsDialog(QDialog):
    """Settings configuration dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # AI Settings
        ai_group = QGroupBox("AI Settings")
        ai_layout = QFormLayout()

        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.whisper_model_combo.setCurrentText(WHISPER_MODEL)
        ai_layout.addRow("Whisper Model:", self.whisper_model_combo)

        self.whisper_lang_combo = QComboBox()
        self.whisper_lang_combo.addItems(["auto", "zh", "en", "ja", "ko"])
        self.whisper_lang_combo.setCurrentText(WHISPER_LANGUAGE if WHISPER_LANGUAGE else "auto")
        ai_layout.addRow("Language:", self.whisper_lang_combo)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # VAD Settings
        vad_group = QGroupBox("Voice Activity Detection")
        vad_layout = QFormLayout()

        self.vad_threshold_spin = QDoubleSpinBox()
        self.vad_threshold_spin.setRange(0.1, 0.9)
        self.vad_threshold_spin.setSingleStep(0.1)
        self.vad_threshold_spin.setValue(VAD_THRESHOLD)
        vad_layout.addRow("Threshold:", self.vad_threshold_spin)

        self.max_pause_spin = QDoubleSpinBox()
        self.max_pause_spin.setRange(0.3, 3.0)
        self.max_pause_spin.setSingleStep(0.1)
        self.max_pause_spin.setValue(VAD_MAX_PAUSE_DURATION)
        vad_layout.addRow("Max Pause (s):", self.max_pause_spin)

        vad_group.setLayout(vad_layout)
        layout.addWidget(vad_group)

        # Error Detection Settings
        error_group = QGroupBox("Error Detection")
        error_layout = QFormLayout()

        self.repetition_threshold_spin = QDoubleSpinBox()
        self.repetition_threshold_spin.setRange(0.5, 1.0)
        self.repetition_threshold_spin.setSingleStep(0.05)
        self.repetition_threshold_spin.setValue(REPETITION_THRESHOLD)
        error_layout.addRow("Repetition Threshold:", self.repetition_threshold_spin)

        error_group.setLayout(error_layout)
        layout.addWidget(error_group)

        # OCR Matching Settings
        ocr_group = QGroupBox("OCR Matching")
        ocr_layout = QFormLayout()

        self.match_threshold_spin = QDoubleSpinBox()
        self.match_threshold_spin.setRange(0.3, 0.9)
        self.match_threshold_spin.setSingleStep(0.05)
        self.match_threshold_spin.setValue(MATCH_OVERLAP_THRESHOLD)
        ocr_layout.addRow("Match Threshold:", self.match_threshold_spin)

        self.max_overlay_width_spin = QDoubleSpinBox()
        self.max_overlay_width_spin.setRange(0.1, 0.8)
        self.max_overlay_width_spin.setSingleStep(0.05)
        self.max_overlay_width_spin.setValue(IMAGE_OVERLAY_MAX_WIDTH_RATIO)
        ocr_layout.addRow("Max Overlay Width:", self.max_overlay_width_spin)

        ocr_group.setLayout(ocr_layout)
        layout.addWidget(ocr_group)

        # Learning Settings
        learning_group = QGroupBox("Self-Learning")
        learning_layout = QFormLayout()

        self.enable_learning_check = QCheckBox()
        self.enable_learning_check.setChecked(True)
        learning_layout.addRow("Enable Learning:", self.enable_learning_check)

        learning_group.setLayout(learning_layout)
        layout.addWidget(learning_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_settings(self) -> dict:
        """Get current settings as dict."""
        return {
            "whisper_model": self.whisper_model_combo.currentText(),
            "whisper_language": self.whisper_lang_combo.currentText(),
            "vad_threshold": self.vad_threshold_spin.value(),
            "max_pause_duration": self.max_pause_spin.value(),
            "repetition_threshold": self.repetition_threshold_spin.value(),
            "match_threshold": self.match_threshold_spin.value(),
            "max_overlay_width": self.max_overlay_width_spin.value(),
            "enable_learning": self.enable_learning_check.isChecked()
        }

    def set_settings(self, settings: dict):
        """Set settings from dict."""
        if "whisper_model" in settings:
            self.whisper_model_combo.setCurrentText(settings["whisper_model"])
        if "whisper_language" in settings:
            self.whisper_lang_combo.setCurrentText(settings["whisper_language"])
        if "vad_threshold" in settings:
            self.vad_threshold_spin.setValue(settings["vad_threshold"])
        if "max_pause_duration" in settings:
            self.max_pause_spin.setValue(settings["max_pause_duration"])
        if "repetition_threshold" in settings:
            self.repetition_threshold_spin.setValue(settings["repetition_threshold"])
        if "match_threshold" in settings:
            self.match_threshold_spin.setValue(settings["match_threshold"])
        if "max_overlay_width" in settings:
            self.max_overlay_width_spin.setValue(settings["max_overlay_width"])
        if "enable_learning" in settings:
            self.enable_learning_check.setChecked(settings["enable_learning"])
