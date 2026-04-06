import argparse
import time

import chess

import ArchiveAlpha


def main():
    parser = argparse.ArgumentParser(description="Benchmark ArchiveAlpha encode_board backend")
    parser.add_argument("--iters", type=int, default=20000)
    args = parser.parse_args()

    board = chess.Board()

    # Warmup call
    tensor = ArchiveAlpha.encode_board(board)
    checksum = float(tensor.sum())

    start = time.perf_counter()
    for _ in range(args.iters):
        t = ArchiveAlpha.encode_board(board)
        checksum += float(t[0, 0, 0])
    elapsed = time.perf_counter() - start

    print(
        f"backend(cython={ArchiveAlpha.HAS_CYTHON_ENCODE}, numba={ArchiveAlpha.HAS_NUMBA}) "
        f"iters={args.iters} time={elapsed:.4f}s calls/s={args.iters/max(elapsed,1e-9):.1f} checksum={checksum:.3f}"
    )


if __name__ == "__main__":
    main()

