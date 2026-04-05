"""
Main application entry point.
"""
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import VIDEOAI_HOME, LOGS_DIR
from src.database.models import db_manager


def setup_logging():
    """Setup logging configuration."""
    import logging

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "videoai.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="VideoAI Auto-Editing Tool")
    parser.add_argument("--project", "-p", type=str, help="Project name")
    parser.add_argument("--video", "-v", type=str, help="Video file path")
    parser.add_argument("--gui", "-g", action="store_true", help="Launch GUI")
    parser.add_argument("--no-gui", action="store_true", help="Run without GUI")
    return parser.parse_args()


def main():
    """Main entry point."""
    setup_logging()

    args = parse_args()

    if args.gui or not args.no_gui:
        # Launch GUI
        try:
            from PyQt6.QtWidgets import QApplication
            from src.ui.main_window import MainWindow

            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            sys.exit(app.exec())
        except ImportError as e:
            print(f"PyQt6 not available: {e}")
            print("Install with: pip install PyQt6")
            return 1
    else:
        # CLI mode
        print("VideoAI Auto-Editing Tool - CLI Mode")
        print("Use --gui to launch GUI")

        if args.video:
            print(f"Processing video: {args.video}")
            # TODO: Implement CLI processing

        return 0


if __name__ == "__main__":
    sys.exit(main())
