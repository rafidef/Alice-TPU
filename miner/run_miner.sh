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
DEFAULT_PS_URL="${ALICE_PS_URL:-https://ps.aliceprotocol.org}"
HAS_ADDRESS=false
HAS_REWARD_ADDRESS=false
HAS_PS_URL=false
HAS_DEVICE=false
HAS_INSTANCE_ID=false
for arg in "$@"; do
  if [[ "$arg" == "--address" || "$arg" == --address=* ]]; then
    HAS_ADDRESS=true
  fi
  if [[ "$arg" == "--reward-address" || "$arg" == --reward-address=* ]]; then
    HAS_REWARD_ADDRESS=true
  fi
  if [[ "$arg" == "--ps-url" || "$arg" == --ps-url=* ]]; then
    HAS_PS_URL=true
  fi
  if [[ "$arg" == "--device" || "$arg" == --device=* ]]; then
    HAS_DEVICE=true
  fi
  if [[ "$arg" == "--instance-id" || "$arg" == --instance-id=* ]]; then
    HAS_INSTANCE_ID=true
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

if [[ "$HAS_REWARD_ADDRESS" == false ]]; then
  if [[ -z "${WALLET_ADDRESS:-}" ]]; then
    WALLET_ADDRESS="$(python - <<'PY'
import json
from pathlib import Path
path = Path.home() / ".alice" / "wallet.json"
print(json.loads(path.read_text())["address"])
PY
)"
  fi
  set -- --reward-address "$WALLET_ADDRESS" "$@"
fi

if [[ "$HAS_PS_URL" == false ]]; then
  set -- --ps-url "$DEFAULT_PS_URL" "$@"
fi

is_tpu_environment() {
  [[ "${PJRT_DEVICE:-}" == "TPU" || -n "${TPU_NAME:-}" || -n "${TPU_WORKER_HOSTNAMES:-}" || -n "${TPU_WORKER_ID:-}" || -n "${TPU_ACCELERATOR_TYPE:-}" || -n "${TPU_TYPE:-}" || -n "${ACCELERATOR_TYPE:-}" ]]
}

