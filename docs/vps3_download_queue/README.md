# VPS3 Download Queue

This directory contains the deployment artifacts for the VPS3 full-model download queue.

Files:
- `queue_core.py`: in-memory FIFO queue manager with lease-based active slots
- `queue_server.py`: Flask app exposing queue APIs and nginx `auth_request` verification
- `requirements.txt`: Python packages for the queue service host
- `alice-download-queue.service`: single-worker systemd unit using `gunicorn`
- `alice-data.nginx.conf`: nginx server block fragment for `dl.aliceprotocol.org`
- `test_queue_core.py`: stdlib unit tests for the queue state machine

Deployment notes:
- Only `v*_full.pt` downloads are queue-protected.
- Layer exports, shards, and epoch updates stay unchanged.
- Queue state is intentionally in-memory. A queue-service restart clears outstanding tickets; miners rejoin automatically when they receive `not_found`.
- The nginx config is fail-open for auth backend outages: if `/internal/auth/verify` returns 5xx or times out, the static full-model file is served directly.
- `/models/queue/status` is intentionally localhost-only in v1. Check it from the VPS itself, or via `ssh root@vps3 'curl http://127.0.0.1:8095/models/queue/status'`.

Suggested rollout:
1. Copy this directory to `/root/alice-download-queue`.
2. Create a venv with `python3 -m venv /root/alice-download-queue/.venv`.
3. Install dependencies with `/root/alice-download-queue/.venv/bin/pip install -r requirements.txt`.
4. Add `limit_conn_zone $binary_remote_addr zone=per_ip:10m;` to `/etc/nginx/nginx.conf` inside the global `http {}` block.
5. Install `alice-download-queue.service`, then `systemctl enable --now alice-download-queue`.
6. Validate local health with `curl http://127.0.0.1:8095/health`.
7. Validate local queue status with `curl http://127.0.0.1:8095/models/queue/status`.
8. Install the nginx fragment updates, run `nginx -t`, then reload nginx.
