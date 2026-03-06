import chess

class Game:
    def __init__(self, ai_white=None, ai_black=None):
        self.board = chess.Board()
        self.ai_white = ai_white
        self.ai_black = ai_black
        self.turn = chess.WHITE

    def _auto_promote_if_needed(self, move_uci):
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
        piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
        reward = -0.01
        if captured_piece:
            num_pieces = len(self.board.piece_map())
            scaling = 1.0 if num_pieces > 20 else 1.5
            reward += piece_values.get(captured_piece.symbol().lower(), 0) * scaling

        # Temporarily push move to evaluate positional factors
        self.board.push(move)

        for square in self.board.piece_map():
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                if self.board.is_attacked_by(not self.board.turn, square):
                    reward -= piece_values.get(piece.symbol().lower(), 0) * 0.5

        for sq in [chess.E4, chess.D4, chess.E5, chess.D5]:
            piece = self.board.piece_at(sq)
            if piece and piece.color != self.board.turn:
                reward += 0.05

        # Pop the move so make_move can push it properly
        self.board.pop()

        return reward

    def make_move(self, move_uci=None):
        if self.board.is_game_over():
            return False, "Game is already over"

        move_uci = self._auto_promote_if_needed(move_uci)
        move = chess.Move.from_uci(move_uci)

        if move not in self.board.legal_moves:
            return False, "Mutare ilegală"

        captured_piece = self.board.piece_at(move.to_square)
        reward = self._calculate_reward(move, captured_piece)

        # Actually apply the move to the board
        self.board.push(move)

        # verificăm starea jocului după mutare
        return True, {
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
            "is_game_over": self.board.is_game_over(),
            "reward": reward
        }

    def reset(self):
        self.board.reset()
        self.turn = chess.WHITE  # Reset turn to white
        print("🔄 Board has been reset to initial state.")  # Debugging log
        print(f"Current FEN: {self.board.fen()}")  # Log the FEN for debugging
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
