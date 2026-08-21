class MockTranslationProvider:
    def __init__(self, dictionary: dict[str, dict[str, str]] | None = None):
        # Basic translations for demo/testing
        self.dictionary = dictionary or {
            "作業手順マニュアル": {
                "vi": "Hướng dẫn quy trình thao tác",
                "id": "Panduan Prosedur Operasional"
            },
            "電源を入れる": {
                "vi": "Bật nguồn",
                "id": "Menyalakan daya"
            },
            "赤色の電源ボタンを押します。": {
                "vi": "Nhấn nút nguồn màu đỏ.",
                "id": "Tekan tombol daya berwarna merah."
            },
            "材料を投入する": {
                "vi": "Cho nguyên liệu vào",
                "id": "Memasukkan bahan"
            },
            "投入レバーを右に回して材料を投入します。": {
                "vi": "Xoay cần nạp sang phải để cho nguyên liệu vào.",
                "id": "Putar tuas pengisi ke kanan untuk memasukkan bahan."
            }
        }

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        if not text:
            return ""
        if text in self.dictionary and target_lang in self.dictionary[text]:
            return self.dictionary[text][target_lang]
        
        # Suffix placeholder for unmapped strings
        if target_lang == "vi":
            return f"[VI] {text}"
        elif target_lang == "id":
            return f"[ID] {text}"
        return f"[{target_lang.upper()}] {text}"

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        return [self.translate(t, source_lang, target_lang) for t in texts]
