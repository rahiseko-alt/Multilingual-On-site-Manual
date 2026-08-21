import subprocess
from pathlib import Path

def extract_audio(video_path: str, output_wav_path: str) -> str:
    v_path = Path(video_path).resolve()
    out_path = Path(output_wav_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg 16kHz mono pcm_s16le (shell=False)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(v_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(out_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return str(out_path)
