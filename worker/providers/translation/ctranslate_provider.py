import os

class CTranslateTranslationProvider:
    def __init__(self, model_path: str | None = None, device: str = "cpu"):
        self.model_path = model_path or os.getenv("TRANSLATION_MODEL_PATH")
        self.device = device
        self._translator = None
        self._sp_model = None

    def _get_translator(self):
        if self._translator is None:
            if not self.model_path or not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Translation model not found at: {self.model_path}")
            import ctranslate2
            import sentencepiece as spm
            
            self._translator = ctranslate2.Translator(self.model_path, device=self.device, compute_type="int8")
            sp_path = os.path.join(self.model_path, "spm.model")
            self._sp_model = spm.SentencePieceProcessor(model_file=sp_path)
        return self._translator, self._sp_model

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text:
            return ""
        results = self.translate_batch([text], source_lang, target_lang)
        return results[0] if results else ""

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        if not texts:
            return []
        if not self.model_path or not os.path.exists(self.model_path):
            from worker.providers.translation.mock_provider import MockTranslationProvider
            return MockTranslationProvider().translate_batch(texts, source_lang, target_lang)

        translator, sp = self._get_translator()
        # M2M100 formatting
        source_prefix = f"__{source_lang}__"
        target_prefix = f"__{target_lang}__"

        tokens = [sp.encode(f"{source_prefix} {t}", out_type=str) for t in texts]
        results = translator.translate_batch(
            tokens,
            target_prefix=[[target_prefix]] * len(texts),
            beam_size=4
        )
        
        translated_texts = []
        for r in results:
            out_tokens = r.hypotheses[0]
            if out_tokens and out_tokens[0] == target_prefix:
                out_tokens = out_tokens[1:]
            translated_texts.append(sp.decode(out_tokens))
        return translated_texts
