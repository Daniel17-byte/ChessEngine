import random

import chess

from TrainingGame import TrainingGame


def run_smoke(max_plies: int = 200):
    game = TrainingGame()
    plies = 0

    while not game.is_game_over() and plies < max_plies:
        legal = list(game.board.legal_moves)
        if not legal:
            break
        mv = random.choice(legal)
        ok, _ = game.make_move_fast(mv)
        if not ok:
            raise RuntimeError(f"fast move rejected unexpectedly at ply {plies}: {mv.uci()}")
        plies += 1

    print(f"smoke_ok plies={plies} result={game.get_result()}")


if __name__ == "__main__":
    run_smoke()

