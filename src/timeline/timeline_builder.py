"""
Timeline builder - builds edit timeline with video segments and image overlays.
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import subprocess

from src.config import IMAGE_OVERLAY_MAX_WIDTH_RATIO, IMAGE_OVERLAY_FADE_DURATION
from src.core.ocr_matcher import ImageMatch


@dataclass
class TimelineItem:
    """Timeline item (video segment or image overlay)."""
    item_type: str  # "video" or "image_overlay"
    start: float
    end: float
    source_path: Optional[str] = None
    overlay_position: Tuple[int, int] = (0, 0)
    z_index: int = 0
    file_path: Optional[str] = None


class TimelineBuilder:
    """Build and manage edit timeline."""

    def __init__(self):
        self.items: List[TimelineItem] = []
        self.video_duration: float = 0.0

    def set_video_duration(self, duration: float):
        """Set total video duration."""
        self.video_duration = duration

    def add_video_segment(
        self,
        start: float,
        end: float,
        source_path: Optional[str] = None
    ):
        """
        Add a video segment.

        Args:
            start: Start time in seconds
            end: End time in seconds
            source_path: Path to source video
        """
        self.items.append(TimelineItem(
            item_type="video",
            start=start,
            end=end,
            source_path=source_path
        ))

    def add_image_overlay(
        self,
        start: float,
        end: float,
        image_path: str,
        position: Tuple[int, int] = (0, 0),
        z_index: int = 1
    ):
        """
        Add an image overlay item.

        Args:
            start: Start time in seconds
            end: End time in seconds
            image_path: Path to overlay image
            position: (x, y) position
            z_index: Z-index for layering
        """
        self.items.append(TimelineItem(
            item_type="image_overlay",
            start=start,
            end=end,
            source_path=image_path,
            overlay_position=position,
            z_index=z_index
        ))

    def add_matches(self, matches: List[ImageMatch]):
        """
        Add image overlay items from OCR matches.

        Args:
            matches: List of ImageMatch objects
        """
        for match in matches:
            self.add_image_overlay(
                start=match.subtitle_start,
                end=match.subtitle_end,
                image_path=match.image_path
            )

    def remove_overlay_at(self, time_point: float, tolerance: float = 0.5):
        """
        Remove overlay at given time point.

        Args:
            time_point: Time in seconds
            tolerance: Time tolerance in seconds
        """
        self.items = [
            item for item in self.items
            if not (
                item.item_type == "image_overlay" and
                abs(item.start - time_point) < tolerance
            )
        ]

    def move_overlay(
        self,
        time_point: float,
        new_start: float,
        new_end: float,
        tolerance: float = 0.5
    ):
        """
        Move overlay to new time position.

        Args:
            time_point: Current time point
            new_start: New start time
            new_end: New end time
            tolerance: Time tolerance
        """
        for item in self.items:
            if (
                item.item_type == "image_overlay" and
                abs(item.start - time_point) < tolerance
            ):
                item.start = new_start
                item.end = new_end

    def get_overlays(self) -> List[TimelineItem]:
        """Get all image overlay items."""
        return [
            item for item in self.items
            if item.item_type == "image_overlay"
        ]

    def get_video_segments(self) -> List[TimelineItem]:
        """Get all video segment items."""
        return [
            item for item in self.items
            if item.item_type == "video"
        ]

    def get_timeline_data(self) -> List[Dict]:
        """
        Get timeline data as list of dicts.

        Returns:
            List of timeline item dicts
        """
        return [
            {
                "type": item.item_type,
                "start": item.start,
                "end": item.end,
                "source_path": item.source_path,
                "position": item.overlay_position,
                "z_index": item.z_index
            }
            for item in sorted(self.items, key=lambda x: (x.start, x.z_index))
        ]

    def clear(self):
        """Clear all timeline items."""
        self.items.clear()
