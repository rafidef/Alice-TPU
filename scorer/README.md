# Alice Scorer

This is the standalone scorer worker for Alice Protocol.

Current access policy:
- repository is private
- external scorer operations are still coordinated manually

## Quick Start

```bash
python3 scorer/scoring_server.py \
  --model-path /path/to/current_full.pt \
  --validation-dir /path/to/validation \
  --host 0.0.0.0 \
  --port 8090 \
  --device cpu \
  --model-dtype auto \
  --num-val-shards 5 \
  --ps-url https://ps.aliceprotocol.org
```

## Platform Defaults

- Linux x86 `>= 32GB RAM`: `float32`
- Linux x86 `24-32GB RAM`: `float16` fallback, slower
- Mac ARM `>= 24GB unified memory`: `float16`
- Windows `>= 32GB RAM`: experimental, `float32`

## Chain Flow

1. Fund scorer address
2. Stake `5000 ALICE`
3. Activate scorer
4. Add scorer endpoint to aggregator pool
5. Confirm `/health` and first scored request

Current scorer reward pool: `6%`

