#!/usr/bin/env python3
"""
Comprehensive chess engine benchmark – 1000 games.

Tests:
  1. Raw random games (pure python-chess speed)
  2. TrainingGame random games (training loop overhead)
  3. Board encoding speed (Cython vs Python)
  4. Board evaluation speed (Cython vs Python)
  5. Full Game class (API path)

Usage:
    python benchmark_game_1000.py                    # default 1000 games
    python benchmark_game_1000.py --games 500        # custom count
    python benchmark_game_1000.py --profile           # with cProfile top-10
    python benchmark_game_1000.py --compare            # side-by-side Python vs Cython
"""
import argparse
import random
import time
import chess


# ═══════════════════════════════════════════════════════════════════════════════
#  Benchmark helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _play_random_games_raw(num_games, max_moves, rng):
    """Raw python-chess: board.push(random_move) — no wrapper overhead."""
    total_moves = 0
    results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}
    for _ in range(num_games):
        board = chess.Board()
        moves = 0
        while not board.is_game_over() and moves < max_moves:
            legal = list(board.legal_moves)
            if not legal:
                break
            board.push(rng.choice(legal))
            moves += 1
        total_moves += moves
        r = board.result()
        results[r] = results.get(r, 0) + 1
    return total_moves, results


def _play_random_games_training(num_games, max_moves, rng):
    """Through TrainingGame class — measures training loop overhead."""
    from TrainingGame import TrainingGame
    game = TrainingGame()
    total_moves = 0
    results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}
    for _ in range(num_games):
        game.reset()
        moves = 0
        while not game.is_game_over() and moves < max_moves:
            legal = list(game.board.legal_moves)
            if not legal:
                break
            move = rng.choice(legal)
            ok, _ = game.make_move_fast(move)
            if not ok:
                break
            moves += 1
        total_moves += moves
        r = game.get_result()
        results[r] = results.get(r, 0) + 1
    return total_moves, results


def _play_random_games_full(num_games, max_moves, rng):
    """Through full Game class — measures API-level overhead."""
    from Game import Game
    game = Game()
    total_moves = 0
    results = {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}
    for _ in range(num_games):
        game.reset()
        moves = 0
        while not game.is_game_over() and moves < max_moves:
            legal = list(game.board.legal_moves)
            if not legal:
                break
            move = rng.choice(legal)
            ok, _ = game.make_move_fast(move)
            if not ok:
                break
            moves += 1
        total_moves += moves
        r = game.get_result()
        results[r] = results.get(r, 0) + 1
    return total_moves, results


def _bench_encoding(num_boards):
    """Benchmark board encoding speed."""
    boards = []
    rng = random.Random(123)
    for _ in range(num_boards):
        b = chess.Board()
        for _ in range(rng.randint(5, 40)):
            legal = list(b.legal_moves)
            if not legal or b.is_game_over():
                break
            b.push(rng.choice(legal))
        boards.append(b.copy())

    results = {}

    # Python encoding
    from ArchiveAlpha import _encode_board_numpy
    t0 = time.perf_counter()
    for b in boards:
        _encode_board_numpy(b)
    t_py = time.perf_counter() - t0
    results["python_numpy"] = t_py

    # Cython encoding
    try:
        from fastgame.board_encode import encode_board_array as cy_enc
        t0 = time.perf_counter()
        for b in boards:
            cy_enc(b)
        t_cy = time.perf_counter() - t0
        results["cython_single"] = t_cy
    except ImportError:
        results["cython_single"] = None

    # Cython batch encoding
    try:
        from fastgame.board_encode import encode_board_batch as cy_batch
        t0 = time.perf_counter()
        cy_batch(boards)
        t_batch = time.perf_counter() - t0
        results["cython_batch"] = t_batch
    except ImportError:
        results["cython_batch"] = None

    return results, len(boards)


def _bench_eval(num_boards):
    """Benchmark board evaluation speed."""
    boards = []
    rng = random.Random(456)
    for _ in range(num_boards):
        b = chess.Board()
        for _ in range(rng.randint(5, 40)):
            legal = list(b.legal_moves)
            if not legal or b.is_game_over():
                break
            b.push(rng.choice(legal))
        boards.append(b.copy())

    results = {}

    # Python eval
    from ChessAI import PIECE_VALUES, CENTER_SQUARES
    def py_eval(board):
        value = 0.0
        for square, piece in board.piece_map().items():
            sign = 1.0 if piece.color == chess.WHITE else -1.0
            val = PIECE_VALUES.get(piece.piece_type, 0.0)
            if square in CENTER_SQUARES:
                val += 0.1
            value += sign * val
        return value

    t0 = time.perf_counter()
    for b in boards:
        py_eval(b)
    t_py = time.perf_counter() - t0
    results["python"] = t_py

    # Cython eval
    try:
        from fastgame.game_eval import evaluate_board as cy_eval
        t0 = time.perf_counter()
        for b in boards:
            cy_eval(b, True)
        t_cy = time.perf_counter() - t0
        results["cython"] = t_cy
    except ImportError:
        results["cython"] = None

    return results, len(boards)


# ═══════════════════════════════════════════════════════════════════════════════
#  Main benchmark runner
# ═══════════════════════════════════════════════════════════════════════════════

