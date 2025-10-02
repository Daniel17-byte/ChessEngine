import chess
import json

def generate_legal_moves_from_fens(
        game_fens_path="generated_games.json",
        endgame_fens_path="generated_endgames.json",
        output_path="move_mapping.json"
):
    all_legal_moves = set()

    # Încarcă FEN-uri din jocuri complete
    with open(game_fens_path, "r") as f:
        game_fens = json.load(f)
    for fen in game_fens:
        board = chess.Board(fen)
        for move in board.legal_moves:
            all_legal_moves.add(move.uci())

    # Încarcă FEN-uri din endgames
    with open(endgame_fens_path, "r") as f:
        endgame_fens = json.load(f)
    for fen in endgame_fens:
        board = chess.Board(fen)
        for move in board.legal_moves:
            all_legal_moves.add(move.uci())

    # Salvăm mutările legale unice
    idx_to_move = sorted(list(all_legal_moves))
    with open(output_path, "w") as f:
        json.dump(idx_to_move, f, indent=2)

    print(f"✅ Salvat {len(idx_to_move)} mutări legale în '{output_path}'")

if __name__ == "__main__":
    generate_legal_moves_from_fens()
