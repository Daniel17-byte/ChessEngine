import argparse
import time
import chess

from ArchiveAlpha import encode_board
from ChessAI import ChessAI


def bench_encode(iterations: int):
    board = chess.Board()
    start = time.perf_counter()
    for _ in range(iterations):
        _ = encode_board(board)
    elapsed = time.perf_counter() - start
    print(f"encode_board: {iterations} calls in {elapsed:.4f}s ({iterations / max(elapsed, 1e-9):.1f} calls/s)")


def bench_model_move(iterations: int, depth: int):
    ai = ChessAI(is_white=True, default_strategy="model")
    board = chess.Board()

    # Warmup
    _ = ai.get_best_move_from_model(board, depth=depth)

    start = time.perf_counter()
    for _ in range(iterations):
        _ = ai.get_best_move_from_model(board, depth=depth)
    elapsed = time.perf_counter() - start
    print(f"model_move(depth={depth}): {iterations} calls in {elapsed:.4f}s ({1000.0 * elapsed / iterations:.2f} ms/call)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quick local speed benchmark for ai-engine")
    parser.add_argument("--encode-iters", type=int, default=2000)
    parser.add_argument("--move-iters", type=int, default=20)
    parser.add_argument("--depth", type=int, default=2)
    args = parser.parse_args()

    bench_encode(args.encode_iters)
    bench_model_move(args.move_iters, args.depth)

