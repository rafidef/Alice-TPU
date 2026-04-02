# Alice Miner Guide

This guide reflects the current standalone miner layout in `Alice-Protocol`.

Current rollout state:
- repository is private
- outside miner admission remains restricted

## 1. Install

macOS / Linux:

```bash
cd miner
./install.sh
```

Windows:

```powershell
cd miner
.\install.ps1
```

## 2. Create or import an address

Create a new local wallet:

```bash
python3 miner/alice_wallet.py create
```

If you already have an Alice address, you can pass it directly with `--address`.

## 3. Start mining

```bash
python3 miner/alice_miner.py \
  --ps-url https://ps.aliceprotocol.org \
  --address aYourAliceAddress \
  --device auto \
  --precision auto
```

Optional:

```bash
python3 miner/alice_miner.py \
  --ps-url https://ps.aliceprotocol.org \
  --address aControlAddress \
  --reward-address aRewardAddress
```

## 4. Network flow

The miner talks directly to the Parameter Server:
- `/register`
- `/task/request`
- `/task/complete`
- `/model`
- `/model/info`
- `/model/delta`

It does **not** connect directly to the aggregator.

## 5. Hardware guidance

- CUDA GPU `>= 24GB`: recommended
- Apple Silicon `>= 24GB`: supported
- CPU `>= 32GB RAM`: supported but very slow
- `< 20GB`: not supported

CPU mining is supported but not recommended.

## 6. Rewards

Rewards are paid to:
- `--reward-address` if provided
- otherwise `--address`

Reward timing depends on successful epoch settlement on chain.

## 7. Current release note

This repository is a private release-prep baseline. Cross-platform validation is still in progress before public access opens.

