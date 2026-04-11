# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""
Bitboard-based board evaluation.  Avoids board.piece_map() entirely by
using pieces_mask() and popcount for material scoring.
"""
import chess

# Piece values indexed by piece_type (1=PAWN .. 5=QUEEN, 6=KING)
cdef double[7] C_PIECE_VAL
C_PIECE_VAL[0] = 0.0
C_PIECE_VAL[1] = 1.0   # PAWN
C_PIECE_VAL[2] = 3.2   # KNIGHT
C_PIECE_VAL[3] = 3.3   # BISHOP
C_PIECE_VAL[4] = 5.0   # ROOK
C_PIECE_VAL[5] = 9.0   # QUEEN
C_PIECE_VAL[6] = 0.0   # KING

# Center squares as a bitmask
cdef unsigned long long CENTER_BB = (
    (1ULL << 27) |  # D4
    (1ULL << 28) |  # E4
    (1ULL << 35) |  # D5
    (1ULL << 36)    # E5
)

cdef inline int _popcount(unsigned long long bb) noexcept nogil:
    cdef int count = 0
    while bb:
        bb &= bb - 1
        count += 1
    return count


def evaluate_board(board, bint is_white):
    """Evaluate board using bitboard operations – no piece_map() call."""
    cdef int my_color = chess.WHITE if is_white else chess.BLACK
    cdef double value = 0.0
    cdef int pt
    cdef unsigned long long white_bb, black_bb, center_w, center_b

    if board.is_checkmate():
        if board.turn == my_color:
            return float('-inf')
        return float('inf')

    # Material evaluation via bitboard popcount – no Python dict creation
    for pt in range(1, 7):
        white_bb = <unsigned long long>board.pieces_mask(pt, chess.WHITE)
        black_bb = <unsigned long long>board.pieces_mask(pt, chess.BLACK)
        value += C_PIECE_VAL[pt] * _popcount(white_bb)
        value -= C_PIECE_VAL[pt] * _popcount(black_bb)

        # Center control bonus
        if pt <= 5:  # not king
            center_w = white_bb & CENTER_BB
            center_b = black_bb & CENTER_BB
            value += 0.1 * _popcount(center_w)
            value -= 0.1 * _popcount(center_b)

    # Check bonus
    if board.is_check():
        value += 0.5 if board.turn != my_color else -0.5

    return value if is_white else -value


def evaluate_material_fast(board):
    """Return raw material balance (white - black) using bitboards only."""
    cdef double value = 0.0
    cdef int pt
    cdef unsigned long long white_bb, black_bb
    for pt in range(1, 6):  # PAWN..QUEEN
        white_bb = <unsigned long long>board.pieces_mask(pt, chess.WHITE)
        black_bb = <unsigned long long>board.pieces_mask(pt, chess.BLACK)
        value += C_PIECE_VAL[pt] * (_popcount(white_bb) - _popcount(black_bb))
    return value
