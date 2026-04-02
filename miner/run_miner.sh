#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d .venv ]]; then
  echo "Missing .venv. Run ./miner/install.sh first."
  exit 1
fi

source .venv/bin/activate

WALLET_PATH="${HOME}/.alice/wallet.json"
HAS_ADDRESS=false
for arg in "$@"; do
  if [[ "$arg" == "--address" ]]; then
    HAS_ADDRESS=true
    break
  fi
done

if [[ "$HAS_ADDRESS" == false ]]; then
  if [[ ! -f "$WALLET_PATH" ]]; then
    python miner/alice_wallet.py create
  fi
  WALLET_ADDRESS="$(python - <<'PY'
import json
from pathlib import Path
path = Path.home() / ".alice" / "wallet.json"
print(json.loads(path.read_text())["address"])
PY
)"
  set -- --address "$WALLET_ADDRESS" "$@"
fi

exec python miner/alice_miner.py "$@"

