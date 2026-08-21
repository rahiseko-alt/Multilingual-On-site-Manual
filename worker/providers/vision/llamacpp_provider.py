import json
import os
import re
from worker.schemas.vision import VisionObservation, ActionItem

class LlamaCppVisionProvider:
    def __init__(self, model_path: str | None = None, mmproj_path: str | None = None, max_retries: int = 2):
        self.model_path = model_path or os.getenv("VISION_MODEL_PATH")
        self.mmproj_path = mmproj_path or os.getenv("VISION_MMPROJ_PATH")
        self.max_retries = max_retries
        self._llm = None

    def _get_llm(self):
        if self._llm is None:
            if not self.model_path or not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Vision model file not found at: {self.model_path}")
            from llama_cpp import Llama
            from llama_cpp.llama_chat_format import Llava15ChatHandler
            
            chat_handler = Llava15ChatHandler(clip_model_path=self.mmproj_path) if self.mmproj_path else None
            self._llm = Llama(
                model_path=self.model_path,
                chat_handler=chat_handler,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
        return self._llm

    def analyze_frame(self, frame_id: str, timestamp: float, image_path: str, context: str | None = None) -> VisionObservation:
        # If model is not configured, fallback gracefully
        if not self.model_path or not os.path.exists(self.model_path):
            from worker.providers.vision.rule_provider import RuleBasedVisionProvider
            return RuleBasedVisionProvider().analyze_frame(frame_id, timestamp, image_path, context)

        prompt = (
            "Analyze the image and return a JSON object with keys 'objects' (list of strings), "
            "'actions' (list of objects with 'actor', 'action', 'target'), 'visible_text' (list of strings), "
            "and 'uncertain' (list of strings). Do not add operational facts not visible in the frame."
        )

        for attempt in range(self.max_retries):
            try:
                llm = self._get_llm()
                # Run inference
                response = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": "You are an accurate visual analysis assistant for industrial manuals."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_text = response["choices"][0]["message"]["content"]
                parsed = json.loads(raw_text)
                
                actions = [
                    ActionItem(
                        actor=a.get("actor", "作業者"),
                        action=a.get("action", "操作する"),
                        target=a.get("target", "機器")
                    )
                    for a in parsed.get("actions", [])
                ]

                return VisionObservation(
                    frame_id=frame_id,
                    timestamp=timestamp,
                    objects=parsed.get("objects", []),
                    actions=actions,
                    visible_text=parsed.get("visible_text", []),
                    uncertain=parsed.get("uncertain", [])
                )
            except Exception:
                if attempt == self.max_retries - 1:
                    # Final fallback to rule-based
                    from worker.providers.vision.rule_provider import RuleBasedVisionProvider
                    return RuleBasedVisionProvider().analyze_frame(frame_id, timestamp, image_path, context)
