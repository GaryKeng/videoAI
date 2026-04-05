"""
Keyboard shortcuts manager.
"""
from typing import Dict, Callable, Union
from PyQt6.QtCore import QObject
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QApplication


class ShortcutManager(QObject):
    """Manage keyboard shortcuts for the application."""

    def __init__(self):
        super().__init__()
        self.shortcuts: Dict[str, QKeySequence] = {}
        self.callbacks: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        key: Union[str, QKeySequence],
        callback: Callable
    ):
        """
        Register a keyboard shortcut.

        Args:
            name: Shortcut name
            key: Key sequence (e.g., "Ctrl+S", "Ctrl+Shift+P")
            callback: Function to call when shortcut is triggered
        """
        if isinstance(key, str):
            key_sequence = QKeySequence(key)
        else:
            key_sequence = key

        self.shortcuts[name] = key_sequence
        self.callbacks[name] = callback

    def get_shortcuts(self) -> Dict[str, str]:
        """Get all registered shortcuts as dict."""
        return {
            name: seq.toString()
            for name, seq in self.shortcuts.items()
        }

    def apply_to_widget(self, widget):
        """
        Apply all shortcuts to a widget.

        Args:
            widget: QWidget to apply shortcuts to
        """
        for name, sequence in self.shortcuts.items():
            callback = self.callbacks.get(name)
            if callback:
                from PyQt6.QtWidgets import QShortcut
                shortcut = QShortcut(sequence, widget)
                shortcut.activated.connect(callback)


# Default shortcuts
DEFAULT_SHORTCUTS = {
    "new_project": "Ctrl+N",
    "open_video": "Ctrl+O",
    "save": "Ctrl+S",
    "export": "Ctrl+E",
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y",
    "delete": "Del",
    "zoom_in": "Ctrl++",
    "zoom_out": "Ctrl+-",
    "play": "Space",
    "analyze": "Ctrl+A",
    "auto_edit": "Ctrl+G",
}
