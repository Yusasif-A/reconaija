import os
import sys
import subprocess

# --- CONFIGURATION FOR EMBEDDING GEMMA ---
LLAMACPP_DIR = os.path.expanduser('~/llama.cpp')
BUILD_DIR = os.path.join(LLAMACPP_DIR, 'build')

MODEL_REPO = 'Qwen/Qwen3-Embedding-0.6B-GGUF'
QUANT = 'Qwen3-Embedding-0.6B-Q8_0.gguf'

SERVER_BINARY = os.path.join(BUILD_DIR, 'bin', 'llama-server')

def download_model():
    """Download the GGUF model via huggingface_hub (auto-cached)."""
    print(f"Downloading {QUANT}...")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Installing huggingface_hub...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--quiet', 'huggingface_hub'])
        from huggingface_hub import hf_hub_download

    model_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=QUANT,
        resume_download=True,
        local_files_only=False
    )
    print(f"Model ready at: {model_path}")
    return model_path

def main():
    model_path = download_model()

    # Use all available cores minus 2
    n_threads = str(max(1, (os.cpu_count() or 8) - 2))

    PORT = os.getenv('PORT', '8000')

    # KEY CHANGES FOR CONCURRENT USERS:
    cmd = [
        str(SERVER_BINARY),
        '-m', model_path,
        '--host', '0.0.0.0',
        '--port', PORT,
        '--embeddings',

        # CONCURRENCY SETTINGS (CRITICAL):
        '--parallel', '8',           # Allow 8 concurrent requests (was missing!)
        '--cont-batching',           # Enable continuous batching for parallel processing

        # PERFORMANCE SETTINGS:
        '--ctx-size', '2048',        # Reduced from 4096 for faster processing
        '--batch-size', '512',
        '--ubatch-size', '256',      # Smaller micro-batch for responsiveness
        '--threads', n_threads,
        '-ngl', '0',                 # CPU only
        '--pooling', 'mean',

        # TIMEOUT SETTINGS:
        '--timeout', '300',          # 5 minute timeout per request
    ]

    os.environ['OMP_NUM_THREADS'] = n_threads

    print("=" * 60)
    print(f"🚀 Concurrent Embedding Server on http://0.0.0.0:{PORT}")
    print(f"📡 Endpoint: http://localhost:{PORT}/v1/embeddings")
    print(f"👥 Concurrent Slots: 8 (can handle 8 users at once)")
    print(f"🧠 Model: {QUANT}")
    print("=" * 60)

    try:
        subprocess.run(cmd, check=False)
    except KeyboardInterrupt:
        print("\n✋ Shutting down...")

if __name__ == "__main__":
    main()
