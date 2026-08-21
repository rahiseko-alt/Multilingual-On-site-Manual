"""
Instant Public URL Sharer for Video2Doc MultiLang
Allows anyone to access and use the Web UI from the internet instantly.
"""
import sys
import os
import subprocess
import time
import shutil

def main():
    port = 8000
    print("==================================================")
    print("Video2Doc MultiLang - Instant Public URL Launcher")
    print("==================================================")
    
    # 1. Start FastAPI server in background
    print(f"[*] Starting local Web server on port {port}...")
    server_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "apps.api.main:app",
        "--host", "0.0.0.0",
        "--port", str(port)
    ])
    
    time.sleep(2)
    
    print("\n[OK] Local Web UI is running at: http://localhost:8000")
    print("[*] To make this publicly accessible online:")
    print("    Option A: Use Cloudflare Tunnel (Free, no account required)")
    print("              Run: cloudflared tunnel --url http://localhost:8000")
    print("    Option B: Use ngrok")
    print("              Run: ngrok http 8000")
    print("    Option C: Deploy directly to Hugging Face Spaces / Render / Fly.io")
    print("==================================================")
    print("Press Ctrl+C to stop the server.")

    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
        server_process.terminate()

if __name__ == "__main__":
    main()
