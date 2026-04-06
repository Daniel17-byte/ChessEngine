import argparse
import sys
import chess
import chess.pgn
import numpy as np
import torch
import torch.nn as nn
import torch.nn.utils
from ChessNet import ChessNet
from torch.utils.data import Dataset, DataLoader
import os
import json

USE_CYTHON_ENCODE = os.getenv("CHESS_ENCODE_FORCE_PYTHON", "0") != "1"
if USE_CYTHON_ENCODE:
    try:
        from fastgame.board_encode import encode_board_array as cy_encode_board_array
        HAS_CYTHON_ENCODE = True
    except ImportError:
        cy_encode_board_array = None
        HAS_CYTHON_ENCODE = False
else:
    cy_encode_board_array = None
    HAS_CYTHON_ENCODE = False

try:
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    njit = None
    HAS_NUMBA = False

# ── dataset utilities ─────────────────────────────────────────────────────────

class ChessDataset(Dataset):
    def __init__(self, samples, move2idx):
        """
        samples: list of (fen, uci)
        move2idx: dict mapping uci→int label
        """
        # Filter out moves not in our mapping
        self.samples = [(fen, uci) for fen, uci in samples if uci in move2idx]
        self.move2idx = move2idx

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        fen, uci = self.samples[idx]
        board = chess.Board(fen)
        x = encode_board(board)              # [18×8×8] float tensor
        y = self.move2idx[uci]               # integer label
        return x, y

