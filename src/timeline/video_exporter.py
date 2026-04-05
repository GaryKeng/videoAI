"""
Video exporter - exports final video using FFmpeg.
"""
import logging
from pathlib import Path
from typing import Union, List, Optional, Tuple
import subprocess

from src.config import OUTPUT_VIDEO_CODEC, OUTPUT_VIDEO_PRESET, OUTPUT_AUDIO_CODEC
from src.timeline.timeline_builder import TimelineBuilder, TimelineItem
from src.timeline.image_overlayer import ImageOverlayer

logger = logging.getLogger(__name__)


class VideoExporter:
    """Export final video with FFmpeg."""

    def __init__(
        self,
        video_codec: str = OUTPUT_VIDEO_CODEC,
        preset: str = OUTPUT_VIDEO_PRESET,
        audio_codec: str = OUTPUT_AUDIO_CODEC
    ):
        self.video_codec = video_codec
        self.preset = preset
        self.audio_codec = audio_codec

    def export_with_overlays(
        self,
        video_path: Union[str, Path],
        overlay_items: List[TimelineItem],
        output_path: Union[str, Path],
        video_width: int = 1920,
        video_height: int = 1080
    ) -> bool:
        """
        Export video with image overlays.

        Args:
            video_path: Input video path
            overlay_items: List of overlay items
            output_path: Output video path
            video_width: Video width
            video_height: Video height

        Returns:
            True if successful
        """
        video_path = Path(video_path)
        output_path = Path(output_path)

        if not overlay_items:
            # No overlays, simple copy
            return self._copy_video(video_path, output_path)

        # Build FFmpeg command with overlays
        cmd = ["ffmpeg", "-y", "-i", str(video_path)]

        # Add overlay inputs
        for item in overlay_items:
            if item.source_path:
                cmd.extend(["-i", str(item.source_path)])

        # Build filter complex
        filter_parts = []

        # Main video passthrough
        filter_parts.append("[0:v]null")

        # Chain overlays
        current_stream = "0:v"
        for i, item in enumerate(overlay_items):
            if item.item_type != "image_overlay" or not item.source_path:
                continue

            enable = f"between(t,{item.start},{item.end})"
            filter_parts.append(
                f"[{i+1}:v]overlay=0:0:enable='{enable}'[out]"
            )

        if len(filter_parts) > 1:
            cmd.extend(["-filter_complex", ";".join(filter_parts)])
            cmd.extend(["-map", f"[out]"])
        else:
            cmd.extend(["-map", "0:v"])

        # Encoding options
        cmd.extend([
            "-c:v", self.video_codec,
            "-preset", self.preset,
            "-crf", "23",
            "-c:a", self.audio_codec
        ])

        cmd.append(str(output_path))

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg export failed: {result.stderr}")

        return result.returncode == 0

    def export_with_timeline(
        self,
        video_path: Union[str, Path],
        timeline_builder: TimelineBuilder,
        output_path: Union[str, Path]
    ) -> bool:
        """
        Export video with complete timeline.

        Args:
            video_path: Input video path
            timeline_builder: TimelineBuilder with all items
            output_path: Output video path

        Returns:
            True if successful
        """
        overlay_items = timeline_builder.get_overlays()
        return self.export_with_overlays(
            video_path,
            overlay_items,
            output_path
        )

    def _copy_video(
        self,
        input_path: Path,
        output_path: Path
    ) -> bool:
        """Simple video copy without re-encoding."""
        if not input_path.exists():
            logger.error(f"Input video not found: {input_path}")
            return False

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-c", "copy",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg copy failed: {result.stderr}")
            return False

        return True

    def get_video_info(self, video_path: Union[str, Path]) -> dict:
        """
        Get video information using FFprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dict with video info (empty dict if failed)
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration,size:stream=codec_name,width,height",
                "-of", "json",
                str(video_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            import json
            data = json.loads(result.stdout)
            return data
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return {}

    def segment_video(
        self,
        video_path: Union[str, Path],
        segments: List[Tuple[float, float]],
        output_dir: Path
    ) -> List[Path]:
        """
        Segment video into multiple parts.

        Args:
            video_path: Input video path
            segments: List of (start, end) time tuples
            output_dir: Output directory

        Returns:
            List of output segment paths
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = []
        for i, (start, end) in enumerate(segments):
            output_path = output_dir / f"segment_{i:03d}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-ss", str(start),
                "-to", str(end),
                "-c", "copy",
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True)
            output_paths.append(output_path)

        return output_paths
