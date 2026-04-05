"""
Image overlayer - handles image overlay positioning and video composition.
"""
from typing import Union, List, Dict, Tuple
from pathlib import Path
import subprocess
import json

from src.config import IMAGE_OVERLAY_MAX_WIDTH_RATIO, IMAGE_OVERLAY_FADE_DURATION, IMAGE_OVERLAY_POSITION
from src.timeline.timeline_builder import TimelineItem


class ImageOverlayer:
    """Handle image overlay positioning and effects."""

    def __init__(
        self,
        max_width_ratio: float = IMAGE_OVERLAY_MAX_WIDTH_RATIO,
        fade_duration: float = IMAGE_OVERLAY_FADE_DURATION,
        position: str = IMAGE_OVERLAY_POSITION
    ):
        self.max_width_ratio = max_width_ratio
        self.fade_duration = fade_duration
        self.position = position

    def calculate_overlay_position(
        self,
        video_width: int,
        video_height: int,
        image_width: int,
        image_height: int
    ) -> Tuple[int, int]:
        """
        Calculate overlay position based on configuration.

        Args:
            video_width: Video width in pixels
            video_height: Video height in pixels
            image_width: Image width in pixels
            image_height: Image height in pixels

        Returns:
            (x, y) position tuple
        """
        # Calculate scaled dimensions
        max_width = int(video_width * self.max_width_ratio)
        scale = min(max_width / image_width, 1.0)
        scaled_width = int(image_width * scale)
        scaled_height = int(image_height * scale)

        # Calculate position based on configured position
        if self.position == "center-top":
            x = (video_width - scaled_width) // 2
            y = 20  # Small margin from top
        elif self.position == "center":
            x = (video_width - scaled_width) // 2
            y = (video_height - scaled_height) // 2
        elif self.position == "center-bottom":
            x = (video_width - scaled_width) // 2
            y = video_height - scaled_height - 20
        else:
            x = (video_width - scaled_width) // 2
            y = 20

        return (x, y)

    def get_video_dimensions(self, video_path: Union[str, Path]) -> Tuple[int, int]:
        """
        Get video dimensions using FFprobe.

        Args:
            video_path: Path to video file

        Returns:
            (width, height) tuple
        """
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "json",
            str(video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        if data.get("streams"):
            stream = data["streams"][0]
            return (stream["width"], stream["height"])

        return (1920, 1080)  # Default fallback

    def generate_overlay_filter(
        self,
        timeline_items: List[TimelineItem],
        video_width: int,
        video_height: int
    ) -> Tuple[str, List[str]]:
        """
        Generate FFmpeg overlay filter string.

        Args:
            timeline_items: List of image overlay timeline items
            video_width: Video width
            video_height: Video height

        Returns:
            Tuple of (filter_complex_string, list_of_overlay_inputs)
        """
        overlays = []
        inputs = ["0:v"]  # Start with main video

        for i, item in enumerate(timeline_items):
            if item.item_type != "image_overlay":
                continue

            # Get overlay image dimensions
            try:
                from PIL import Image
                with Image.open(item.source_path) as img:
                    img_width, img_height = img.size
            except Exception:
                img_width, img_height = 400, 300

            # Calculate position
            x, y = self.calculate_overlay_position(
                video_width, video_height,
                img_width, img_height
            )

            # Create filter
            enable_str = f"between(t,{item.start},{item.end})"

            if self.fade_duration > 0:
                # Add fade in/out
                fade_in = f"if(lt(t,{item.start}+0.3),0,1)"
                fade_out = f"if(gt(t,{item.end}-0.3),0,1)"
                enable_str = f"{enable_str}*if(between(t,{item.start},{item.start}+0.3),(t-{item.start})/0.3,if(between(t,{item.end}-0.3,{item.end}),({item.end}-t)/0.3,1))"

            overlay_filter = f"[{i+1}:v]overlay=0:0:enable='{enable_str}'"
            overlays.append(overlay_filter)

        return ",".join(overlays), inputs

    def apply_overlays_ffmpeg(
        self,
        video_path: Union[str, Path],
        overlay_items: List[TimelineItem],
        output_path: Union[str, Path]
    ) -> bool:
        """
        Apply overlays to video using FFmpeg.

        Args:
            video_path: Input video path
            overlay_items: List of overlay items
            output_path: Output video path

        Returns:
            True if successful
        """
        video_path = Path(video_path)
        output_path = Path(output_path)

        if not overlay_items:
            # No overlays, just copy
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-c", "copy",
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True)
            return True

        # Get video dimensions
        width, height = self.get_video_dimensions(video_path)

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y"]

        # Add input videos
        cmd.extend(["-i", str(video_path)])
        for item in overlay_items:
            if item.source_path:
                cmd.extend(["-i", str(item.source_path)])

        # Generate filter
        filter_str, inputs = self.generate_overlay_filter(overlay_items, width, height)

        if filter_str:
            cmd.extend(["-filter_complex", filter_str])
            cmd.extend(["-map", f"{len(overlay_items)}:v"])
        else:
            cmd.extend(["-map", "0:v"])

        cmd.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "23"])
        cmd.append(str(output_path))

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
