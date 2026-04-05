"""
Video segmenter - splits video based on detected segments.
"""
from pathlib import Path
from typing import Union, List, Tuple, Optional
import subprocess

from src.core.speech_recognizer import SubtitleSegment
from src.core.error_detector import ErrorMarker


class VideoSegmenter:
    """Segment video based on detected segments and errors."""

    def __init__(self):
        self.segments: List[Tuple[float, float]] = []

    def create_segments_from_subtitles(
        self,
        subtitle_segments: List[SubtitleSegment],
        error_markers: List[ErrorMarker] = None
    ) -> List[Tuple[float, float]]:
        """
        Create video segments from subtitle segments, optionally removing error segments.

        Args:
            subtitle_segments: List of subtitle segments
            error_markers: Optional list of error markers

        Returns:
            List of (start, end) time tuples for video segments
        """
        segments = []
        error_ranges = set()

        # Build set of error time ranges
        if error_markers:
            for marker in error_markers:
                error_ranges.add((marker.segment.start, marker.segment.end))

        # Create segments excluding error ranges
        for seg in subtitle_segments:
            if (seg.start, seg.end) not in error_ranges:
                segments.append((seg.start, seg.end))

        self.segments = segments
        return segments

    def create_segments_keep_all(self, subtitle_segments: List[SubtitleSegment]) -> List[Tuple[float, float]]:
        """
        Create segments keeping all content (no removal).

        Args:
            subtitle_segments: List of subtitle segments

        Returns:
            List of (start, end) time tuples
        """
        segments = [(seg.start, seg.end) for seg in subtitle_segments]
        self.segments = segments
        return segments

    def create_segments_remove_errors(
        self,
        subtitle_segments: List[SubtitleSegment],
        error_markers: List[ErrorMarker],
        remove_types: List[str] = None
    ) -> List[Tuple[float, float]]:
        """
        Create segments with specific error types removed.

        Args:
            subtitle_segments: List of subtitle segments
            error_markers: List of error markers
            remove_types: List of error types to remove (pause, repetition, filler)

        Returns:
            List of (start, end) time tuples
        """
        if remove_types is None:
            remove_types = ["pause", "repetition", "filler"]

        segments = []
        error_ranges = set()

        # Build error ranges for specified types
        for marker in error_markers:
            if marker.error_type in remove_types:
                error_ranges.add((marker.segment.start, marker.segment.end))

        # Create segments excluding error ranges
        for seg in subtitle_segments:
            if (seg.start, seg.end) not in error_ranges:
                segments.append((seg.start, seg.end))

        self.segments = segments
        return segments

    def segment_video(
        self,
        video_path: Union[str, Path],
        output_dir: Union[str, Path],
        prefix: str = "segment"
    ) -> List[Path]:
        """
        Segment video into parts using FFmpeg.

        Args:
            video_path: Input video path
            output_dir: Output directory
            prefix: Output file prefix

        Returns:
            List of output segment paths
        """
        if not self.segments:
            return []

        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = []
        for i, (start, end) in enumerate(self.segments):
            output_path = output_dir / f"{prefix}_{i:03d}.mp4"
            self._extract_segment(video_path, start, end, output_path)
            output_paths.append(output_path)

        return output_paths

    def _extract_segment(
        self,
        video_path: Path,
        start: float,
        end: float,
        output_path: Path
    ):
        """
        Extract a single segment from video.

        Args:
            video_path: Input video path
            start: Start time in seconds
            end: End time in seconds
            output_path: Output path
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-ss", str(start),
            "-to", str(end),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(output_path)
        ]

        subprocess.run(cmd, capture_output=True)

    def concatenate_segments(
        self,
        segment_paths: List[Path],
        output_path: Path
    ) -> bool:
        """
        Concatenate segments back into single video.

        Args:
            segment_paths: List of segment paths
            output_path: Output path

        Returns:
            True if successful
        """
        if not segment_paths:
            return False

        # Create concat file
        concat_dir = output_path.parent / "temp_concat"
        concat_dir.mkdir(parents=True, exist_ok=True)
        concat_file = concat_dir / "concat.txt"

        with open(concat_file, "w") as f:
            for path in segment_paths:
                f.write(f"file '{path}'\n")

        # Run FFmpeg concat
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True)

        # Cleanup
        concat_file.unlink()
        try:
            concat_dir.rmdir()
        except Exception:
            pass

        return result.returncode == 0

    def get_segments(self) -> List[Tuple[float, float]]:
        """Get current segments."""
        return self.segments
