"""
Video utilities and helpers.
"""
import subprocess
from pathlib import Path
from typing import Union, Tuple, Optional
import json


def get_video_info(video_path: Union[str, Path]) -> dict:
    """
    Get video information using FFprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dict with video info (duration, width, height, codec, etc.)
    """
    video_path = Path(video_path)

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,width,height,pix_fmt",
        "-of", "json",
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}

    info = {}

    # Format info
    if "format" in data:
        fmt = data["format"]
        info["duration"] = float(fmt.get("duration", 0))
        info["size"] = int(fmt.get("size", 0))
        info["bit_rate"] = int(fmt.get("bit_rate", 0))

    # Stream info
    if "streams" in data and len(data["streams"]) > 0:
        stream = data["streams"][0]
        info["codec"] = stream.get("codec_name", "")
        info["width"] = stream.get("width", 0)
        info["height"] = stream.get("height", 0)
        info["pix_fmt"] = stream.get("pix_fmt", "")

    return info


def get_video_duration(video_path: Union[str, Path]) -> float:
    """Get video duration in seconds."""
    info = get_video_info(video_path)
    return info.get("duration", 0.0)


def get_video_resolution(video_path: Union[str, Path]) -> Tuple[int, int]:
    """Get video resolution as (width, height)."""
    info = get_video_info(video_path)
    return (info.get("width", 0), info.get("height", 0))


def extract_audio(
    video_path: Union[str, Path],
    audio_path: Union[str, Path] = None,
    format: str = "wav",
    sample_rate: int = 16000,
    channels: int = 1
) -> Path:
    """
    Extract audio from video using FFmpeg.

    Args:
        video_path: Input video path
        audio_path: Output audio path (optional)
        format: Output audio format
        sample_rate: Sample rate in Hz
        channels: Number of channels

    Returns:
        Path to extracted audio file
    """
    video_path = Path(video_path)

    if audio_path is None:
        audio_path = video_path.with_suffix(f".{format}")

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
        "-ar", str(sample_rate),
        "-ac", str(channels),
        str(audio_path)
    ]

    subprocess.run(cmd, capture_output=True)
    return audio_path


def create_thumbnail(
    video_path: Union[str, Path],
    thumbnail_path: Union[str, Path] = None,
    timestamp: float = 0,
    size: Tuple[int, int] = (320, 180)
) -> Path:
    """
    Create thumbnail from video at specified timestamp.

    Args:
        video_path: Input video path
        thumbnail_path: Output thumbnail path
        timestamp: Timestamp in seconds
        size: Output size (width, height)

    Returns:
        Path to thumbnail
    """
    video_path = Path(video_path)

    if thumbnail_path is None:
        thumbnail_path = video_path.with_suffix(".jpg")

    cmd = [
        "ffmpeg", "-y", "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-vf", f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=decrease",
        "-q:v", "2",
        str(thumbnail_path)
    ]

    subprocess.run(cmd, capture_output=True)
    return thumbnail_path


def create_video_from_images(
    image_paths: list,
    output_path: Union[str, Path],
    duration: float = 3.0,
    fps: int = 30,
    transition: str = "fade"
) -> Path:
    """
    Create video from a list of images.

    Args:
        image_paths: List of image paths
        output_path: Output video path
        duration: Duration per image in seconds
        fps: Frames per second
        transition: Transition effect (fade, none)

    Returns:
        Path to output video
    """
    output_path = Path(output_path)

    if not image_paths:
        raise ValueError("No image paths provided")

    # Create concat file
    concat_dir = output_path.parent / "temp_concat"
    concat_dir.mkdir(parents=True, exist_ok=True)

    concat_file = concat_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for img_path in image_paths:
            # Create video from image
            img_video = concat_dir / f"{Path(img_path).stem}.mp4"
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1",
                "-i", str(img_path),
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-vf", f"scale=1920:1080:force_original_aspect_ratio=decrease",
                "-shortest",
                str(img_video)
            ], capture_output=True)
            f.write(f"file '{img_video}'\n")

    # Concatenate
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(output_path)
    ], capture_output=True)

    # Cleanup
    concat_file.unlink()

    return output_path


def trim_video(
    video_path: Union[str, Path],
    output_path: Union[str, Path],
    start: float,
    end: float
) -> Path:
    """
    Trim video to specified time range.

    Args:
        video_path: Input video path
        output_path: Output video path
        start: Start time in seconds
        end: End time in seconds

    Returns:
        Path to output video
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-ss", str(start),
        "-to", str(end),
        "-c", "copy",
        str(output_path)
    ]

    subprocess.run(cmd, capture_output=True)
    return output_path