def _encode_board_numpy(board):
    """Fast NumPy encoding using bitboards."""
    arr = np.zeros((18, 8, 8), dtype=np.float32)

    # Piece planes from bitboards (python-chess stores them as uint64 masks)
    piece_specs = (
        (chess.PAWN, chess.WHITE, 0),
        (chess.KNIGHT, chess.WHITE, 1),
        (chess.BISHOP, chess.WHITE, 2),
        (chess.ROOK, chess.WHITE, 3),
        (chess.QUEEN, chess.WHITE, 4),
        (chess.KING, chess.WHITE, 5),
        (chess.PAWN, chess.BLACK, 6),
        (chess.KNIGHT, chess.BLACK, 7),
        (chess.BISHOP, chess.BLACK, 8),
        (chess.ROOK, chess.BLACK, 9),
        (chess.QUEEN, chess.BLACK, 10),
        (chess.KING, chess.BLACK, 11),
    )

    for piece_type, color, plane in piece_specs:
        bb = board.pieces_mask(piece_type, color)
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            arr[plane, sq // 8, sq % 8] = 1.0
            bb ^= lsb

    # Turn indicator
    if board.turn == chess.WHITE:
        arr[12, :, :] = 1.0

    # Castling rights
    if board.has_kingside_castling_rights(chess.WHITE):
        arr[13, :, :] = 1.0
    if board.has_queenside_castling_rights(chess.WHITE):
        arr[14, :, :] = 1.0
    if board.has_kingside_castling_rights(chess.BLACK):
        arr[15, :, :] = 1.0
    if board.has_queenside_castling_rights(chess.BLACK):
        arr[16, :, :] = 1.0

    # En passant
    if board.ep_square is not None:
        arr[17, board.ep_square // 8, board.ep_square % 8] = 1.0

    return arr


if HAS_NUMBA:
    @njit(cache=True)
    def _fill_piece_planes_numba(arr, masks):
        for plane in range(12):
            bb = masks[plane]
            for sq in range(64):
                if (bb >> sq) & np.uint64(1):
                    arr[plane, sq // 8, sq % 8] = 1.0


    def _encode_board_numba(board):
        arr = np.zeros((18, 8, 8), dtype=np.float32)
        masks = np.array([
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
        ], dtype=np.uint64)

        _fill_piece_planes_numba(arr, masks)

        if board.turn == chess.WHITE:
            arr[12, :, :] = 1.0
        if board.has_kingside_castling_rights(chess.WHITE):
            arr[13, :, :] = 1.0
        if board.has_queenside_castling_rights(chess.WHITE):
            arr[14, :, :] = 1.0
        if board.has_kingside_castling_rights(chess.BLACK):
            arr[15, :, :] = 1.0
        if board.has_queenside_castling_rights(chess.BLACK):
            arr[16, :, :] = 1.0
        if board.ep_square is not None:
            arr[17, board.ep_square // 8, board.ep_square % 8] = 1.0

        return arr


def encode_board(board):
    """
    18-plane feature encoding with Cython/Numba/NumPy fallback.
    Returns a torch.FloatTensor of shape [18,8,8].
    """
    if HAS_CYTHON_ENCODE:
        arr = cy_encode_board_array(board)
    elif HAS_NUMBA:
        arr = _encode_board_numba(board)
    else:
        arr = _encode_board_numpy(board)
    return torch.from_numpy(arr)

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Train on Lichess PGN archive')
    p.add_argument('--pgn',          default='lichess_2350plus.pgn', help='PGN file of games')
    p.add_argument('--epochs',       type=int, default=10, help='Number of training epochs')
    p.add_argument('--batch-size',   type=int, default=256, help='Positions per batch')
    p.add_argument('--chunk-size',   type=int, default=300, help='Games per chunk')
    p.add_argument('--lr',           type=float, default=1e-3)
    p.add_argument('--model-path',   default='chessnet.pth', help='Path to save/load model')
    args = p.parse_args()

    # ── Load move mapping ─────────────────────────────────────────────────
    print("Loading move mappings from move_mapping.json...")
    sys.stdout.flush()
    with open('move_mapping.json', 'r', encoding='utf-8') as fmap:
        move_list = json.load(fmap)
    move2idx = {m: i for i, m in enumerate(move_list)}
    n_moves = len(move_list)
    print(f"Loaded {n_moves} moves from mapping file.")
    sys.stdout.flush()

    # ── Check PGN file ────────────────────────────────────────────────────
    if not os.path.exists(args.pgn):
        print(f"❌ PGN file not found: {args.pgn}")
        print("Download a Lichess database from https://database.lichess.org/")
        sys.stdout.flush()
        sys.exit(1)

    # ── Device ────────────────────────────────────────────────────────────
    if torch.backends.mps.is_available():
        device = torch.device('mps')
    elif torch.cuda.is_available():
        device = torch.device('cuda')
    else:
        device = torch.device('cpu')
    print(f"Device: {device}, moves: {n_moves}")
    sys.stdout.flush()

    # ── Single shared model (consistent with rest of app) ─────────────────
    model = ChessNet(n_moves).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    criterion = nn.CrossEntropyLoss()

    # Load existing model if available
    if os.path.exists(args.model_path):
        try:
            model.load_state_dict(torch.load(args.model_path, map_location=device))
            print(f"✅ Existing model loaded from {args.model_path}")
        except (RuntimeError, KeyError) as e:
            print(f"⚠️ Could not load old model: {e}")
            print("Architecture changed — training from scratch.")
    sys.stdout.flush()

    # ── Chunked training over PGN ─────────────────────────────────────────
    for epoch in range(args.epochs):
        print(f"===== EPOCH {epoch+1}/{args.epochs} =====")
        sys.stdout.flush()

        epoch_loss = 0.0
        epoch_correct = 0
        epoch_total = 0
        epoch_batches = 0
        chunk_idx = 0

        with open(args.pgn, 'r', encoding='utf-8') as f:
            while True:
                # Read a chunk of games
                games = []
                for _ in range(args.chunk_size):
                    g = chess.pgn.read_game(f)
                    if g is None:
                        break
                    games.append(g)

                if not games:
                    break

                chunk_idx += 1

                # Collect (fen, move) samples from ALL positions, both colors
                samples = []
                for game in games:
                    board = game.board()
                    for move in game.mainline_moves():
                        uci = move.uci()
                        if uci in move2idx:
                            samples.append((board.fen(), uci))
                        board.push(move)

                if not samples:
                    continue

                # Create DataLoader for this chunk
                dataset = ChessDataset(samples, move2idx)
                loader = DataLoader(
                    dataset,
                    batch_size=args.batch_size,
                    shuffle=True,
                    num_workers=0,
                    pin_memory=False
                )

                # Train on this chunk
                model.train()
                chunk_loss = 0.0
                chunk_correct = 0
                chunk_total = 0

                for batch_idx, (xb, yb) in enumerate(loader):
                    xb, yb = xb.to(device), yb.to(device)

                    optimizer.zero_grad()
                    logits = model(xb)
                    loss = criterion(logits, yb)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()

                    chunk_loss += loss.item()
                    chunk_total += xb.size(0)
                    _, predicted = logits.max(1)
                    chunk_correct += predicted.eq(yb).sum().item()

                epoch_loss += chunk_loss
                epoch_correct += chunk_correct
                epoch_total += chunk_total
                epoch_batches += len(loader)

                chunk_acc = 100.0 * chunk_correct / max(chunk_total, 1)
                chunk_avg_loss = chunk_loss / max(len(loader), 1)

                # Print progress every chunk
                if chunk_idx % 10 == 0 or len(games) < args.chunk_size:
                    total_acc = 100.0 * epoch_correct / max(epoch_total, 1)
                    total_avg_loss = epoch_loss / max(epoch_batches, 1)
                    print(
                        f"Batch {chunk_idx} | "
                        f"Chunk: {len(games)} games, {len(samples)} positions | "
                        f"Loss: {chunk_avg_loss:.4f} | "
                        f"Avg Loss: {total_avg_loss:.4f} | "
                        f"Acc: {total_acc:.1f}% | "
                        f"FEN processed: {epoch_total}"
                    )
                    sys.stdout.flush()

                # Save checkpoint every 100 chunks
                if chunk_idx % 100 == 0:
                    torch.save(model.state_dict(), args.model_path)
                    print(f"💾 Checkpoint saved at chunk {chunk_idx}")
                    sys.stdout.flush()

        # End of epoch
        if epoch_total > 0:
            avg_loss = epoch_loss / max(epoch_batches, 1)
            acc = 100.0 * epoch_correct / epoch_total
            print(f"Epoch {epoch+1}/{args.epochs} - Avg Loss: {avg_loss:.4f} - Accuracy: {acc:.1f}% - Positions: {epoch_total}")
        else:
            print(f"Epoch {epoch+1}/{args.epochs} - No positions processed")
        sys.stdout.flush()

        # Save after each epoch
        torch.save(model.state_dict(), args.model_path)
        print(f"💾 Model saved to {args.model_path}")
        sys.stdout.flush()

    print(f"✅ Training complete! Model saved to '{args.model_path}'")
    sys.stdout.flush()


if __name__ == '__main__':
    main()

