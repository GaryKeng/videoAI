"""
Subtitle export utilities.
"""
from pathlib import Path
from typing import Union, List, Dict
import json


def export_srt(subtitle_segments: List[Dict], output_path: Union[str, Path]) -> Path:
    """
    Export subtitles to SRT format.

    Args:
        subtitle_segments: List of segment dicts
        output_path: Output file path

    Returns:
        Path to output file
    """
    output_path = Path(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(subtitle_segments, 1):
            start = _format_srt_time(seg["start"])
            end = _format_srt_time(seg["end"])

            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{seg['text']}\n")
            f.write("\n")

    return output_path


def export_ass(subtitle_segments: List[Dict], output_path: Union[str, Path]) -> Path:
    """
    Export subtitles to ASS format.

    Args:
        subtitle_segments: List of segment dicts
        output_path: Output file path

    Returns:
        Path to output file
    """
    output_path = Path(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        # Write ASS header
        f.write("[Script Info]\n")
        f.write("Title: VideoAI Subtitles\n")
        f.write("ScriptType: v4.00+\n")
        f.write("\n")

        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,"
                "&H80000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n")
        f.write("\n")

        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

        for seg in subtitle_segments:
            start = _format_ass_time(seg["start"])
            end = _format_ass_time(seg["end"])
            text = seg["text"].replace("\n", " ").replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

            f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")

    return output_path


def export_json(subtitle_segments: List[Dict], output_path: Union[str, Path]) -> Path:
    """
    Export subtitles to JSON format.

    Args:
        subtitle_segments: List of segment dicts
        output_path: Output file path

    Returns:
        Path to output file
    """
    output_path = Path(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(subtitle_segments, f, indent=2, ensure_ascii=False)

    return output_path


def import_srt(srt_path: Union[str, Path]) -> List[Dict]:
    """
    Import subtitles from SRT format.

    Args:
        srt_path: Path to SRT file

    Returns:
        List of segment dicts
    """
    srt_path = Path(srt_path)
    segments = []

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.strip().split("\n\n")

    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            # Skip index line
            time_line = lines[1]
            text = "\n".join(lines[2:])

            # Parse time
            start_str, end_str = time_line.split(" --> ")
            start = _parse_srt_time(start_str)
            end = _parse_srt_time(end_str)

            segments.append({
                "start": start,
                "end": end,
                "text": text
            })

    return segments


def _format_srt_time(seconds: float) -> str:
    """Format time for SRT (HH:MM:SS,mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _format_ass_time(seconds: float) -> str:
    """Format time for ASS (HH:MM:SS.cc)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _parse_srt_time(time_str: str) -> float:
    """Parse SRT time string to seconds."""
    time_str = time_str.replace(",", ".")
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds
