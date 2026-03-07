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

def encode_board(board):
    """
    18‐plane feature encoding:
      planes 0–5   = white pawn, knight, bishop, rook, queen, king
      planes 6–11  = black pawn, knight, bishop, rook, queen, king
      plane 12     = turn indicator (all 1s if white to move, 0s if black)
      planes 13–16 = castling rights (white K, white Q, black k, black q)
      plane 17     = en passant square (1 at the target square, 0 elsewhere)
    Returns a torch.FloatTensor of shape [18,8,8].
    """
    arr = np.zeros((18, 8, 8), dtype=np.float32)
    # Piece planes
    for square, piece in board.piece_map().items():
        pt = piece.piece_type  # 1..6
        color = piece.color    # True=white, False=black
        plane = (pt - 1) + (0 if color else 6)
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        arr[plane, rank, file] = 1.0
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
        ep_rank = chess.square_rank(board.ep_square)
        ep_file = chess.square_file(board.ep_square)
        arr[17, ep_rank, ep_file] = 1.0
    return torch.from_numpy(arr)

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Train on Lichess PGN archive')
    p.add_argument('--pgn',          default='lichess_db.pgn', help='PGN file of games')
    p.add_argument('--epochs',       type=int, default=5)
    p.add_argument('--batch-size',   type=int, default=64)
    p.add_argument('--chunk-size',   type=int, default=100, help='Games per chunk')
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
                if chunk_idx % 5 == 0 or len(games) < args.chunk_size:
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

                # Save checkpoint every 50 chunks
                if chunk_idx % 50 == 0:
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

