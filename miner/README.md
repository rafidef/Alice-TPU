# Alice Miner

Standalone miner runtime for Alice Protocol.

## Default Mode

`Plan B` is the default runtime.

Start a miner with:

```bash
./miner/bootstrap.sh --ps-url https://ps.aliceprotocol.org --address YOUR_ADDRESS
```

or directly:

```bash
python3 miner/alice_miner.py --ps-url https://ps.aliceprotocol.org --address YOUR_ADDRESS
```

Legacy Plan A is still available but deprecated:

```bash
python3 miner/alice_miner.py --ps-url https://ps.aliceprotocol.org --address YOUR_ADDRESS --mode plan_a
```

## Batch Assignment

The network assigns a batch-size cap based on VRAM. The miner must train at or below that cap.

- default behavior: use the assigned batch size from the task
- manual `--batch-size`: allowed only as a lower cap
- manual overrides never increase rewards

Reference matrix:

| VRAM | Assigned Batch Size | Tokens per Shard |
|------|---------------------|------------------|
| 16GB | 1                   | 10,240           |
| 24GB | 4                   | 40,960           |
| 32GB | 8                   | 81,920           |
| 48GB | 16                  | 163,840          |
| 80GB | 32                  | 327,680          |

## Rewards

```text
effective_tokens = completed_shards * assigned_batch_size
tokens_trained = effective_tokens * 10240
reward_share = your_effective_tokens / total_network_effective_tokens
```

Rewards are based on effective tokens. If the miner is forced to downshift batch locally for stability, logs should be reviewed before treating that epoch as production-ready.

## Long-Running Operation

Foreground bootstrap is fine for setup and debugging. For long-running use:

- `./miner/install-service.sh`
- `./miner/start-service.sh`
- `./miner/stop-service.sh`
- `./miner/status-service.sh`

Or run in the background:

```bash
nohup ./miner/run_miner.sh \
  --ps-url https://ps.aliceprotocol.org \
  --address YOUR_ADDRESS \
  > /tmp/miner.log 2>&1 &
```

## Multi-GPU

Use one process per GPU and a unique `--instance-id` per process:

```bash
CUDA_VISIBLE_DEVICES=0 ./miner/bootstrap.sh \
  --ps-url https://ps.aliceprotocol.org \
  --address YOUR_ADDRESS \
  --instance-id gpu0

CUDA_VISIBLE_DEVICES=1 ./miner/run_miner.sh \
  --ps-url https://ps.aliceprotocol.org \
  --address YOUR_ADDRESS \
  --instance-id gpu1
```

## TPU (single VM and multi-host)

Use a TPU-oriented instance id:

```bash
./miner/bootstrap.sh \
  --ps-url https://ps.aliceprotocol.org \
  --address YOUR_ADDRESS \
  --reward-address YOUR_REWARD_ADDRESS \
  --instance-id tpu0
```

On TPU VMs, `run_miner.sh` auto-detects TPU runtime, sets `--device tpu` when missing, and defaults the instance id to `tpu${TPU_WORKER_ID}` when not provided.

For multi-host TPU slices, start only on VM-0. If `TPU_WORKER_HOSTNAMES` (or `ALICE_TPU_WORKERS`) lists multiple hosts, VM-0 will try to start workers on the remaining hosts over SSH automatically.

## Wallet

Create a wallet:

```bash
python3 miner/alice_wallet.py create
```

If `--address` is omitted, the bootstrap flow will create or reuse `~/.alice/wallet.json`.

## Notes

- Plan B refreshes stale local models automatically.
- If a local model is more than 5 versions behind, the miner downloads a fresh full model.
- `~/.alice/plan_b_models/current_version` tracks the miner's current local Plan B model version.
