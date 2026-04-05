"""
File watcher - monitors the materials folder for new files.
"""
import time
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.config import MATERIALS_FOLDER


class MaterialsFileHandler(FileSystemEventHandler):
    """Handle file system events in materials folder."""

    def __init__(self, callback: Callable[[str, str], None] = None):
        """
        Initialize file handler.

        Args:
            callback: Callback function(new_path, event_type)
        """
        self.callback = callback
        self.last_modified = {}

    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if not event.is_directory:
            self._handle_file_event(event, "created")

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if not event.is_directory:
            self._handle_file_event(event, "modified")

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion."""
        if not event.is_directory:
            self._handle_file_event(event, "deleted")

    def _handle_file_event(self, event: FileSystemEvent, event_type: str):
        """Handle file event with debouncing."""
        file_path = event.src_path
        current_time = time.time()

        # Debounce rapid events
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < 2.0:
                return

        self.last_modified[file_path] = current_time

        if self.callback:
            self.callback(file_path, event_type)


class FileWatcher:
    """Watch materials folder for changes."""

    def __init__(self, watch_path: Path = None):
        """
        Initialize file watcher.

        Args:
            watch_path: Path to watch (defaults to MATERIALS_FOLDER)
        """
        self.watch_path = watch_path or MATERIALS_FOLDER
        self.observer: Optional[Observer] = None
        self.handler = None

    def start_watching(self, callback: Callable[[str, str], None] = None):
        """
        Start watching the materials folder.

        Args:
            callback: Callback function(new_path, event_type)
        """
        if self.observer is not None:
            return

        self.watch_path.mkdir(parents=True, exist_ok=True)

        self.handler = MaterialsFileHandler(callback=callback)
        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(self.watch_path),
            recursive=False
        )
        self.observer.start()
        print(f"Started watching: {self.watch_path}")

    def stop_watching(self):
        """Stop watching the materials folder."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("Stopped watching materials folder")

    def is_watching(self) -> bool:
        """Check if watcher is active."""
        return self.observer is not None
