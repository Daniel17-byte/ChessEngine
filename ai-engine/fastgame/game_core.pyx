# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""
Optimized game-core helpers.  calculate_reward uses bitboard piece counting
where possible to reduce Python object creation.
"""
import chess

# C-typed piece values for fast lookup
cdef double[7] C_PIECE_VALUES
C_PIECE_VALUES[0] = 0.0  # no piece
C_PIECE_VALUES[1] = 1.0  # PAWN
C_PIECE_VALUES[2] = 3.0  # KNIGHT
C_PIECE_VALUES[3] = 3.0  # BISHOP
C_PIECE_VALUES[4] = 5.0  # ROOK
C_PIECE_VALUES[5] = 9.0  # QUEEN
C_PIECE_VALUES[6] = 0.0  # KING

PIECE_VALUES = {'p': 1.0, 'n': 3.0, 'b': 3.0, 'r': 5.0, 'q': 9.0, 'k': 0.0}
CENTER_SQUARES = (chess.E4, chess.D4, chess.E5, chess.D5)


cdef inline int _popcount(unsigned long long bb) noexcept nogil:
    cdef int count = 0
    while bb:
        bb &= bb - 1
        count += 1
    return count


def auto_promote_if_needed(board, move_uci):
    if move_uci is None or len(move_uci) != 4:
        return move_uci
    cdef int from_sq = chess.parse_square(move_uci[:2])
    cdef int to_sq = chess.parse_square(move_uci[2:4])
    piece = board.piece_at(from_sq)
    if piece and piece.piece_type == chess.PAWN:
        if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
           (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
            return move_uci + 'q'
    return move_uci


def calculate_reward(board, move, captured_piece):
    """Calculate move reward with bitboard-accelerated piece counting."""
    cdef double reward = -0.01
    cdef double scaling
    cdef int num_pieces
    cdef int piece_type

    if captured_piece is not None:
        # Use bitboard popcount instead of len(board.piece_map())
        num_pieces = _popcount(<unsigned long long>board.occupied)
        scaling = 1.0 if num_pieces > 20 else 1.5
        piece_type = captured_piece.piece_type
        if 1 <= piece_type <= 6:
            reward += C_PIECE_VALUES[piece_type] * scaling

    board.push(move)
    turn = board.turn
    enemy_color = not turn

    # Use piece_map iteration but with C-typed value lookup
    cdef double val
    for square, piece in board.piece_map().items():
        if piece.color == turn and board.is_attacked_by(enemy_color, square):
            piece_type = piece.piece_type
            if 1 <= piece_type <= 6:
                val = C_PIECE_VALUES[piece_type]
            else:
                val = 0.0
            reward -= val * 0.5

    for sq in CENTER_SQUARES:
        piece = board.piece_at(sq)
        if piece is not None and piece.color != turn:
            reward += 0.05

    board.pop()
    return reward


def count_pieces_fast(board):
    """Fast piece count using bitboard popcount."""
    return _popcount(<unsigned long long>board.occupied)
