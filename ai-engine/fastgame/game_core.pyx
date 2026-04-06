# cython: language_level=3
import chess

PIECE_VALUES = {'p': 1.0, 'n': 3.0, 'b': 3.0, 'r': 5.0, 'q': 9.0, 'k': 0.0}
CENTER_SQUARES = (chess.E4, chess.D4, chess.E5, chess.D5)


def auto_promote_if_needed(board, move_uci):
    if move_uci is None or len(move_uci) != 4:
        return move_uci

    from_sq = chess.parse_square(move_uci[:2])
    to_sq = chess.parse_square(move_uci[2:4])
    piece = board.piece_at(from_sq)
    if piece and piece.piece_type == chess.PAWN:
        if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
           (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
            return move_uci + 'q'
    return move_uci


def calculate_reward(board, move, captured_piece):
    cdef double reward = -0.01

    if captured_piece is not None:
        num_pieces = len(board.piece_map())
        scaling = 1.0 if num_pieces > 20 else 1.5
        reward += PIECE_VALUES.get(captured_piece.symbol().lower(), 0.0) * scaling

    board.push(move)
    turn = board.turn
    enemy_color = not turn

    for square, piece in board.piece_map().items():
        if piece.color == turn and board.is_attacked_by(enemy_color, square):
            reward -= PIECE_VALUES.get(piece.symbol().lower(), 0.0) * 0.5

    for sq in CENTER_SQUARES:
        piece = board.piece_at(sq)
        if piece is not None and piece.color != turn:
            reward += 0.05

    board.pop()
    return reward

