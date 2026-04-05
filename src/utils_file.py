"""
File system utilities.
"""
import hashlib
import shutil
from pathlib import Path
from typing import Union, List, Optional
from datetime import datetime


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """
    Calculate file hash.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha256)

    Returns:
        Hash string
    """
    file_path = Path(file_path)

    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def copy_file(src: Union[str, Path], dst: Union[str, Path], create_dirs: bool = True) -> Path:
    """
    Copy file to destination.

    Args:
        src: Source file path
        dst: Destination file path
        create_dirs: Create parent directories if needed

    Returns:
        Path to destination file
    """
    src = Path(src)
    dst = Path(dst)

    if create_dirs:
        dst.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src, dst)
    return dst


def move_file(src: Union[str, Path], dst: Union[str, Path], create_dirs: bool = True) -> Path:
    """
    Move file to destination.

    Args:
        src: Source file path
        dst: Destination file path
        create_dirs: Create parent directories if needed

    Returns:
        Path to destination file
    """
    src = Path(src)
    dst = Path(dst)

    if create_dirs:
        dst.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(src, dst)
    return dst


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False,
    extensions: List[str] = None
) -> List[Path]:
    """
    Find files matching pattern or extensions.

    Args:
        directory: Directory to search
        pattern: Glob pattern
        recursive: Search recursively
        extensions: List of extensions to filter (e.g., [".mp4", ".mov"])

    Returns:
        List of matching file paths
    """
    directory = Path(directory)

    if extensions:
        files = []
        for ext in extensions:
            files.extend(directory.glob(f"**/*{ext}" if recursive else f"*{ext}"))
        return sorted(set(files))
    else:
        if recursive:
            return sorted(directory.glob(f"**/{pattern}"))
        else:
            return sorted(directory.glob(pattern))


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        Path to directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes."""
    return Path(file_path).stat().st_size


def get_file_size_human(file_path: Union[str, Path]) -> str:
    """Get file size in human readable format."""
    size = get_file_size(file_path)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} PB"


def get_file_modified_time(file_path: Union[str, Path]) -> datetime:
    """Get file last modified time."""
    return datetime.fromtimestamp(Path(file_path).stat().st_mtime)


def is_valid_video_file(file_path: Union[str, Path]) -> bool:
    """Check if file is a valid video file."""
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"}
    return Path(file_path).suffix.lower() in video_extensions


def is_valid_image_file(file_path: Union[str, Path]) -> bool:
    """Check if file is a valid image file."""
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}
    return Path(file_path).suffix.lower() in image_extensions


def clean_directory(directory: Union[str, Path], pattern: str = "*", recursive: bool = False):
    """
    Delete files matching pattern.

    Args:
        directory: Directory to clean
        pattern: Glob pattern
        recursive: Search recursively
    """
    directory = Path(directory)
    files = find_files(directory, pattern, recursive)

    for file_path in files:
        if file_path.is_file():
            file_path.unlink()


def get_directory_size(directory: Union[str, Path]) -> int:
    """Get total size of all files in directory."""
    directory = Path(directory)
    total_size = 0

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size

    return total_size
