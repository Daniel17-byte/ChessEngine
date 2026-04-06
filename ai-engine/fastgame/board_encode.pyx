# cython: language_level=3
import chess
import numpy as np
cimport numpy as cnp

ctypedef cnp.float32_t float32_t

cdef inline void _fill_plane_ones(cnp.ndarray[float32_t, ndim=3] arr, int plane):
    cdef int r
    cdef int f
    for r in range(8):
        for f in range(8):
            arr[plane, r, f] = 1.0


def encode_board_array(board):
    """Return a [18, 8, 8] float32 numpy array for ArchiveAlpha features."""
    cdef cnp.ndarray[float32_t, ndim=3] arr = np.zeros((18, 8, 8), dtype=np.float32)
    cdef tuple piece_masks = (
        board.pieces_mask(chess.PAWN, chess.WHITE),
        board.pieces_mask(chess.KNIGHT, chess.WHITE),
        board.pieces_mask(chess.BISHOP, chess.WHITE),
        board.pieces_mask(chess.ROOK, chess.WHITE),
        board.pieces_mask(chess.QUEEN, chess.WHITE),
        board.pieces_mask(chess.KING, chess.WHITE),
        board.pieces_mask(chess.PAWN, chess.BLACK),
        board.pieces_mask(chess.KNIGHT, chess.BLACK),
        board.pieces_mask(chess.BISHOP, chess.BLACK),
        board.pieces_mask(chess.ROOK, chess.BLACK),
        board.pieces_mask(chess.QUEEN, chess.BLACK),
        board.pieces_mask(chess.KING, chess.BLACK),
    )
    cdef int plane
    cdef int sq
    cdef unsigned long long bb

    for plane in range(12):
        bb = <unsigned long long>piece_masks[plane]
        for sq in range(64):
            if (bb >> sq) & 1:
                arr[plane, sq // 8, sq % 8] = 1.0

    if board.turn == chess.WHITE:
        _fill_plane_ones(arr, 12)
    if board.has_kingside_castling_rights(chess.WHITE):
        _fill_plane_ones(arr, 13)
    if board.has_queenside_castling_rights(chess.WHITE):
        _fill_plane_ones(arr, 14)
    if board.has_kingside_castling_rights(chess.BLACK):
        _fill_plane_ones(arr, 15)
    if board.has_queenside_castling_rights(chess.BLACK):
        _fill_plane_ones(arr, 16)

    if board.ep_square is not None:
        arr[17, board.ep_square // 8, board.ep_square % 8] = 1.0

    return arr

