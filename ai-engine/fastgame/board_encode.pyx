# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""
High-speed board encoding: 18-plane float32 tensor from python-chess Board.
All inner loops run in pure C – only the 12 pieces_mask() calls cross the
Python boundary (unavoidable without replacing python-chess entirely).
"""
import chess
import numpy as np
cimport numpy as cnp
from libc.string cimport memset

cnp.import_array()

# ── C-level bitboard → plane fill ────────────────────────────────────────────

cdef inline void _bb_to_plane(unsigned long long bb, float *plane) noexcept nogil:
    """Set plane[sq] = 1.0 for each set bit via isolate-lowest-bit."""
    cdef unsigned long long tmp = bb
    cdef unsigned long long lowest
    cdef int sq
    while tmp:
        lowest = tmp & (<unsigned long long>0 - tmp)  # isolate LSB
        sq = 0
        if lowest:
            while (lowest >> sq) != 1:
                sq += 1
        plane[sq] = 1.0
        tmp ^= lowest


cdef inline void _fill_plane_one(float *plane) noexcept nogil:
    """Fill entire 64-float plane with 1.0."""
    cdef int i
    for i in range(64):
        plane[i] = 1.0


# ── Public API ────────────────────────────────────────────────────────────────

def encode_board_array(board):
    """Return an [18, 8, 8] float32 numpy array for the given python-chess Board.

    ~3-5x faster than the pure-Python version because all
    inner loops are compiled to C.
    """
    cdef cnp.ndarray[float, ndim=1] flat = np.zeros(18 * 64, dtype=np.float32)
    cdef float *data = <float *>flat.data

    # ── Extract 12 bitboard masks (only Python→C crossing) ───────────────
    cdef unsigned long long masks[12]
    masks[0]  = <unsigned long long>board.pieces_mask(chess.PAWN,   chess.WHITE)
    masks[1]  = <unsigned long long>board.pieces_mask(chess.KNIGHT, chess.WHITE)
    masks[2]  = <unsigned long long>board.pieces_mask(chess.BISHOP, chess.WHITE)
    masks[3]  = <unsigned long long>board.pieces_mask(chess.ROOK,   chess.WHITE)
    masks[4]  = <unsigned long long>board.pieces_mask(chess.QUEEN,  chess.WHITE)
    masks[5]  = <unsigned long long>board.pieces_mask(chess.KING,   chess.WHITE)
    masks[6]  = <unsigned long long>board.pieces_mask(chess.PAWN,   chess.BLACK)
    masks[7]  = <unsigned long long>board.pieces_mask(chess.KNIGHT, chess.BLACK)
    masks[8]  = <unsigned long long>board.pieces_mask(chess.BISHOP, chess.BLACK)
    masks[9]  = <unsigned long long>board.pieces_mask(chess.ROOK,   chess.BLACK)
    masks[10] = <unsigned long long>board.pieces_mask(chess.QUEEN,  chess.BLACK)
    masks[11] = <unsigned long long>board.pieces_mask(chess.KING,   chess.BLACK)

    # ── Fill piece planes in pure C ──────────────────────────────────────
    cdef int plane
    with nogil:
        for plane in range(12):
            if masks[plane]:
                _bb_to_plane(masks[plane], data + plane * 64)

    # ── Metadata planes ──────────────────────────────────────────────────
    if board.turn == chess.WHITE:
        with nogil:
            _fill_plane_one(data + 12 * 64)

    if board.has_kingside_castling_rights(chess.WHITE):
        with nogil:
            _fill_plane_one(data + 13 * 64)
    if board.has_queenside_castling_rights(chess.WHITE):
        with nogil:
            _fill_plane_one(data + 14 * 64)
    if board.has_kingside_castling_rights(chess.BLACK):
        with nogil:
            _fill_plane_one(data + 15 * 64)
    if board.has_queenside_castling_rights(chess.BLACK):
        with nogil:
            _fill_plane_one(data + 16 * 64)

    cdef int ep_sq
    if board.ep_square is not None:
        ep_sq = board.ep_square
        data[17 * 64 + ep_sq] = 1.0

    return flat.reshape((18, 8, 8))


def encode_board_batch(boards):
    """Encode a list of boards into a single [N, 18, 8, 8] float32 numpy array.

    More efficient than calling encode_board_array() in a loop because we
    allocate one contiguous buffer.
    """
    cdef int n = len(boards)
    if n == 0:
        return np.zeros((0, 18, 8, 8), dtype=np.float32)
    cdef cnp.ndarray[float, ndim=1] flat = np.zeros(n * 18 * 64, dtype=np.float32)
    cdef float *data = <float *>flat.data
    cdef int i, plane, ep_sq
    cdef unsigned long long masks[12]
    cdef float *board_data

    for i in range(n):
        board = boards[i]
        board_data = data + i * 18 * 64

        masks[0]  = <unsigned long long>board.pieces_mask(chess.PAWN,   chess.WHITE)
        masks[1]  = <unsigned long long>board.pieces_mask(chess.KNIGHT, chess.WHITE)
        masks[2]  = <unsigned long long>board.pieces_mask(chess.BISHOP, chess.WHITE)
        masks[3]  = <unsigned long long>board.pieces_mask(chess.ROOK,   chess.WHITE)
        masks[4]  = <unsigned long long>board.pieces_mask(chess.QUEEN,  chess.WHITE)
        masks[5]  = <unsigned long long>board.pieces_mask(chess.KING,   chess.WHITE)
        masks[6]  = <unsigned long long>board.pieces_mask(chess.PAWN,   chess.BLACK)
        masks[7]  = <unsigned long long>board.pieces_mask(chess.KNIGHT, chess.BLACK)
        masks[8]  = <unsigned long long>board.pieces_mask(chess.BISHOP, chess.BLACK)
        masks[9]  = <unsigned long long>board.pieces_mask(chess.ROOK,   chess.BLACK)
        masks[10] = <unsigned long long>board.pieces_mask(chess.QUEEN,  chess.BLACK)
        masks[11] = <unsigned long long>board.pieces_mask(chess.KING,   chess.BLACK)

        with nogil:
            for plane in range(12):
                if masks[plane]:
                    _bb_to_plane(masks[plane], board_data + plane * 64)

        if board.turn == chess.WHITE:
            with nogil:
                _fill_plane_one(board_data + 12 * 64)

        if board.has_kingside_castling_rights(chess.WHITE):
            with nogil:
                _fill_plane_one(board_data + 13 * 64)
        if board.has_queenside_castling_rights(chess.WHITE):
            with nogil:
                _fill_plane_one(board_data + 14 * 64)
        if board.has_kingside_castling_rights(chess.BLACK):
            with nogil:
                _fill_plane_one(board_data + 15 * 64)
        if board.has_queenside_castling_rights(chess.BLACK):
            with nogil:
                _fill_plane_one(board_data + 16 * 64)

        if board.ep_square is not None:
            ep_sq = board.ep_square
            board_data[17 * 64 + ep_sq] = 1.0

    return flat.reshape((n, 18, 8, 8))
