#!/usr/bin/env bash
# Local AI setup for Apple Silicon Macs (Mac Studio M5 Max, 64 GB target).
# Usage: bash scripts/setup-local-ai.sh [--with-webui] [--big]
#   --with-webui  also start Open WebUI in Docker (http://localhost:3000)
#   --big         also pull a ~70B-class model (needs ~45 GB free memory)
set -euo pipefail

WITH_WEBUI=0; BIG=0
for a in "$@"; do
  case "$a" in
    --with-webui) WITH_WEBUI=1 ;;
    --big) BIG=1 ;;
    *) echo "Unknown option: $a"; exit 1 ;;
  esac
done

say() { printf '\n==> %s\n' "$*"; }

# ---------- 1. System check ----------
say "Checking system"
[[ "$(uname -s)" == "Darwin" ]] || { echo "This script is for macOS."; exit 1; }
[[ "$(uname -m)" == "arm64" ]]  || { echo "Apple Silicon required."; exit 1; }

CHIP=$(sysctl -n machdep.cpu.brand_string)
MEM_GB=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
FREE_GB=$(df -g / | awk 'NR==2{print $4}')
echo "macOS : $(sw_vers -productVersion)"
echo "Chip  : $CHIP"
echo "Memory: ${MEM_GB} GB"
echo "Disk  : ${FREE_GB} GB free"

(( FREE_GB >= 60 )) || { echo "Need at least 60 GB free disk for models."; exit 1; }
if (( BIG )) && (( MEM_GB < 64 )); then
  echo "--big needs 64 GB memory; skipping the large model."; BIG=0
fi

# ---------- 2. Homebrew + Ollama (native, uses Metal GPU) ----------
say "Installing Ollama"
if ! command -v brew >/dev/null; then
  echo "Homebrew not found. Install it from https://brew.sh and re-run."; exit 1
fi
command -v ollama >/dev/null || brew install ollama
brew services start ollama >/dev/null 2>&1 || true

for _ in $(seq 1 30); do
  curl -sf http://localhost:11434/api/version >/dev/null && break
  sleep 1
done
curl -sf http://localhost:11434/api/version >/dev/null || { echo "Ollama did not start."; exit 1; }
echo "Ollama $(ollama --version | tail -1)"

# ---------- 3. Models (sized for 64 GB unified memory) ----------
# Names change often; verify at https://ollama.com/library and edit as needed.
MODELS=(
  "llama3.2"      # small and fast, ~2 GB, sanity test
  "qwen2.5:32b"   # strong general model, ~20 GB
)
(( BIG )) && MODELS+=("llama3.3:70b")   # ~43 GB, fits tightly on 64 GB

say "Pulling models"
for m in "${MODELS[@]}"; do
  echo "--- $m"
  ollama pull "$m" || echo "Could not pull $m (name may have changed); skipping."
done

# ---------- 4. Smoke test ----------
say "Smoke test"
ollama run llama3.2 "Reply with one short sentence confirming you are running locally." || true

# ---------- 5. Optional web UI ----------
if (( WITH_WEBUI )); then
  say "Starting Open WebUI"
  command -v docker >/dev/null || { echo "Install Docker Desktop first."; exit 1; }
  docker rm -f open-webui >/dev/null 2>&1 || true
  docker run -d --name open-webui --restart unless-stopped -p 3000:8080 \
    --add-host=host.docker.internal:host-gateway \
    -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    -v open-webui:/app/backend/data \
    ghcr.io/open-webui/open-webui:main
  echo "Open http://localhost:3000"
fi

say "Done. Chat with: ollama run qwen2.5:32b"
echo "API (OpenAI-compatible): http://localhost:11434/v1"
