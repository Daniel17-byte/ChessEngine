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

PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.2,
    chess.BISHOP: 3.3,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}
CENTER_SQUARES = {chess.D4, chess.D5, chess.E4, chess.E5}

USE_CYTHON_EVAL = os.getenv("CHESS_EVAL_FORCE_PYTHON", "0") != "1"
if USE_CYTHON_EVAL:
    try:
        from fastgame.game_eval import evaluate_board as cy_evaluate_board
        HAS_CYTHON_EVAL = True
    except ImportError:
        HAS_CYTHON_EVAL = False
else:
    HAS_CYTHON_EVAL = False


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
        # Optional PyTorch compile for faster repeated inference on supported backends.
        if os.getenv("CHESS_USE_TORCH_COMPILE", "0") == "1" and hasattr(torch, "compile"):
            try:
                self.model = torch.compile(self.model, mode="reduce-overhead")
            except Exception as exc:
                print(f"⚠️ torch.compile disabled: {exc}")

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

    def get_best_move_from_stockfish(self, board: chess.Board, time_limit: float = 0.01) -> Optional[chess.Move]:
        if self.engine is None:
            return random.choice(list(board.legal_moves))
        if board.is_game_over():
            return None
        result = self.engine.play(board, chess.engine.Limit(time=time_limit))
        return result.move

    def _predict_policy(self, board: chess.Board, cache: dict) -> torch.Tensor:
        # Include full state parts used by encoding so cache stays correct.
        cache_key = f"{board.board_fen()}|{int(board.turn)}|{board.castling_xfen()}|{board.ep_square}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        board_tensor = encode_board(board).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            pred = self.model(board_tensor).squeeze(0)
        cache[cache_key] = pred
        return pred

    def _top_legal_model_moves(self, board: chess.Board, prediction: torch.Tensor, top_n: int):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return [], []

        output_size = prediction.shape[0]

        legal_by_uci = {}
        legal_indices = []
        for move in legal_moves:
            uci = move.uci()
            legal_by_uci[uci] = move
            idx = self.move_to_index(uci)
            if idx < output_size:
                legal_indices.append(idx)

        if not legal_indices:
            return legal_moves, []

        idx_tensor = torch.tensor(legal_indices, device=prediction.device, dtype=torch.long)
        legal_scores = prediction[idx_tensor]
        k = min(top_n, legal_scores.shape[0])
        top_pos = torch.topk(legal_scores, k=k).indices.tolist()

        top_moves = []
        for pos in top_pos:
            idx = legal_indices[pos]
            uci = self.idx_to_move[idx]
            move = legal_by_uci.get(uci)
            if move is not None:
                top_moves.append(move)
        return legal_moves, top_moves

    def get_best_move_from_model(self, board: chess.Board, top_n: int = 5, depth: int = 2) -> Optional[chess.Move]:
        self.board = board

        prediction_cache = {}
        prediction = self._predict_policy(board, prediction_cache)
        legal_moves, top_moves = self._top_legal_model_moves(board, prediction, top_n)

        if not legal_moves:
            return None
        if not top_moves:
            return random.choice(legal_moves)

        def model_minimax(board_, depth_, maximizing):
            if depth_ == 0 or board_.is_game_over():
                return self.evaluate_board(board_), None

            pred_ = self._predict_policy(board_, prediction_cache)
            moves_, top_moves_ = self._top_legal_model_moves(board_, pred_, top_n)
            if not moves_:
                return self.evaluate_board(board_), None
            if not top_moves_:
                top_moves_ = moves_

            best_eval = float('-inf') if maximizing else float('inf')
            best_move_ = None

            for move in top_moves_:
                board_.push(move)
                eval_, _ = model_minimax(board_, depth_ - 1, not maximizing)
                board_.pop()

                if maximizing:
                    if eval_ > best_eval:
                        best_eval = eval_
                        best_move_ = move
                else:
                    if eval_ < best_eval:
                        best_eval = eval_
                        best_move_ = move
            return best_eval, best_move_

        maximizing = board.turn == (chess.WHITE if self.is_white else chess.BLACK)
        _, best_move = model_minimax(board, depth, maximizing)
        if best_move and best_move in legal_moves:
            return best_move

        # Fallback: pick best move from the current top candidates.
        return top_moves[0] if top_moves else random.choice(legal_moves)

    def _evaluate_board_python(self, board: chess.Board) -> float:
        my_color = chess.WHITE if self.is_white else chess.BLACK
        if board.is_checkmate():
            return float('-inf') if board.turn == my_color else float('inf')

        value = 0.0
        for square, piece in board.piece_map().items():
            sign = 1.0 if piece.color == chess.WHITE else -1.0
            val = PIECE_VALUES[piece.piece_type]
            if square in CENTER_SQUARES:
                val += 0.1
            value += sign * val

        if board.is_check():
            value += 0.5 if board.turn != my_color else -0.5

        return value if self.is_white else -value

    def evaluate_board(self, board: chess.Board) -> float:
        if HAS_CYTHON_EVAL:
            return cy_evaluate_board(board, self.is_white)
        return self._evaluate_board_python(board)

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

