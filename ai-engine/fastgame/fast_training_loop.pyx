# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""
Fast self-play training loop.
Runs the entire game simulation with minimal Python overhead.
Board encoding is done in batch at the end instead of per-move.
"""
import chess
import random
import numpy as np
cimport numpy as cnp

cnp.import_array()


cdef inline int _popcount(unsigned long long bb) noexcept nogil:
    cdef int count = 0
    while bb:
        bb &= bb - 1
        count += 1
    return count


cdef bint _fast_is_game_over(board, int ply):
    """Fast game-over with amortized repetition checks."""
    if board.is_checkmate() or board.is_stalemate():
        return True
    if board.is_insufficient_material():
        return True
    if board.halfmove_clock >= 100:
        return True
    # Threefold: only every 4 plies, only if no capture/pawn move since last check
    if ply >= 8 and ply % 4 == 0 and board.halfmove_clock >= 4:
        if board.can_claim_threefold_repetition():
            return True
    return False


def play_one_game_fast(board, ai_white_func, ai_black_func, move_to_idx,
                       int random_opening_plies=6,
                       double exploration_epsilon=0.20,
                       int policy_top_n=3,
                       int policy_sample_k=2,
                       pred_cache_white=None,
                       pred_cache_black=None,
                       move_cache_white=None,
                       move_cache_black=None,
                       cpu_model=None):
    """Play one game collecting (board_copy, move_idx) pairs.

    Returns: (white_history, black_history, result_str)

    board_copies are chess.Board snapshots (cheap via copy()).
    Encoding is deferred to batch encoding after game selection.
    """
    cdef int ply_count = 0
    cdef bint is_white_turn

    white_boards = []
    white_moves = []
    black_boards = []
    black_moves = []

    if pred_cache_white is None:
        pred_cache_white = {}
    if pred_cache_black is None:
        pred_cache_black = {}
    if move_cache_white is None:
        move_cache_white = {}
    if move_cache_black is None:
        move_cache_black = {}

    while not _fast_is_game_over(board, ply_count):
        ply_count += 1
        is_white_turn = board.turn == chess.WHITE

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            break

        if ply_count <= random_opening_plies or random.random() < exploration_epsilon:
            move = random.choice(legal_moves)
        else:
            if is_white_turn:
                move = ai_white_func(
                    board,
                    top_n=policy_top_n,
                    sample_top_k=policy_sample_k,
                    prediction_cache=pred_cache_white,
                    move_cache=move_cache_white,
                    cpu_model=cpu_model,
                )
            else:
                move = ai_black_func(
                    board,
                    top_n=policy_top_n,
                    sample_top_k=policy_sample_k,
                    prediction_cache=pred_cache_black,
                    move_cache=move_cache_black,
                    cpu_model=cpu_model,
                )
            if move is None:
                move = random.choice(legal_moves)

        move_idx = move_to_idx.get(move.uci())
        if move_idx is not None:
            # Store board copy (fast) instead of encoding now
            if is_white_turn:
                white_boards.append(board.copy())
                white_moves.append(move_idx)
            else:
                black_boards.append(board.copy())
                black_moves.append(move_idx)

        board.push(move)

    result = board.result(claim_draw=True)
    return (white_boards, white_moves), (black_boards, black_moves), result


def play_games_fast(ai_white, ai_black, game, fen_positions, int num_games,
                    int policy_top_n=3, int policy_sample_k=2,
                    double exploration_epsilon=0.20,
                    int random_opening_plies=6,
                    double draw_sample_ratio=0.15,
                    move_to_idx=None,
                    encode_batch_fn=None,
                    cpu_model=None):
    """Play N games and return (states_np, moves_list, stats_dict).

    Key optimization: board encoding is deferred and done in batch
    using encode_board_batch() after game result filtering.
    cpu_model: optional CPU-only model for fast single-board inference.
    """
    from collections import Counter

    cdef int g, half, keep_w, keep_b

    stats = Counter()
    # Collect boards to encode in batch
    all_boards = []
    all_move_indices = []

    for g in range(num_games):
        if fen_positions:
            fen = random.choice(fen_positions)
            game.reset_from_fen(fen)
        else:
            game.reset()

        ai_white.model.eval()

        (w_boards, w_moves), (b_boards, b_moves), result = play_one_game_fast(
            game.board,
            ai_white.get_fast_move_from_model,
            ai_black.get_fast_move_from_model,
            move_to_idx,
            random_opening_plies=random_opening_plies,
            exploration_epsilon=exploration_epsilon,
            policy_top_n=policy_top_n,
            policy_sample_k=policy_sample_k,
            cpu_model=cpu_model,
        )
        stats[result] += 1

        # Filter samples based on result (same logic as MirrorMatch)
        if result == '1-0':
            all_boards.extend(w_boards)
            all_move_indices.extend(w_moves)
            if b_boards:
                half = max(1, len(b_boards) // 2)
                sampled_idx = random.sample(range(len(b_boards)), half)
                for idx in sampled_idx:
                    all_boards.append(b_boards[idx])
                    all_move_indices.append(b_moves[idx])
        elif result == '0-1':
            all_boards.extend(b_boards)
            all_move_indices.extend(b_moves)
            if w_boards:
                half = max(1, len(w_boards) // 2)
                sampled_idx = random.sample(range(len(w_boards)), half)
                for idx in sampled_idx:
                    all_boards.append(w_boards[idx])
                    all_move_indices.append(w_moves[idx])
        else:
            # Draws: keep small ratio
            if w_boards:
                keep_w = max(1, int(len(w_boards) * draw_sample_ratio))
                sampled_idx = random.sample(range(len(w_boards)), min(keep_w, len(w_boards)))
                for idx in sampled_idx:
                    all_boards.append(w_boards[idx])
                    all_move_indices.append(w_moves[idx])
            if b_boards:
                keep_b = max(1, int(len(b_boards) * draw_sample_ratio))
                sampled_idx = random.sample(range(len(b_boards)), min(keep_b, len(b_boards)))
                for idx in sampled_idx:
                    all_boards.append(b_boards[idx])
                    all_move_indices.append(b_moves[idx])

    # Batch encode all boards at once (much faster than per-move encoding)
    if all_boards and encode_batch_fn is not None:
        states_np = encode_batch_fn(all_boards)
    else:
        states_np = None

    return states_np, all_move_indices, stats

