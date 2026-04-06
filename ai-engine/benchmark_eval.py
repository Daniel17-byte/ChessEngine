import argparse
import random
import time

import chess

PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.2,
    chess.BISHOP: 3.3,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}
CENTER_SQUARES = {chess.D4, chess.D5, chess.E4, chess.E5}


def evaluate_board_python(board: chess.Board, is_white: bool) -> float:
    my_color = chess.WHITE if is_white else chess.BLACK
    if board.is_checkmate():
        return float("-inf") if board.turn == my_color else float("inf")

    value = 0.0
    for square, piece in board.piece_map().items():
        sign = 1.0 if piece.color == chess.WHITE else -1.0
        val = PIECE_VALUES[piece.piece_type]
        if square in CENTER_SQUARES:
            val += 0.1
        value += sign * val

    if board.is_check():
        value += 0.5 if board.turn != my_color else -0.5

    return value if is_white else -value


def build_positions(n: int, seed: int):
    random.seed(seed)
    boards = [chess.Board()]

    b = chess.Board()
    while len(boards) < n:
        if b.is_game_over():
            b = chess.Board()
        legal = list(b.legal_moves)
        if not legal:
            b = chess.Board()
            continue
        b.push(random.choice(legal))
        boards.append(b.copy(stack=False))

    return boards


def benchmark_eval(boards, is_white: bool, iterations: int, eval_fn, label: str):
    start = time.perf_counter()
    s = 0.0
    for _ in range(iterations):
        for b in boards:
            v = eval_fn(b, is_white)
            if v == float("inf"):
                s += 1000.0
            elif v == float("-inf"):
                s -= 1000.0
            else:
                s += v
    elapsed = time.perf_counter() - start
    calls = iterations * len(boards)
    print(f"{label}: calls={calls} time={elapsed:.4f}s eval/s={calls/max(elapsed,1e-9):.1f} checksum={s:.3f}")


def check_parity(boards, is_white: bool, eval_cy):
    for i, b in enumerate(boards):
        p = evaluate_board_python(b, is_white)
        c = eval_cy(b, is_white)
        if p == c:
            continue
        if abs(p - c) > 1e-9:
            raise AssertionError(f"Parity failed at index={i}: python={p}, cython={c}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Chess evaluation Python vs Cython")
    parser.add_argument("--positions", type=int, default=300)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--is-white", action="store_true", default=False)
    args = parser.parse_args()

    boards = build_positions(args.positions, args.seed)
    benchmark_eval(boards, args.is_white, args.iterations, evaluate_board_python, "python")

    try:
        from fastgame.game_eval import evaluate_board as evaluate_board_cython
        check_parity(boards, args.is_white, evaluate_board_cython)
        benchmark_eval(boards, args.is_white, args.iterations, evaluate_board_cython, "cython")
    except ImportError:
        print("cython: module not available (build with: python setup_cython.py build_ext --inplace)")

