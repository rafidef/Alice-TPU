# Alice Miner

This is the standalone miner client for Alice Protocol.

Current access policy:
- repository is private
- outside miner admission remains restricted

## Quick Start

### macOS / Linux

```bash
cd miner
./install.sh
./run_miner.sh --ps-url https://ps.aliceprotocol.org
```

### Windows

```powershell
cd miner
.\install.ps1
.\run_miner.bat --ps-url https://ps.aliceprotocol.org
```

## Wallet

Create a local wallet:

```bash
python3 miner/alice_wallet.py create
```

Use an existing reward address:

```bash
python3 miner/alice_miner.py \
  --ps-url https://ps.aliceprotocol.org \
  --address aYourAliceAddress \
  --reward-address aYourRewardAddress
```

## Hardware

See `docs/HARDWARE_REQUIREMENTS.md` for the full matrix.

Summary:
- CUDA GPU `>= 24GB`: recommended
- Apple Silicon `>= 24GB`: supported
- CPU `>= 32GB RAM`: supported but very slow
- `< 20GB`: not supported

