"""
Material library panel for displaying imported materials.
"""
from pathlib import Path
from typing import List, Dict, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QAbstractItemView,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


class MaterialLibraryPanel(QWidget):
    """Material library panel widget."""

    material_selected = pyqtSignal(dict)
    materials_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.materials: List[Dict] = []
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("Material Library"))
        header.addStretch()

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setMaximumWidth(40)
        self.refresh_btn.clicked.connect(self.refresh_materials)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Material list
        self.material_list = QListWidget()
        self.material_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.material_list.itemClicked.connect(self.on_material_clicked)
        self.material_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.material_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.material_list)

        # Info label
        self.info_label = QLabel("No materials")
        self.info_label.setStyleSheet("color: #888;")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def set_materials(self, materials: List[Dict]):
        """Set materials list."""
        self.materials = materials
        self.update_display()

    def update_display(self):
        """Update material list display."""
        self.material_list.clear()

        for mat in self.materials:
            path = Path(mat.get("image_path", ""))
            ocr_text = mat.get("ocr_text", "")

            item_text = f"{path.name}\n"
            item_text += f"   OCR: {ocr_text[:60]}{'...' if len(ocr_text) > 60 else ''}"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, mat)
            self.material_list.addItem(item)

        count = len(self.materials)
        self.info_label.setText(f"{count} material{'s' if count != 1 else ''}")

    def on_material_clicked(self, item: QListWidgetItem):
        """Handle material clicked."""
        mat = item.data(Qt.ItemDataRole.UserRole)
        if mat:
            self.material_selected.emit(mat)

    def show_context_menu(self, position):
        """Show context menu."""
        menu = QMenu()

        view_action = QAction("View", self)
        view_action.triggered.connect(self.view_selected_material)
        menu.addAction(view_action)

        copy_action = QAction("Copy OCR Text", self)
        copy_action.triggered.connect(self.copy_ocr_text)
        menu.addAction(copy_action)

        menu.exec_(self.material_list.mapToGlobal(position))

    def view_selected_material(self):
        """View selected material."""
        current_row = self.material_list.currentRow()
        if 0 <= current_row < len(self.materials):
            mat = self.materials[current_row]
            # Could open in preview
            pass

    def copy_ocr_text(self):
        """Copy OCR text to clipboard."""
        current_row = self.material_list.currentRow()
        if 0 <= current_row < len(self.materials):
            mat = self.materials[current_row]
            ocr_text = mat.get("ocr_text", "")
            from PyQt6.QtGui import QGuiApplication
            QGuiApplication.clipboard().setText(ocr_text)

    def refresh_materials(self):
        """Refresh materials."""
        self.materials_changed.emit()

    def get_selected_material(self) -> Optional[Dict]:
        """Get selected material."""
        current_row = self.material_list.currentRow()
        if 0 <= current_row < len(self.materials):
            return self.materials[current_row]
        return None
