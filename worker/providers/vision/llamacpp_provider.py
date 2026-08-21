import base64
import json
import os
from pathlib import Path
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

    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_frame(self, frame_id: str, timestamp: float, image_path: str, context: str | None = None) -> VisionObservation:
        img_path = Path(image_path)
        if not img_path.exists():
            return VisionObservation(
                frame_id=frame_id,
                timestamp=timestamp,
                objects=[],
                actions=[],
                visible_text=[],
                uncertain=["image_file_not_found"],
                provider_status="failed"
            )

        if not self.model_path or not os.path.exists(self.model_path):
            # Fail-closed: Return empty observation if model is unconfigured
            return VisionObservation(
                frame_id=frame_id,
                timestamp=timestamp,
                objects=[],
                actions=[],
                visible_text=[],
                uncertain=["vision_model_unconfigured"],
                provider_status="failed"
            )

        prompt = (
            "Analyze the image and return a JSON object with keys 'objects' (list of strings), "
            "'actions' (list of objects with 'actor', 'action', 'target'), 'visible_text' (list of strings), "
            "and 'uncertain' (list of strings). Do not hallucinate or add operational facts not visible in the frame."
        )

        b64_img = self._encode_image(str(img_path))
        data_uri = f"data:image/jpeg;base64,{b64_img}"

        for attempt in range(self.max_retries):
            try:
                llm = self._get_llm()
                # Pass both text prompt and image data to multimodal chat completion
                response = llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": "You are an accurate visual analysis assistant for industrial manuals. Output strictly JSON."},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": data_uri}}
                            ]
                        }
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
                    uncertain=parsed.get("uncertain", []),
                    provider_status="success"
                )
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return VisionObservation(
                        frame_id=frame_id,
                        timestamp=timestamp,
                        objects=[],
                        actions=[],
                        visible_text=[],
                        uncertain=[f"vision_analysis_error: {str(e)}"],
                        provider_status="failed"
                    )
