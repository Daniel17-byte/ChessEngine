"""
Pre-compute Stockfish best moves for all FEN positions.
Run this ONCE, then stockfish_trainer.py uses the cached results.

Usage:
    python precompute_stockfish.py [--time-limit 0.05] [--input generated_games.json] [--output stockfish_labels.json]
"""
import os
import sys
import json
import argparse
import chess
import chess.engine


def main():
    parser = argparse.ArgumentParser(description='Pre-compute Stockfish labels for training')
    parser.add_argument('--input', default='generated_games.json', help='Input FEN file')
    parser.add_argument('--output', default='stockfish_labels.json', help='Output labels file')
    parser.add_argument('--time-limit', type=float, default=0.05, help='Stockfish time per move (seconds)')
    parser.add_argument('--engine-path', default='/opt/homebrew/bin/stockfish', help='Path to Stockfish binary')
    parser.add_argument('--resume', action='store_true', help='Resume from existing partial output')
    args = parser.parse_args()

    # Load FENs
    if not os.path.exists(args.input):
        print(f"❌ Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, 'r') as f:
        fens = json.load(f)
    print(f"📋 Loaded {len(fens)} FEN positions from {args.input}")

    # Load existing results if resuming
    results = {}
    if args.resume and os.path.exists(args.output):
        with open(args.output, 'r') as f:
            results = json.load(f)
        print(f"♻️ Resuming: {len(results)} already computed")

    # Start Stockfish
    if not os.path.exists(args.engine_path):
        print(f"❌ Stockfish not found at {args.engine_path}")
        sys.exit(1)

    engine = chess.engine.SimpleEngine.popen_uci(args.engine_path)
    print(f"♟️ Stockfish started (time limit: {args.time_limit}s per position)")

    total = len(fens)
    skipped = 0
    errors = 0

    try:
        for i, fen in enumerate(fens):
            # Skip already computed
            if fen in results:
                skipped += 1
                continue

            try:
                board = chess.Board(fen)
                if board.is_game_over():
                    results[fen] = None  # No move for finished games
                    continue

                result = engine.play(board, chess.engine.Limit(time=args.time_limit))
                if result.move:
                    results[fen] = result.move.uci()
                else:
                    results[fen] = None
            except Exception as e:
                results[fen] = None
                errors += 1

            # Progress report every 1000
            if (i + 1) % 1000 == 0:
                computed = len(results) - skipped
                pct = (i + 1) / total * 100
                print(f"  Progress: {i+1}/{total} ({pct:.1f}%) | Computed: {computed} | Errors: {errors}")
                sys.stdout.flush()

            # Save checkpoint every 10000
            if (i + 1) % 10000 == 0:
                with open(args.output, 'w') as f:
                    json.dump(results, f)
                print(f"  💾 Checkpoint saved ({len(results)} entries)")
                sys.stdout.flush()

    except KeyboardInterrupt:
        print(f"\n⚠️ Interrupted! Saving progress...")
    finally:
        engine.quit()

    # Save final results
    with open(args.output, 'w') as f:
        json.dump(results, f)

    valid = sum(1 for v in results.values() if v is not None)
    print(f"\n✅ Done! {valid} valid labels saved to {args.output}")
    print(f"   Total FENs: {total} | Computed: {len(results)} | Errors: {errors}")


if __name__ == '__main__':
    main()

