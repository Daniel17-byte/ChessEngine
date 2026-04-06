import os
import chess

PIECE_VALUES = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
CENTER_SQUARES = (chess.E4, chess.D4, chess.E5, chess.D5)

USE_CYTHON_GAME_CORE = os.getenv("CHESS_GAME_FORCE_PYTHON", "0") != "1"

if USE_CYTHON_GAME_CORE:
    try:
        from fastgame.game_core import auto_promote_if_needed as cy_auto_promote_if_needed
        from fastgame.game_core import calculate_reward as cy_calculate_reward
        HAS_CYTHON_GAME_CORE = True
    except ImportError:
        HAS_CYTHON_GAME_CORE = False
else:
    HAS_CYTHON_GAME_CORE = False


class Game:
    def __init__(self, ai_white=None, ai_black=None):
        self.board = chess.Board()
        self.ai_white = ai_white
        self.ai_black = ai_black
        self.turn = chess.WHITE

    def _auto_promote_if_needed(self, move_uci):
        if HAS_CYTHON_GAME_CORE:
            return cy_auto_promote_if_needed(self.board, move_uci)
        if len(move_uci) == 4:
            from_sq = chess.parse_square(move_uci[:2])
            to_sq = chess.parse_square(move_uci[2:4])
            piece = self.board.piece_at(from_sq)
            if piece and piece.piece_type == chess.PAWN:
                # White promotes when reaching rank 7 (8th row), Black promotes when reaching rank 0 (1st row)
                if (piece.color == chess.WHITE and chess.square_rank(to_sq) == 7) or \
                        (piece.color == chess.BLACK and chess.square_rank(to_sq) == 0):
                    return move_uci + 'q'
        return move_uci

    def _calculate_reward(self, move, captured_piece):
        if HAS_CYTHON_GAME_CORE:
            return cy_calculate_reward(self.board, move, captured_piece)

        reward = -0.01
        if captured_piece:
            num_pieces = len(self.board.piece_map())
            scaling = 1.0 if num_pieces > 20 else 1.5
            reward += PIECE_VALUES.get(captured_piece.symbol().lower(), 0) * scaling

        # Temporarily push move to evaluate positional factors.
        self.board.push(move)

        board = self.board
        enemy_color = not board.turn
        for square, piece in board.piece_map().items():
            if piece.color == board.turn and board.is_attacked_by(enemy_color, square):
                reward -= PIECE_VALUES.get(piece.symbol().lower(), 0) * 0.5

        for sq in CENTER_SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.color != board.turn:
                reward += 0.05

        self.board.pop()
        return reward

    def make_move(self, move_uci=None):
        if self.board.is_game_over():
            return False, "Game is already over"

        move_uci = self._auto_promote_if_needed(move_uci)
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError:
            return False, "Mutare ilegală"

        if move not in self.board.legal_moves:
            return False, "Mutare ilegală"

        captured_piece = self.board.piece_at(move.to_square)
        reward = self._calculate_reward(move, captured_piece)

        self.board.push(move)
        board = self.board

        return True, {
            "fen": board.fen(),
            "turn": "white" if board.turn == chess.WHITE else "black",
            "is_check": board.is_check(),
            "is_checkmate": board.is_checkmate(),
            "is_stalemate": board.is_stalemate(),
            "is_insufficient_material": board.is_insufficient_material(),
            "is_fifty_moves": board.is_fifty_moves(),
            "can_claim_fifty_moves": board.can_claim_fifty_moves(),
            "is_repetition": board.is_repetition(),
            "can_claim_threefold_repetition": board.can_claim_threefold_repetition(),
            "is_game_over": board.is_game_over(),
            "reward": reward
        }

    def reset(self):
        self.board.reset()
        self.turn = chess.WHITE  # Reset turn to white
        return {
            "message": "Board reset",
            "fen": self.board.fen(),
            "turn": "white",
            "is_check": False,
            "is_checkmate": False,
            "is_stalemate": False,
            "is_insufficient_material": False
        }

    def reset_from_fen(self, fen):
        self.board = chess.Board(fen)
        return {
            "message": "Board reset from FEN",
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn == chess.WHITE else "black",
            "is_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate(),
            "is_insufficient_material": self.board.is_insufficient_material(),
            "is_fifty_moves": self.board.is_fifty_moves(),
            "can_claim_fifty_moves": self.board.can_claim_fifty_moves(),
            "is_repetition": self.board.is_repetition(),
            "can_claim_threefold_repetition": self.board.can_claim_threefold_repetition(),
            "is_game_over": self.board.is_game_over()
        }

    def get_board_fen(self):
        return self.board.fen()

    def is_game_over(self):
        return self.board.is_game_over()

    def get_fen(self):
        return self.board.fen()

    def ai_move(self, side):
        if self.board.is_game_over():
            return None

        ai = self.ai_white if side == chess.WHITE else self.ai_black
        if not ai or self.board.turn != side:
            return None

        move = ai.select_move(self.board)
        self.board.push(move)
        return move.uci()

    def get_result(self):
        return self.board.result()
