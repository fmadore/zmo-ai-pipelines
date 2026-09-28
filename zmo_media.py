"""Bounded-memory audio preparation using the existing ffmpeg executable."""

import math
import shutil
import subprocess
from pathlib import Path

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def duration_seconds(source):
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is required to check recording duration")
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(source),
        ],
        capture_output=True,
        check=True,
        timeout=60,
    )
    duration = float(result.stdout)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Recording duration must be finite and positive")
    return duration


def audio_segments(
    source, directory, limit_seconds, overlap_seconds=0, *, duration=None, skip_indices=()
):
    """Yield one segment at a time; ffmpeg reads only the requested interval.

    The caller may delete each yielded segment immediately after processing.
    Offsets follow the source timeline, independently of encoder padding.
    Completed segment indices yield (offset, None) without running ffmpeg.
    """
    source, directory = Path(source), Path(directory)
    skip_indices = set(skip_indices)
    limit_seconds, overlap_seconds = float(limit_seconds), float(overlap_seconds)
    if not 0 <= overlap_seconds < limit_seconds - 0.1 or not math.isfinite(limit_seconds):
        raise ValueError("Segment duration must be positive and longer than overlap")
    duration = duration if duration is not None else duration_seconds(source)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Recording duration must be finite and positive")
    video = source.suffix.lower() in VIDEO_EXTENSIONS
    if duration <= limit_seconds and not video:
        yield 0.0, None if 1 in skip_indices else source
        return
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required for long recordings and video soundtracks")
    directory.mkdir(parents=True, exist_ok=True)
    start, index = 0.0, 1
    while start < duration:
        path = directory / f"segment-{index:05d}.mp3"
        # A small margin keeps encoded duration below the provider limit.
        length = min(limit_seconds - 0.1, duration - start)
        if index in skip_indices:
            yield start, None
            if start + length >= duration - 0.001:
                break
            start += length - overlap_seconds
            index += 1
            continue
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-ss",
                str(start),
                "-i",
                str(source),
                "-t",
                str(length),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "64k",
                str(path),
            ],
            capture_output=True,
            timeout=max(300, length),
        )
        if result.returncode or not path.is_file():
            raise RuntimeError(
                "Could not extract soundtrack: " + result.stderr.decode("utf-8", "replace")[:300]
            )
        yield start, path
        if start + length >= duration - 0.001:
            break
        start += length - overlap_seconds
        index += 1
