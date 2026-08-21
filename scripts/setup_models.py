import os
import sys

def setup_models():
    print("Video2Doc MultiLang Model Setup Helper")
    print("---------------------------------------")
    print("1. Whisper: Model will be automatically downloaded by faster-whisper on first run.")
    print("2. Qwen3-VL-2B (llama.cpp GGUF): Download quantized GGUF from Hugging Face if using local VLM.")
    print("3. M2M100 (CTranslate2): Convert or download M2M100 418M model if using local CTranslate2.")
    print("Setup guide completed.")

if __name__ == "__main__":
    setup_models()
