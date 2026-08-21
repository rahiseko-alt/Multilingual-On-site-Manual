from worker.schemas.transcript import TranscriptData, TranscriptSegment

class MockTranscriptionProvider:
    def __init__(self, sample_segments: list[dict] | None = None):
        self.sample_segments = sample_segments or [
            {"id": "seg_001", "start": 0.0, "end": 4.5, "text": "まず、この赤いボタンを押して電源を入れます。"},
            {"id": "seg_002", "start": 5.0, "end": 9.2, "text": "次に、投入レバーを右に回して材料を投入します。"}
        ]

    def transcribe(self, audio_path: str, language: str = "ja") -> TranscriptData:
        segments = [
            TranscriptSegment(
                id=s["id"],
                start=s["start"],
                end=s["end"],
                text=s["text"]
            )
            for s in self.sample_segments
        ]
        return TranscriptData(language=language, segments=segments)
