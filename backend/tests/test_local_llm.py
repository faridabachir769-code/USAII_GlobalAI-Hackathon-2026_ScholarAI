import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.services.ai_service import generate_text

async def main():
    print("=" * 60)
    print("Local LLM Integration Test")
    print("=" * 60)
    
    # Configure variables temporarily if not set in .env
    url = settings.LOCAL_LLM_URL or "http://localhost:8000/v1"
    model = settings.LOCAL_LLM_MODEL or "qwen2.5:7b-instruct-q3_K_M"
    
    print(f"[*] Configuration:")
    print(f"    - LOCAL_LLM_URL   : {url}")
    print(f"    - LOCAL_LLM_MODEL : {model}")
    print("-" * 60)

    # Temporarily override settings if they are empty
    if not settings.LOCAL_LLM_URL:
        settings.LOCAL_LLM_URL = url
    if not settings.LOCAL_LLM_MODEL:
        settings.LOCAL_LLM_MODEL = model

    print("[*] Sending test prompt: 'Explain in one sentence what a government welfare scheme is.'")
    print("[*] Awaiting local inference (may take a moment to load model)...")
    
    try:
        response = await generate_text("Explain in one sentence what a government welfare scheme is.")
        print("-" * 60)
        print("[+] Success! Response from local LLM:")
        print(f"\n{response}\n")
        print("-" * 60)
        print("[+] Connection and inference verified successfully!")
    except Exception as e:
        print("-" * 60)
        print(f"[-] ERROR: Failed to query local LLM: {e}")
        print("-" * 60)
        print("💡 Troubleshoot:")
        print("1. Ensure Docker Model Runner (DMR) or Ollama is running.")
        print(f"2. Verify the server is active on the configured URL: {url}")
        print("   Try visiting http://localhost:8000/v1/models or http://localhost:11434/ in a browser.")
        print(f"3. Make sure you pulled the model: {model}")
        print("   If using DMR: docker model run qwen2.5:7b-instruct-q3_K_M (or llama3.2:3b)")
        print("   If using Ollama: ollama run qwen2.5:7b-instruct-q3_K_M")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