def run_benchmark(num_games, max_moves, seed, compare=False, profile=False):
    rng = random.Random(seed)
    separator = "─" * 72

    print(f"\n{'═' * 72}")
    print(f"  CHESS ENGINE BENCHMARK — {num_games} games, max {max_moves} moves/game")
    print(f"  Seed: {seed}")
    print(f"{'═' * 72}\n")

    all_results = []

    # ── Test 1: Raw python-chess ─────────────────────────────────────────
    print(f"[1/5] Raw python-chess (board.push random moves)...")
    rng_copy = random.Random(seed)
    t0 = time.perf_counter()
    total_moves, results = _play_random_games_raw(num_games, max_moves, rng_copy)
    t1 = time.perf_counter() - t0
    gps = num_games / t1
    mps = total_moves / t1
    avg_moves = total_moves / num_games
    print(f"      {num_games} games | {total_moves} moves | {t1:.3f}s")
    print(f"      {gps:.1f} games/s | {mps:.0f} moves/s | avg {avg_moves:.1f} moves/game")
    print(f"      Results: W={results.get('1-0',0)} B={results.get('0-1',0)} D={results.get('1/2-1/2',0)}")
    all_results.append(("Raw python-chess", gps, mps, t1))
    print(separator)

    # ── Test 2: TrainingGame ─────────────────────────────────────────────
    print(f"[2/5] TrainingGame (training loop path)...")
    rng_copy = random.Random(seed)
    t0 = time.perf_counter()
    total_moves, results = _play_random_games_training(num_games, max_moves, rng_copy)
    t2 = time.perf_counter() - t0
    gps2 = num_games / t2
    mps2 = total_moves / t2
    print(f"      {num_games} games | {total_moves} moves | {t2:.3f}s")
    print(f"      {gps2:.1f} games/s | {mps2:.0f} moves/s")
    overhead = ((t2 / t1) - 1) * 100 if t1 > 0 else 0
    print(f"      Overhead vs raw: {overhead:+.1f}%")
    all_results.append(("TrainingGame", gps2, mps2, t2))
    print(separator)

    # ── Test 3: Full Game class ──────────────────────────────────────────
    print(f"[3/5] Full Game class (API path)...")
    rng_copy = random.Random(seed)
    t0 = time.perf_counter()
    total_moves, results = _play_random_games_full(num_games, max_moves, rng_copy)
    t3 = time.perf_counter() - t0
    gps3 = num_games / t3
    mps3 = total_moves / t3
    print(f"      {num_games} games | {total_moves} moves | {t3:.3f}s")
    print(f"      {gps3:.1f} games/s | {mps3:.0f} moves/s")
    overhead = ((t3 / t1) - 1) * 100 if t1 > 0 else 0
    print(f"      Overhead vs raw: {overhead:+.1f}%")
    all_results.append(("Full Game", gps3, mps3, t3))
    print(separator)

    # ── Test 4: Board Encoding ───────────────────────────────────────────
    num_encode = min(num_games * 10, 10000)
    print(f"[4/5] Board encoding ({num_encode} boards)...")
    enc_results, n_boards = _bench_encoding(num_encode)
    for name, t in enc_results.items():
        if t is not None:
            bps = n_boards / t
            print(f"      {name:20s}: {t:.3f}s ({bps:.0f} boards/s)")
        else:
            print(f"      {name:20s}: NOT AVAILABLE")

    if enc_results.get("cython_single") and enc_results.get("python_numpy"):
        speedup = enc_results["python_numpy"] / enc_results["cython_single"]
        print(f"      Cython speedup: {speedup:.2f}x")
    if enc_results.get("cython_batch") and enc_results.get("python_numpy"):
        speedup = enc_results["python_numpy"] / enc_results["cython_batch"]
        print(f"      Batch speedup:  {speedup:.2f}x")
    print(separator)

    # ── Test 5: Board Evaluation ─────────────────────────────────────────
    num_eval = min(num_games * 10, 10000)
    print(f"[5/5] Board evaluation ({num_eval} boards)...")
    eval_results, n_eval = _bench_eval(num_eval)
    for name, t in eval_results.items():
        if t is not None:
            bps = n_eval / t
            print(f"      {name:20s}: {t:.3f}s ({bps:.0f} evals/s)")
        else:
            print(f"      {name:20s}: NOT AVAILABLE")

    if eval_results.get("cython") and eval_results.get("python"):
        speedup = eval_results["python"] / eval_results["cython"]
        print(f"      Cython speedup: {speedup:.2f}x")
    print(separator)

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'═' * 72}")
    print(f"  SUMMARY")
    print(f"{'═' * 72}")
    print(f"  {'Test':<25s} {'Games/s':>10s} {'Moves/s':>12s} {'Time':>10s}")
    print(f"  {'─'*25} {'─'*10} {'─'*12} {'─'*10}")
    for name, gps, mps, t in all_results:
        print(f"  {name:<25s} {gps:>10.1f} {mps:>12.0f} {t:>9.3f}s")
    print(f"{'═' * 72}\n")

    # ── Optional: cProfile ───────────────────────────────────────────────
    if profile:
        import cProfile
        import pstats
        print(f"\n  Profiling {num_games} raw games...\n")
        prof = cProfile.Profile()
        rng_copy = random.Random(seed)
        prof.enable()
        _play_random_games_raw(num_games, max_moves, rng_copy)
        prof.disable()
        stats = pstats.Stats(prof)
        stats.sort_stats('cumulative')
        stats.print_stats(15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comprehensive chess engine benchmark")
    parser.add_argument("--games", type=int, default=1000, help="Number of games to play")
    parser.add_argument("--max-moves", type=int, default=200, help="Max moves per game")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--compare", action="store_true", help="Compare Python vs Cython side-by-side")
    parser.add_argument("--profile", action="store_true", help="Run cProfile on raw games")
    args = parser.parse_args()

    run_benchmark(args.games, args.max_moves, args.seed, args.compare, args.profile)
