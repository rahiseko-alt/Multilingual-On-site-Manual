import json
import subprocess
from pathlib import Path

class VideoValidationError(Exception):
    pass

def validate_video(video_path: str, max_size_mb: int = 500, max_duration_minutes: int = 30) -> dict:
    path = Path(video_path)
    if not path.exists() or not path.is_file():
        raise VideoValidationError(f"Video file does not exist: {video_path}")

    # Check file size
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        raise VideoValidationError(f"Video size ({size_mb:.1f}MB) exceeds limit of {max_size_mb}MB")

    # ffprobe execution (shell=False)
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path.resolve())
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        info = json.loads(res.stdout)
    except Exception as e:
        raise VideoValidationError(f"ffprobe failed to inspect file: {e}")

    format_info = info.get("format", {})
    duration = float(format_info.get("duration", 0.0))
    if duration <= 0:
        raise VideoValidationError("Invalid video duration (0 or undetected)")
    if duration > (max_duration_minutes * 60):
        raise VideoValidationError(f"Video duration ({duration/60:.1f} min) exceeds limit of {max_duration_minutes} min")

    streams = info.get("streams", [])
    has_video = any(s.get("codec_type") == "video" for s in streams)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)

    if not has_video:
        raise VideoValidationError("No video stream found in file")

    return {
        "duration": duration,
        "size_mb": size_mb,
        "has_audio": has_audio,
        "format_name": format_info.get("format_name", ""),
        "streams_count": len(streams)
    }
