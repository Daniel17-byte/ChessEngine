import torch
import torch.nn as nn
import torch.nn.utils
from torch.utils.data import DataLoader, TensorDataset
import os
import sys
import json
import argparse
from collections import Counter
import random
import chess

from ChessAI import ChessAI
from ChessNet import ChessNet
from Game import Game
from ArchiveAlpha import encode_board

# Load move mapping
with open('move_mapping.json', 'r', encoding='utf-8') as f:
    move_list = json.load(f)
move_to_idx = {m: i for i, m in enumerate(move_list)}


def load_fens_from_files(filepath="generated_endgames.json"):
    fens = []
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            fens = json.load(file)
    random.shuffle(fens)
    return fens


def print_status(epoch, max_epochs, loss, acc, games, winner, stats):
    """Print status as JSON for parsing by app.py"""
    status = {
        "epoch": epoch,
        "max_epochs": max_epochs,
        "loss": round(loss, 4),
        "accuracy": round(acc, 1),
        "winner": winner,
        "moves": games,
        "white_reward": 0,
        "black_reward": 0,
        "stats": {
            "white_wins": stats.get('1-0', 0),
            "black_wins": stats.get('0-1', 0),
            "draws": stats.get('1/2-1/2', 0)
        }
    }
    print(json.dumps(status))
    sys.stdout.flush()


def play_games(ai_white, ai_black, game, fen_positions, num_games, max_moves):
    """Play N games and collect (board_state, move) samples from winning/drawing side."""
    samples_states = []
    samples_moves = []
    stats = Counter()

    for g in range(num_games):
        # Reset board
        if fen_positions:
            fen = random.choice(fen_positions)
            game.reset_from_fen(fen)
        else:
            game.reset()

        # Collect moves per side
        white_history = []  # (encoded_board, move_index)
        black_history = []
        move_count = 0

        ai_white.model.eval()

        while not game.is_game_over() and move_count < max_moves:
            move_count += 1
            is_white_turn = game.board.turn == chess.WHITE
            current_ai = ai_white if is_white_turn else ai_black

            move = current_ai.select_move(game.board)
            if not move:
                break

            move_idx = move_to_idx.get(move.uci())
            if move_idx is not None:
                board_tensor = encode_board(chess.Board(game.get_fen()))
                if is_white_turn:
                    white_history.append((board_tensor, move_idx))
                else:
                    black_history.append((board_tensor, move_idx))

            success, _ = game.make_move(move.uci())
            if not success:
                break

        result = game.get_result()
        stats[result] += 1

        # Collect samples: winner's moves as positive examples
        # Draw: use both sides (both played reasonably)
        if result == '1-0':
            samples_states.extend([s for s, _ in white_history])
            samples_moves.extend([m for _, m in white_history])
        elif result == '0-1':
            samples_states.extend([s for s, _ in black_history])
            samples_moves.extend([m for _, m in black_history])
        else:
            # Draw — use both sides
            samples_states.extend([s for s, _ in white_history])
            samples_moves.extend([m for _, m in white_history])
            samples_states.extend([s for s, _ in black_history])
            samples_moves.extend([m for _, m in black_history])

    return samples_states, samples_moves, stats


