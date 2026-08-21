from typing import Protocol

class TranslationProvider(Protocol):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        ...

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        ...
