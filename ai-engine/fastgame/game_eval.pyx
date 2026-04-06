# cython: language_level=3
import chess

cdef inline double _piece_value(int piece_type):
    if piece_type == chess.PAWN:
        return 1.0
    elif piece_type == chess.KNIGHT:
        return 3.2
    elif piece_type == chess.BISHOP:
        return 3.3
    elif piece_type == chess.ROOK:
        return 5.0
    elif piece_type == chess.QUEEN:
        return 9.0
    return 0.0


def evaluate_board(board, bint is_white):
    cdef int my_color = chess.WHITE if is_white else chess.BLACK
    cdef double value = 0.0
    cdef double sign
    cdef double val

    if board.is_checkmate():
        if board.turn == my_color:
            return float('-inf')
        return float('inf')

    for square, piece in board.piece_map().items():
        sign = 1.0 if piece.color == chess.WHITE else -1.0
        val = _piece_value(piece.piece_type)
        if square == chess.D4 or square == chess.D5 or square == chess.E4 or square == chess.E5:
            val += 0.1
        value += sign * val

    if board.is_check():
        value += 0.5 if board.turn != my_color else -0.5

    return value if is_white else -value