def main():
    parser = argparse.ArgumentParser(description='Mirror Match Training for Chess AI')
    parser.add_argument('--epochs', type=int, default=10, help='Number of training epochs')
    parser.add_argument('--max-moves', type=int, default=80, help='Maximum moves per game')
    parser.add_argument('--games-per-epoch', type=int, default=200, help='Games to play per epoch')
    parser.add_argument('--batch-size', type=int, default=512, help='Training batch size')
    parser.add_argument('--white-strategy', type=str, default='model')
    parser.add_argument('--black-strategy', type=str, default='model')
    parser.add_argument('--fen-type', type=str, default='endgames')
    args = parser.parse_args()

    valid_strategies = ['model', 'random', 'stockfish']
    if args.white_strategy not in valid_strategies:
        print(json.dumps({"error": f"Invalid white strategy: {args.white_strategy}"}))
        sys.exit(1)
    if args.black_strategy not in valid_strategies:
        print(json.dumps({"error": f"Invalid black strategy: {args.black_strategy}"}))
        sys.exit(1)

    valid_fen_types = ['endgames', 'normal_games', 'mixed', 'from_scratch']
    if args.fen_type not in valid_fen_types:
        print(json.dumps({"error": f"Invalid FEN type: {args.fen_type}"}))
        sys.exit(1)

    if args.fen_type == 'from_scratch':
        fen_file = "__scratch__"
    elif args.fen_type == 'endgames':
        fen_file = "generated_endgames.json"
    elif args.fen_type == 'normal_games':
        fen_file = "generated_games.json"
    else:
        fen_file = None

    print(json.dumps({
        "status": "training_start",
        "epochs": args.epochs,
        "max_moves": args.max_moves,
        "white_strategy": args.white_strategy,
        "black_strategy": args.black_strategy,
        "fen_type": args.fen_type
    }))
    sys.stdout.flush()

    # --- Shared model for both sides ---
    ai_white = ChessAI(is_white=True, default_strategy=args.white_strategy)
    ai_black = ChessAI(is_white=False, default_strategy=args.black_strategy)
    ai_black.model = ai_white.model  # shared model
    device = ai_white.device

    game = Game(ai_white, ai_black)
    all_stats = Counter()

    optimizer = torch.optim.Adam(ai_white.model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)
    criterion = nn.CrossEntropyLoss()

    # Load FEN positions
    if fen_file == "__scratch__":
        fen_positions = []
        print(json.dumps({"info": "Training from scratch — all games start from standard position"}))
    elif fen_file:
        fen_positions = load_fens_from_files(fen_file)
    else:
        fen_positions = load_fens_from_files("generated_endgames.json") + load_fens_from_files("generated_games.json")
        random.shuffle(fen_positions)

    if not fen_positions:
        print(json.dumps({"warning": "No FEN positions found, using standard start"}))
        fen_positions = []

    for epoch in range(args.epochs):
        # --- Phase 1: Play games, collect winning moves ---
        states, moves, stats = play_games(
            ai_white, ai_black, game, fen_positions,
            num_games=args.games_per_epoch,
            max_moves=args.max_moves
        )
        all_stats += stats

        if len(states) == 0:
            print(json.dumps({"warning": f"Epoch {epoch+1}: no training samples collected"}))
            sys.stdout.flush()
            continue

        # --- Phase 2: Batch train on collected samples (like Stockfish trainer) ---
        states_tensor = torch.stack(states).to(device)       # [N, 18, 8, 8]
        moves_tensor = torch.tensor(moves, dtype=torch.long, device=device)  # [N]

        dataset = TensorDataset(states_tensor, moves_tensor)
        dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)

        ai_white.model.train()
        total_loss = 0.0
        correct = 0
        total_samples = 0

        for batch_idx, (X, y) in enumerate(dataloader):
            optimizer.zero_grad()
            outputs = ai_white.model(X)
            loss = criterion(outputs, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(ai_white.model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()
            total_samples += X.size(0)
            _, predicted = outputs.max(1)
            correct += predicted.eq(y).sum().item()

            if (batch_idx + 1) % 5 == 0 or (batch_idx + 1) == len(dataloader):
                acc = 100.0 * correct / total_samples
                print(
                    f"Batch {batch_idx+1}/{len(dataloader)} | "
                    f"Loss: {loss.item():.4f} | "
                    f"Avg Loss: {total_loss / (batch_idx+1):.4f} | "
                    f"Acc: {acc:.1f}% | "
                    f"Samples: {total_samples}"
                )
                sys.stdout.flush()

        scheduler.step()
        avg_loss = total_loss / max(len(dataloader), 1)
        acc = 100.0 * correct / max(total_samples, 1)

        last_result = list(stats.keys())[-1] if stats else '*'
        winner = "White" if last_result == "1-0" else "Black" if last_result == "0-1" else "Draw"

        print_status(epoch + 1, args.epochs, avg_loss, acc, len(states), winner, all_stats)

        if (epoch + 1) % 10 == 0:
            torch.save(ai_white.model.state_dict(), "chessnet.pth")
            print(json.dumps({"status": "model_saved", "epoch": epoch + 1}))
            sys.stdout.flush()

    torch.save(ai_white.model.state_dict(), "chessnet.pth")
    print(json.dumps({"status": "training_complete", "total_epochs": args.epochs}))
    sys.stdout.flush()

    # Cleanup
    if hasattr(ai_white, 'engine') and ai_white.engine:
        ai_white.engine.quit()
    if hasattr(ai_black, 'engine') and ai_black.engine:
        ai_black.engine.quit()


if __name__ == "__main__":
    main()
