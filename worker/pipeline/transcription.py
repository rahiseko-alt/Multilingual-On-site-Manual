from pathlib import Path
from worker.providers.transcription.base import TranscriptionProvider
from worker.schemas.transcript import TranscriptData

def run_transcription(audio_path: str, provider: TranscriptionProvider, language: str = "ja", output_json_path: str | None = None) -> TranscriptData:
    data = provider.transcribe(audio_path, language=language)
    if output_json_path:
        out = Path(output_json_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data.model_dump_json(indent=2), encoding="utf-8")
    return data
