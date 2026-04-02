# Alice Protocol

Private release-prep repository for the public Alice miner and scorer distribution.

This repository is the staged public candidate for:
- `miner/`: external miner client
- `scorer/`: external scorer worker
- `shared/`: shared Alice model runtime

Current status:
- private only
- external miner access remains restricted
- documentation is being aligned with the live mainnet implementation

## Repository Layout

```text
Alice-Protocol/
├── miner/
├── scorer/
├── shared/
├── core/
├── docs/
└── LICENSE
```

## Components

### Miner

Entry point: `miner/alice_miner.py`

Quick start:

```bash
cd miner
./install.sh
./run_miner.sh --ps-url https://ps.aliceprotocol.org
```

### Scorer

Entry point: `scorer/scoring_server.py`

Quick start:

```bash
python3 scorer/scoring_server.py \
  --model-path /path/to/current_full.pt \
  --validation-dir /path/to/validation \
  --host 0.0.0.0 \
  --port 8090 \
  --device cpu \
  --model-dtype auto \
  --ps-url https://ps.aliceprotocol.org
```

## Documentation

- `docs/MINER_GUIDE.md`
- `docs/MINER_GUIDE_CN.md`
- `docs/SCORER_GUIDE.md`
- `docs/HARDWARE_REQUIREMENTS.md`

## Notes

- This repository is not public yet.
- Network admission for outside miners remains restricted.
- Hardware guidance and scripts are included now; full cross-platform validation remains a release gate before public launch.

