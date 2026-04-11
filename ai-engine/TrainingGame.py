import chess
import os

# Try to use Cython fast training loop
USE_CYTHON = os.getenv("CHESS_GAME_FORCE_PYTHON", "0") != "1"
if USE_CYTHON:
    try:
        from fastgame.fast_training_loop import play_one_game_fast, play_games_fast
        HAS_CYTHON_TRAINING = True
    except ImportError:
        HAS_CYTHON_TRAINING = False
else:
    HAS_CYTHON_TRAINING = False


class TrainingGame:
    """Minimal game loop optimized for high-throughput self-play training.

    Key optimizations over Game.py:
    - No reward calculation during game play
    - No state payload construction
    - Skips game-over check before each move (redundant with while loop)
    - Uses cheap game-over detection with lazy draw claims
    - Exposes board directly for Cython fast loop access
    """

    __slots__ = ('board', '_ply')

    def __init__(self):
        self.board = chess.Board()
        self._ply = 0

    def reset(self):
        self.board.reset()
        self._ply = 0

    def reset_from_fen(self, fen: str):
        self.board.set_fen(fen)
        self._ply = 0

    def is_game_over(self) -> bool:
        """Fast game-over check: avoids expensive repetition checks on most plies.

        can_claim_threefold_repetition() scans the entire move history and is
        the dominant bottleneck in long self-play games.  We mitigate by:
        1. Only checking threefold every 4 plies (repetition can't appear between)
        2. Only when halfmove_clock > 0 (if a pawn moved or capture happened,
           repetition chain is broken)
        3. Standard checks (checkmate, stalemate, insufficient) stay per-ply
        """
        board = self.board

        # Cheap checks first
        if board.is_checkmate() or board.is_stalemate():
            return True

        if board.is_insufficient_material():
            return True

        # 50-move: only check when clock is actually at limit
        if board.halfmove_clock >= 100:
            return True  # claim the draw

        # Threefold repetition: only check periodically and when possible
        # A repetition requires the same position to appear 3 times.
        # After a capture or pawn move (halfmove_clock resets), prior positions
        # can't repeat, so skip the check entirely.
        # Check every 4 plies to amortize cost.
        if self._ply >= 8 and self._ply % 4 == 0 and board.halfmove_clock >= 4:
            if board.can_claim_threefold_repetition():
                return True

        return False

    def make_move_fast(self, move_or_uci):
        """Apply one move with minimal overhead. Returns (ok, None)."""
        try:
            move = move_or_uci if isinstance(move_or_uci, chess.Move) else chess.Move.from_uci(move_or_uci)
        except (ValueError, TypeError):
            return False, None

        if not self.board.is_legal(move):
            return False, None

        self.board.push(move)
        self._ply += 1
        return True, None

    def get_result(self) -> str:
        return self.board.result(claim_draw=True)

    @staticmethod
    def has_cython_training():
        """Check if Cython fast training loop is available."""
        return HAS_CYTHON_TRAINING
