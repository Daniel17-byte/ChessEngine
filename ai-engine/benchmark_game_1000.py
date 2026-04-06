import argparse
import random
import time

import chess

from Game import Game


def run_benchmark(num_games: int, max_moves: int, seed: int):
    random.seed(seed)
    total_moves = 0

    game = Game()
    start = time.perf_counter()

    for _ in range(num_games):
        game.reset()
        moves = 0

        while not game.is_game_over() and moves < max_moves:
            legal_moves = list(game.board.legal_moves)
            if not legal_moves:
                break
            move = random.choice(legal_moves)
            ok, _ = game.make_move(move.uci())
            if not ok:
                break
            moves += 1

        total_moves += moves

    elapsed = time.perf_counter() - start
    print(f"games={num_games} moves={total_moves} time={elapsed:.4f}s games/s={num_games/elapsed:.2f} moves/s={total_moves/elapsed:.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark sequential game speed through Game.make_move")
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--max-moves", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_benchmark(args.games, args.max_moves, args.seed)

