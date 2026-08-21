from typing import Protocol
from worker.schemas.transcript import TranscriptData

class TranscriptionProvider(Protocol):
    def transcribe(self, audio_path: str, language: str = "ja") -> TranscriptData:
        ...
