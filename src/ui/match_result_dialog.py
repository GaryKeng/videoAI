"""
Match result dialog for manual matching.
"""
from pathlib import Path
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QSlider, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal


class MatchResultDialog(QDialog):
    """Dialog showing match results and allowing manual adjustment."""

    def __init__(self, matches: List[Dict], materials: List[Dict], parent=None):
        super().__init__(parent)
        self.matches = matches
        self.materials = materials
        self.setWindowTitle("Match Results")
        self.setMinimumSize(700, 500)
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Match threshold
        threshold_group = QGroupBox("Match Threshold")
        threshold_layout = QHBoxLayout()

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(50)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)

        self.threshold_label = QLabel("50%")

        threshold_layout.addWidget(QLabel("Min Match:"))
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_label)

        threshold_group.setLayout(threshold_layout)
        layout.addWidget(threshold_group)

        # Matches list
        self.matches_list = QListWidget()
        layout.addWidget(QLabel("Auto Matches:"))
        layout.addWidget(self.matches_list)

        # Materials list
        materials_group = QGroupBox("Available Materials")
        materials_layout = QVBoxLayout()

        self.materials_list = QListWidget()
        self.materials_list.itemClicked.connect(self.on_material_selected)
        materials_layout.addWidget(self.materials_list)

        materials_group.setLayout(materials_layout)
        layout.addWidget(materials_group)

        # Selected match
        selected_group = QGroupBox("Selected Match")
        selected_layout = QVBoxLayout()

        selected_info_layout = QHBoxLayout()
        selected_info_layout.addWidget(QLabel("Subtitle:"))
        self.subtitle_label = QLabel("-")
        selected_layout.addWidget(self.subtitle_label)

        selected_info_layout.addWidget(QLabel("Image:"))
        self.image_label = QLabel("-")
        selected_layout.addWidget(self.image_label)

        selected_layout.addLayout(selected_info_layout)

        # Manual override
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Manual Image:"))
        self.manual_image_edit = QLineEdit()
        self.manual_image_edit.setReadOnly(True)
        manual_layout.addWidget(self.manual_image_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_image)
        manual_layout.addWidget(browse_btn)

        selected_layout.addLayout(manual_layout)

        selected_group.setLayout(selected_layout)
        layout.addWidget(selected_group)

        # Buttons
        button_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.populate_lists()

    def populate_lists(self):
        """Populate matches and materials lists."""
        # Populate matches
        self.match_widgets = []
        for i, match in enumerate(self.matches):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, i)

            subtitle = match.get("subtitle_text", "")[:40]
            image = Path(match.get("image_path", "")).name
            score = match.get("overlap_score", 0)

            item.setText(f"{subtitle}... -> {image} ({score:.0%})")

            self.matches_list.addItem(item)
            self.match_widgets.append(item)

        # Populate materials
        for mat in self.materials:
            item = QListWidgetItem()
            path = Path(mat.get("image_path", ""))
            ocr = mat.get("ocr_text", "")[:40]

            item.setText(f"{path.name}: {ocr}...")
            item.setData(Qt.ItemDataRole.UserRole, mat)

            self.materials_list.addItem(item)

    def on_threshold_changed(self, value: int):
        """Handle threshold slider changed."""
        self.threshold_label.setText(f"{value}%")
        self.filter_matches(value / 100)

    def filter_matches(self, threshold: float):
        """Filter matches by threshold."""
        for i in range(self.matches_list.count()):
            item = self.matches_list.item(i)
            match = self.matches[item.data(Qt.ItemDataRole.UserRole)]
            score = match.get("overlap_score", 0)

            if score >= threshold:
                item.setHidden(False)
            else:
                item.setHidden(True)

    def on_material_selected(self, item: QListWidgetItem):
        """Handle material selected."""
        mat = item.data(Qt.ItemDataRole.UserRole)
        if mat:
            self.manual_image_edit.setText(mat.get("image_path", ""))

    def browse_image(self):
        """Browse for manual image."""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )

        if file_path:
            self.manual_image_edit.setText(file_path)

    def get_adjusted_matches(self) -> List[Dict]:
        """Get adjusted matches after user changes."""
        adjusted = []

        for i in range(self.matches_list.count()):
            item = self.matches_list.item(i)
            if not item.isHidden():
                match_index = item.data(Qt.ItemDataRole.UserRole)
                adjusted.append(self.matches[match_index])

        return adjusted
