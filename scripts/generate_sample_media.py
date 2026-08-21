import subprocess
from pathlib import Path

def generate_sample_mp4(output_mp4_path: str = "fixtures/sample/sample.mp4", duration: int = 6):
    out = Path(output_mp4_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Generate synthetic video with audio using ffmpeg testsrc and sine wave
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration}:size=640x480:rate=25",
        "-f", "lavfi",
        "-i", f"sine=frequency=440:duration={duration}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        str(out)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"Sample video generated at: {out}")

if __name__ == "__main__":
    generate_sample_mp4()
