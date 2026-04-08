# Google Jules Agent Brief for Alice-TPU

## Objective
Add TPU compatibility to this miner fork so it can run on:
- single-VM TPU setups (for example `v5litepod-1`, `v5litepod-4`)
- multi-host TPU setups (for example `v5litepod-8`, 2 VMs) where the miner is started only on VM-0 and VM-0 initializes VM-1 automatically

## Existing default miner command (current GPU-named instance ID)
```bash
./miner/bootstrap.sh --ps-url https://ps.aliceprotocol.org --address a2x49BLY9JUxmsU8pdFet7w4Bb2KVkZ9DJbmXb91jjcZzdzHZ --reward-address a2x49BLY9JUxmsU8pdFet7w4Bb2KVkZ9DJbmXb91jjcZzdzHZ --instance-id gpu0
```

## Target behavior
1. Keep GPU/CPU behavior unchanged.
2. Add TPU runtime detection and TPU-safe startup path.
3. Support single-host TPU training.
4. Support multi-host TPU initialization from VM-0 (coordinator) without manually starting miner on VM-1.
5. Keep miner identity and reward flags compatible with current CLI behavior.

## Constraints
- Make minimal, focused changes.
- Reuse existing scripts/entrypoints where possible (`miner/bootstrap.sh`, `miner/run_miner.sh`, `miner/alice_miner.py`).
- Do not break existing tests.
- Preserve backward compatibility for current users.

## Validation
Run existing unit tests:
```bash
python3 -m unittest discover -s tests -p 'test*.py'
python3 -m unittest discover -s miner -p 'test*.py'
python3 -m unittest discover -s docs/vps3_download_queue -p 'test*.py'
```

## Initial command for Google Jules
Use this as the initial task command/prompt in Jules:

```text
Implement TPU compatibility for this repository so the miner supports single-VM TPU (v5litepod-1/v5litepod-4) and multi-host TPU (v5litepod-8 with 2 VMs) where miner runs only on VM-0 and VM-0 initializes VM-1. Keep existing GPU behavior unchanged. Use a TPU-oriented instance ID. Start from: ./miner/bootstrap.sh --ps-url https://ps.aliceprotocol.org --address a2x49BLY9JUxmsU8pdFet7w4Bb2KVkZ9DJbmXb91jjcZzdzHZ --reward-address a2x49BLY9JUxmsU8pdFet7w4Bb2KVkZ9DJbmXb91jjcZzdzHZ --instance-id tpu0
```
