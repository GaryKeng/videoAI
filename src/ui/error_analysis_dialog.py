"""
Error analysis dialog.
"""
from typing import List, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QTextEdit, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt


class ErrorAnalysisDialog(QDialog):
    """Dialog for analyzing detected errors."""

    def __init__(self, error_markers: List[Dict], parent=None):
        super().__init__(parent)
        self.error_markers = error_markers
        self.setWindowTitle("Error Analysis")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Summary
        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout()

        pause_count = sum(1 for e in self.error_markers if e.get("error_type") == "pause")
        rep_count = sum(1 for e in self.error_markers if e.get("error_type") == "repetition")
        filler_count = sum(1 for e in self.error_markers if e.get("error_type") == "filler")

        summary_layout.addWidget(QLabel(f"Pauses: {pause_count}"))
        summary_layout.addWidget(QLabel(f"Repetitions: {rep_count}"))
        summary_layout.addWidget(QLabel(f"Filler Words: {filler_count}"))
        summary_layout.addStretch()

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Error list
        self.error_list = QListWidget()
        self.error_list.itemClicked.connect(self.on_error_clicked)
        layout.addWidget(self.error_list)

        # Detail view
        detail_group = QGroupBox("Error Detail")
        detail_layout = QVBoxLayout()

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)

        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)

        # Buttons
        button_layout = QHBoxLayout()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(deselect_all_btn)

        button_layout.addStretch()

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected)
        button_layout.addWidget(remove_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.populate_errors()

    def populate_errors(self):
        """Populate error list."""
        self.error_widgets = []

        for i, error in enumerate(self.error_markers):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, i)

            error_type = error.get("error_type", "unknown")
            text = error.get("text", "")
            start = error.get("start", 0)
            end = error.get("end", 0)

            item.setText(f"[{error_type.upper()}] {start:.1f}s - {end:.1f}s: {text[:50]}...")
            item.setCheckState(Qt.CheckState.Checked)

            self.error_list.addItem(item)
            self.error_widgets.append(item)

    def on_error_clicked(self, item: QListWidgetItem):
        """Handle error clicked."""
        index = item.data(Qt.ItemDataRole.UserRole)
        error = self.error_markers[index]

        self.detail_text.setText(
            f"Error Type: {error.get('error_type', 'unknown')}\n"
            f"Time: {error.get('start', 0):.1f}s - {error.get('end', 0):.1f}s\n"
            f"Confidence: {error.get('confidence', 0):.2f}\n"
            f"Description: {error.get('description', 'N/A')}\n"
            f"\nText:\n{error.get('text', '')}"
        )

    def select_all(self):
        """Select all errors."""
        for i in range(self.error_list.count()):
            self.error_list.item(i).setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        """Deselect all errors."""
        for i in range(self.error_list.count()):
            self.error_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def remove_selected(self):
        """Remove selected errors from list."""
        for i in range(self.error_list.count() - 1, -1, -1):
            item = self.error_list.item(i)
            if item.checkState() == Qt.CheckState.Unchecked:
                self.error_list.takeItem(i)

    def get_removed_indices(self) -> List[int]:
        """Get indices of removed errors."""
        removed = []
        for i in range(self.error_list.count()):
            item = self.error_list.item(i)
            if item.checkState() == Qt.CheckState.Unchecked:
                removed.append(item.data(Qt.ItemDataRole.UserRole))
        return sorted(removed)
