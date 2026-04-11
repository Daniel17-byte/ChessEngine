# Training Engine Fast Path

This training-only path decouples self-play from API game payload logic.

## What changed

- Added `TrainingGame` in `TrainingGame.py`.
- `MirrorMatch.py` now uses `TrainingGame` for self-play loops.
- Self-play move application uses `make_move_fast(...)` (minimal validation + push).
- Draw-claim checks are disabled in training loop game-over/result checks for speed.

## Why

Training throughput is limited by per-move overhead. The training loop only needs:

- a legal move application,
- game termination check,
- final result string.

Everything else is unnecessary overhead for self-play generation.

## Quick smoke test

```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/ai-engine
source venv/bin/activate
python training_fast_smoke.py
```

## Run mirror training

```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/ai-engine
source venv/bin/activate
python MirrorMatch.py --epochs 1 --games-per-epoch 20 --max-moves 80 --white-strategy model --black-strategy model --fen-type endgames
```

## Also applied to ArchiveAlpha

`ArchiveAlpha.py` now supports a training throughput mode:

- default mode is `--training-only` (skip accuracy metric computation in batch loop),
- optional `--full-metrics` keeps full accuracy stats.

This means both training pipelines are optimized:

- `MirrorMatch.py` -> fast `TrainingGame` self-play,
- `ArchiveAlpha.py` -> fast metric-light training loop.
