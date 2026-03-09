import chess
import chess.engine
import random
from typing import Optional
from ArchiveAlpha import encode_board
from ChessNet import ChessNet
import torch
import os

import json
with open('move_mapping.json', 'r', encoding='utf-8') as fmap:
    move_list = json.load(fmap)
w2i = {m: i for i, m in enumerate(move_list)}
b2i = w2i

engine_path = "/opt/homebrew/bin/stockfish"

class ChessAI:
    def __init__(self, is_white=True, default_strategy: Optional[str] = None):
        self.is_white = is_white
        self.board = chess.Board()
        # Select device: prefer MPS on Mac, then CUDA, then CPU
        if torch.backends.mps.is_available():
            self.device = torch.device('mps')
        elif torch.cuda.is_available():
            self.device = torch.device('cuda')
        else:
            self.device = torch.device('cpu')

        self.model = ChessNet(len(move_list))
        self.model.to(self.device)
        model_path = "chessnet.pth"
        if os.path.exists(model_path):
            try:
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                print(f"Model loaded successfully from {model_path}")
            except (RuntimeError, KeyError) as e:
                print(f"⚠️ Could not load model from {model_path}: {e}")
                print("Architecture mismatch — training from scratch.")
                # Remove old incompatible checkpoint
                os.rename(model_path, model_path + ".old")
                print(f"Old model backed up to {model_path}.old")
        else:
            print(f"Model not found ({model_path}) - training from scratch.")

        # Only load Stockfish if the strategy might need it
        needs_stockfish = default_strategy in (None, 'stockfish')
        if needs_stockfish and os.path.exists(engine_path):
            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        elif needs_stockfish:
            self.engine = None
            print(f"⚠️ Stockfish nu a fost găsit la {engine_path}. Strategy 'stockfish' nu va fi disponibil.")
        else:
            self.engine = None
            print(f"ℹ️ Stockfish nu e necesar pentru strategia '{default_strategy}' — nu se încarcă.")

        with open("move_mapping.json") as f:
            self.idx_to_move = json.load(f)
        self.move_to_idx = {uci: i for i, uci in enumerate(self.idx_to_move)}

        self.model.eval()
        self.epsilon = 0.05
        self.default_strategy = default_strategy

    def move_to_index(self, move_uci: str) -> int:
        if move_uci not in self.move_to_idx:
            self.move_to_idx[move_uci] = len(self.idx_to_move)
            self.idx_to_move.append(move_uci)
        return self.move_to_idx[move_uci]

    def select_move(self, board: chess.Board, strategy: Optional[str] = None) -> Optional[chess.Move]:
        self.board = board
        if strategy is None:
            strategy = self.default_strategy

        if strategy == 'epsilon':
            return random.choice(list(self.board.legal_moves))
        elif strategy == 'model':
            return self.get_best_move_from_model(board)
        elif strategy == 'minimax':
            return self.select_move_minimax(board)
        elif strategy == 'stockfish':
            return self.get_best_move_from_stockfish(board)
        return None

    def get_best_move_from_stockfish(self, board: chess.Board, time_limit: float = 0.05) -> Optional[chess.Move]:
        if self.engine is None:
            return random.choice(list(board.legal_moves))
        if board.is_game_over():
            return None
        result = self.engine.play(board, chess.engine.Limit(time=time_limit))
        return result.move

    def get_best_move_from_model(self, board: chess.Board) -> Optional[chess.Move]:
        self.board = board
        board_tensor = encode_board(board).unsqueeze(0).to(self.device)

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        with torch.no_grad():
            prediction = self.model(board_tensor).squeeze(0)

        output_size = prediction.shape[0]
        legal_indices = [self.move_to_index(m.uci()) for m in legal_moves if self.move_to_index(m.uci()) < output_size]

        if not legal_indices:
            return random.choice(legal_moves)

        if random.random() < self.epsilon:
            return random.choice(legal_moves)

        best_idx = max(legal_indices, key=lambda i: prediction[i].item())
        best_move = chess.Move.from_uci(self.idx_to_move[best_idx])

        if best_move not in self.board.legal_moves:
            fallback = random.choice(legal_moves)
            print(f"⚠️ Mutarea {best_move.uci()} nu e legală, fallback: {fallback.uci()}")
            return fallback

        return best_move

    def evaluate_board(self, board: chess.Board) -> float:
        my_color = chess.WHITE if self.is_white else chess.BLACK
        if board.is_checkmate():
            return float('-inf') if board.turn == my_color else float('inf')

        piece_values = {
            chess.PAWN: 1.0,
            chess.KNIGHT: 3.2,
            chess.BISHOP: 3.3,
            chess.ROOK: 5.0,
            chess.QUEEN: 9.0,
            chess.KING: 0.0
        }

        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        value = 0.0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                sign = 1 if piece.color == chess.WHITE else -1
                piece_type = piece.piece_type
                val = piece_values[piece_type]

                # Bonus for controlling the center
                if square in center_squares:
                    val += 0.1

                value += sign * val

        if board.is_check():
            value += 0.5 if board.turn != my_color else -0.5

        # Evaluation is from white's perspective; flip for black AI
        return value if self.is_white else -value

    def select_move_minimax(self, board: chess.Board, depth: int = 2) -> Optional[chess.Move]:
        def minimax(board_, depth_, alpha, beta, maximizing_player):
            if depth_ == 0 or board_.is_game_over():
                return self.evaluate_board(board_), None

            best_move_ = None
            if maximizing_player:
                max_eval = float('-inf')
                for move in board_.legal_moves:
                    board_.push(move)
                    eval_, _ = minimax(board_, depth_ - 1, alpha, beta, False)
                    board_.pop()
                    if eval_ > max_eval:
                        max_eval = eval_
                        best_move_ = move
                    alpha = max(alpha, eval_)
                    if beta <= alpha:
                        break
                return max_eval, best_move_
            else:
                min_eval = float('inf')
                for move in board_.legal_moves:
                    board_.push(move)
                    eval_, _ = minimax(board_, depth_ - 1, alpha, beta, True)
                    board_.pop()
                    if eval_ < min_eval:
                        min_eval = eval_
                        best_move_ = move
                    beta = min(beta, eval_)
                    if beta <= alpha:
                        break
                return min_eval, best_move_

        _, best_move = minimax(board, depth, float('-inf'), float('inf'), board.turn == (chess.WHITE if self.is_white else chess.BLACK))
        return best_move