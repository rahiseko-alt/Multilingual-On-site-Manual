import os
from worker.schemas.transcript import TranscriptData, TranscriptSegment

class FasterWhisperTranscriptionProvider:
    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = os.getenv("WHISPER_MODEL", model_size)
        self.device = os.getenv("WHISPER_DEVICE", device)
        self.compute_type = os.getenv("WHISPER_COMPUTE_TYPE", compute_type)
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model

    def transcribe(self, audio_path: str, language: str = "ja") -> TranscriptData:
        model = self._get_model()
        segments_gen, info = model.transcribe(audio_path, language=language, beam_size=5)
        
        segments = []
        for i, seg in enumerate(segments_gen, start=1):
            segments.append(
                TranscriptSegment(
                    id=f"seg_{i:03d}",
                    start=float(seg.start),
                    end=float(seg.end),
                    text=seg.text.strip()
                )
            )
        
        detected_lang = info.language if hasattr(info, "language") and info.language else language
        return TranscriptData(language=detected_lang, segments=segments)