# Restrict to DNS-style hostnames before using host values in SSH commands.
is_safe_tpu_host() {
  [[ "$1" =~ ^([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(\.([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*$ ]]
}

trim_whitespace() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

resolve_tpu_host() {
  local raw="$1"
  local host
  host="$(trim_whitespace "${raw}")"
  if [[ -z "$host" ]]; then
    return 1
  fi
  if is_safe_tpu_host "$host"; then
    echo "$host"
    return 0
  fi
  if [[ "$host" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    local from_env="${!host:-}"
    from_env="$(trim_whitespace "${from_env}")"
    if [[ -n "$from_env" ]] && is_safe_tpu_host "$from_env"; then
      echo "$from_env"
      return 0
    fi
  fi
  return 1
}

sanitize_tpu_process_addresses() {
  local raw="${TPU_PROCESS_ADDRESSES:-}"
  if [[ -z "${raw//[[:space:]]/}" ]]; then
    return 0
  fi

  local entries=()
  local valid=()
  IFS=',' read -r -a entries <<< "$raw"
  for raw_entry in "${entries[@]}"; do
    local entry
    entry="$(trim_whitespace "${raw_entry}")"
    if [[ -z "$entry" ]]; then
      continue
    fi
    if [[ "${entry,,}" == "local" ]]; then
      echo "⚠️ Ignoring invalid TPU process address entry: ${entry}"
      continue
    fi
    if [[ "$entry" =~ ^([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(\.([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*:([0-9]{1,5})$ ]]; then
      local port
      port="${BASH_REMATCH[6]}"
      if (( port < 0 || port > 65535 )); then
        echo "⚠️ Ignoring invalid TPU process address entry: ${entry}"
        continue
      fi
      valid+=("$entry")
    else
      echo "⚠️ Ignoring invalid TPU process address entry: ${entry}"
    fi
  done

  if (( ${#valid[@]} == 0 )); then
    echo "⚠️ No valid TPU process addresses remained after sanitization; unsetting TPU_PROCESS_ADDRESSES"
    unset TPU_PROCESS_ADDRESSES || true
    return 0
  fi

  export TPU_PROCESS_ADDRESSES="$(IFS=, ; echo "${valid[*]}")"
}

is_tpu_runtime=false
if is_tpu_environment; then
  is_tpu_runtime=true
fi

if [[ "$is_tpu_runtime" == true ]]; then
  export PJRT_DEVICE="${PJRT_DEVICE:-TPU}"
  tpu_worker_id="${TPU_WORKER_ID:-0}"
  if [[ "$HAS_DEVICE" == false ]]; then
    set -- --device tpu "$@"
  fi
  if [[ "$HAS_INSTANCE_ID" == false ]]; then
    set -- --instance-id "tpu${tpu_worker_id}" "$@"
  fi

  tpu_hosts_raw="${TPU_WORKER_HOSTNAMES:-${ALICE_TPU_WORKERS:-}}"
  tpu_hosts=()
  tpu_hosts_sanitized=()
  if [[ -n "$tpu_hosts_raw" ]]; then
    IFS=',' read -r -a tpu_hosts <<< "$tpu_hosts_raw"
    for raw_host in "${tpu_hosts[@]}"; do
      if ! host="$(resolve_tpu_host "${raw_host}")"; then
        echo "⚠️ Skipping unsafe TPU host entry: $(trim_whitespace "${raw_host}")"
        continue
      fi
      tpu_hosts_sanitized+=("$host")
    done
  fi

  if (( ${#tpu_hosts_sanitized[@]} > 0 )); then
    tpu_hosts_csv="$(IFS=, ; echo "${tpu_hosts_sanitized[*]}")"
    export TPU_WORKER_HOSTNAMES="$tpu_hosts_csv"
    export ALICE_TPU_WORKERS="$tpu_hosts_csv"
    export TPU_WORKER_COUNT="${#tpu_hosts_sanitized[@]}"
  else
    if [[ -n "$tpu_hosts_raw" ]]; then
      echo "⚠️ No valid TPU hosts remained after sanitization; falling back to single-worker TPU mode"
    fi
    unset TPU_WORKER_HOSTNAMES || true
    unset ALICE_TPU_WORKERS || true
    export TPU_WORKER_COUNT=1
  fi

  sanitize_tpu_process_addresses

  if [[ "${ALICE_TPU_REMOTE_STARTED:-0}" != "1" && "${ALICE_TPU_DISABLE_REMOTE_START:-0}" != "1" && "${tpu_worker_id}" == "0" ]]; then
    if (( ${#tpu_hosts_sanitized[@]} > 1 )); then
      if command -v ssh >/dev/null 2>&1; then
        root_dir_escaped="$(printf '%q' "$ROOT_DIR")"
        for idx in "${!tpu_hosts_sanitized[@]}"; do
          if (( idx == 0 )); then
            continue
          fi
          host="${tpu_hosts_sanitized[$idx]}"
          printf -v remote_args_escaped '%q ' "$@"
          remote_instance_suffix="${idx}"
          remote_instance_id="tpu${remote_instance_suffix}"
          if [[ -z "$remote_instance_suffix" ]]; then
            echo "⚠️ Skipping worker with invalid index '${idx}'"
            continue
          fi
          remote_instance_escaped="$(printf '%q' "$remote_instance_id")"
          echo "[TPU] Starting remote worker ${idx} on ${host} (instance-id=${remote_instance_id})"
          if ! ssh -o BatchMode=yes -o ConnectTimeout=10 "$host" \
            "cd ${root_dir_escaped} && ALICE_TPU_REMOTE_STARTED=1 ALICE_TPU_DISABLE_REMOTE_START=1 PJRT_DEVICE=TPU nohup ./miner/run_miner.sh ${remote_args_escaped} --instance-id ${remote_instance_escaped} >/tmp/alice-miner-${remote_instance_escaped}.log 2>&1 < /dev/null &"; then
            echo "⚠️ Failed to start remote TPU worker on ${host}; continue running local coordinator"
          fi
        done
      else
        echo "⚠️ ssh is unavailable; cannot auto-start secondary TPU workers"
      fi
    fi
  fi
fi

exec python miner/alice_miner.py "$@"
