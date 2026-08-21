import subprocess
from pathlib import Path
import cv2
from PIL import Image
import imagehash
from worker.schemas.frames import FrameData, FrameItem
from worker.schemas.scene import SceneData
from worker.schemas.transcript import TranscriptData

def extract_and_deduplicate_frames(
    video_path: str,
    scenes: SceneData,
    transcript: TranscriptData | None,
    output_dir: str,
    hash_threshold: int = 6,
    output_json_path: str | None = None
) -> FrameData:
    v_path = Path(video_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect candidate timestamps
    candidates = set()
    for s in scenes.scenes:
        candidates.add(round(s.start + 0.1, 2))
        candidates.add(round((s.start + s.end) / 2.0, 2))
        candidates.add(round(max(s.start, s.end - 0.1), 2))

    if transcript:
        for seg in transcript.segments:
            candidates.add(round((seg.start + seg.end) / 2.0, 2))

    # Sort & remove very close timestamps (< 0.8s)
    sorted_ts = sorted(list(candidates))
    filtered_ts = []
    for ts in sorted_ts:
        if not filtered_ts or (ts - filtered_ts[-1] >= 0.8):
            filtered_ts.append(ts)

    # Extract frames using ffmpeg / OpenCV
    cap = cv2.VideoCapture(str(v_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    
    extracted_frames = []
    prev_hashes = []

    for i, ts in enumerate(filtered_ts, start=1):
        cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)
        ret, frame_bgr = cap.read()
        if not ret or frame_bgr is None:
            continue

        # Convert to PIL for hashing
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)
        cur_phash = imagehash.phash(pil_img)

        # Deduplication check
        is_duplicate = False
        for ph in prev_hashes:
            if cur_phash - ph < hash_threshold:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        prev_hashes.append(cur_phash)
        frame_id = f"frame_{len(extracted_frames) + 1:03d}"
        file_path = out_dir / f"{frame_id}.jpg"
        cv2.imwrite(str(file_path), frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

        extracted_frames.append(
            FrameItem(
                id=frame_id,
                timestamp=ts,
                path=str(file_path.relative_to(out_dir.parent) if out_dir.parent in file_path.parents else file_path),
                phash=str(cur_phash)
            )
        )

    cap.release()
    data = FrameData(frames=extracted_frames)
    if output_json_path:
        out = Path(output_json_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data.model_dump_json(indent=2), encoding="utf-8")

    return data
