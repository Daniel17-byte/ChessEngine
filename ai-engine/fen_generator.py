import chess
import random
import json

PIECE_TYPES = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
MAX_ATTEMPTS = 10000  # încercări maxime pentru generarea FEN-urilor unice

def are_kings_non_adjacent(square1, square2):
    """Verificăm că regii nu sunt pe pătrate adiacente."""
    file_diff = abs(chess.square_file(square1) - chess.square_file(square2))
    rank_diff = abs(chess.square_rank(square1) - chess.square_rank(square2))
    return max(file_diff, rank_diff) > 1

# =========================
# Endgame generator
# =========================
def generate_random_endgame(max_pieces=4):
    """Generează o poziție aleatorie de endgame cu maxim max_pieces piese pe fiecare parte."""
    board = chess.Board(None)  # empty board

    # Plasăm regii
    while True:
        king_white = random.randint(0, 63)
        king_black = random.randint(0, 63)
        if king_white != king_black and are_kings_non_adjacent(king_white, king_black):
            break
    board.set_piece_at(king_white, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(king_black, chess.Piece(chess.KING, chess.BLACK))

    placed_squares = {king_white, king_black}

    # Plasăm piese adiționale
    for color in [chess.WHITE, chess.BLACK]:
        for _ in range(2):
            if len(placed_squares) >= max_pieces + 2:
                break
            piece_type = random.choice(PIECE_TYPES)
            for _ in range(100):
                square = random.randint(0, 63)
                if square not in placed_squares:
                    board.set_piece_at(square, chess.Piece(piece_type, color))
                    placed_squares.add(square)
                    break

    board.turn = random.choice([chess.WHITE, chess.BLACK])
    return board.fen()

def generate_endgames(n=1000, max_pieces=4):
    """Generează n FEN-uri unice de endgame."""
    fens = set()
    attempts = 0
    while len(fens) < n and attempts < MAX_ATTEMPTS:
        fen = generate_random_endgame(max_pieces)
        board = chess.Board(fen)
        if board.is_valid() and not board.is_check():
            fens.add(fen)
        attempts += 1
    return list(fens)

# =========================
# Game generator
# =========================
def generate_random_game(max_moves=40):
    """Generează un joc complet până la max_moves mutări."""
    board = chess.Board()
    fens = [board.fen()]

    for _ in range(max_moves):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            break
        move = random.choice(legal_moves)
        board.push(move)
        fens.append(board.fen())
        if board.is_game_over():
            break

    return fens

def generate_games(n_games=100, max_moves=40):
    """Generează n jocuri complete și returnează toate pozițiile FEN."""
    all_fens = set()
    attempts = 0
    while len(all_fens) < n_games and attempts < MAX_ATTEMPTS:
        game_fens = generate_random_game(max_moves)
        all_fens.update(game_fens)
        attempts += 1
    return list(all_fens)

# =========================
# Script principal
# =========================
if __name__ == "__main__":
    # Generăm endgames
    endgame_fens = generate_endgames(n=100000, max_pieces=6)
    with open("generated_endgames.json", "w") as f:
        json.dump(endgame_fens, f, indent=2)
    print(f"✅ Salvat {len(endgame_fens)} FEN-uri de endgame în 'generated_endgames.json'")

    # Generăm jocuri complete
    game_fens = generate_games(n_games=100000, max_moves=60)
    with open("generated_games.json", "w") as f:
        json.dump(game_fens, f, indent=2)
    print(f"✅ Salvat {len(game_fens)} FEN-uri din jocuri complete în 'generated_games.json'")
