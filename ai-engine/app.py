from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from Game import Game
import chess
from ChessAI import ChessAI
import json
import threading
from datetime import datetime
import subprocess
import sys
import os
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

ai_white = None
ai_black = ChessAI(is_white=False, default_strategy="model")
game = Game(ai_white, ai_black)

# Track player color for current game (white or black)
player_color = chess.WHITE  # Default: player is white

# Training state
training_state = {
    "is_training": False,
    "strategy": None,
    "epochs": 0,
    "max_epochs": 0,
    "games_played": 0,
    "wins_white": 0,
    "wins_black": 0,
    "draws": 0,
    "loss_value": 0.0,
    "accuracy": 0.0,
    "start_time": None,
    "current_status": "idle"
}

def emit_training_status():
    """Broadcast training state to all connected WebSocket clients"""
    socketio.emit("training_status", training_state)

# ELO estimation state
elo_state = {
    "is_running": False,
    "current_level": 0,
    "max_level": 10,
    "games_per_level": 20,
    "current_game": 0,
    "results": {},
    "estimated_elo": None,
    "status": "idle"
}

def emit_elo_status():
    """Broadcast ELO estimation state to all connected WebSocket clients"""
    socketio.emit("elo_status", elo_state)

def friendly_strategy(name):
    """Convert strategy ID to display name"""
    return {"model": "Danibot", "stockfish": "Stockfish", "random": "Random"}.get(name, name)


@app.route('/api/game/set_player_color', methods=['POST'])
def set_player_color():
    """Set which color the player is playing as"""
    global player_color
    data = request.get_json()
    color = data.get('color', 'white')
    player_color = chess.WHITE if color == 'white' else chess.BLACK
    print(f"🎮 Player color set to: {color.upper()}")
    return jsonify({'message': f'Player is now playing as {color.upper()}'})

@app.route('/api/game/get_board', methods=['GET'])
def get_board():
    return jsonify({
        'board': game.get_board_fen(),
        'turn': 'white' if game.board.turn == chess.WHITE else 'black',
        'is_check': game.board.is_check(),
        'is_checkmate': game.board.is_checkmate(),
        'is_stalemate': game.board.is_stalemate(),
        'is_insufficient_material': game.board.is_insufficient_material()
    })

@app.route('/api/game/make_move', methods=['POST'])
def make_move():
    print("\n==============================")
    print("🔵 [API] POST /make_move")

    data = request.get_json()
    move = data.get('move')

    # Validate move format
    if not move or len(move) < 4:
        print("❌ No move provided or invalid format.")
        return jsonify({'error': 'No move provided'}), 400

    # Check if it's player's turn
    if game.board.turn != player_color:
        print(f"❌ Not player's turn! Current turn: {'WHITE' if game.board.turn == chess.WHITE else 'BLACK'}")
        return jsonify({
            'error': "It's not your turn!",
            'board': game.get_board_fen(),
            'turn': 'white' if game.board.turn == chess.WHITE else 'black'
        }), 400


    print(f"➡️  Player move received: {move}")

    try:
        chess_move = chess.Move.from_uci(move)
        if chess_move not in game.board.legal_moves:
            print("❌ Move is not legal.")
            return jsonify({'error': 'Illegal move', 'board': game.get_board_fen()}), 400

        success, move_info = game.make_move(move)
        print(f"✅ Player move valid: {success}")

        if not success:
            print(f"❌ Invalid move attempted: {move_info}")
            print("==============================")
            return jsonify({'error': move_info if isinstance(move_info, str) else 'Invalid move', 'board': game.get_board_fen()}), 400

        # After player move, check if AI should move
        if not game.is_game_over():
            # Determine which AI should move
            ai_color = chess.BLACK if player_color == chess.WHITE else chess.WHITE

            if ai_color == chess.BLACK and game.ai_black:
                ai_move = game.ai_move(chess.BLACK)
                print(f"🤖 AI (Black) moved: {ai_move}")
            elif ai_color == chess.WHITE and game.ai_white:
                ai_move = game.ai_move(chess.WHITE)
                print(f"🤖 AI (White) moved: {ai_move}")
            else:
                ai_move = None

            print("==============================")
            return jsonify({
                'board': game.get_board_fen(),
                'result': 'Move successful',
                'ai_move': ai_move,
                'turn': 'white' if game.board.turn == chess.WHITE else 'black',
                'is_check': game.board.is_check(),
                'is_checkmate': game.board.is_checkmate(),
                'is_stalemate': game.board.is_stalemate(),
                'is_insufficient_material': game.board.is_insufficient_material()
            })
        else:
            print("🏁 Game is over!")
            print("==============================")
            return jsonify({
                'board': game.get_board_fen(),
                'result': 'Game over',
                'turn': 'white' if game.board.turn == chess.WHITE else 'black',
                'is_check': game.board.is_check(),
                'is_checkmate': game.board.is_checkmate(),
                'is_stalemate': game.board.is_stalemate(),
                'is_insufficient_material': game.board.is_insufficient_material()
            })
    except Exception as e:
        print(f"🔥 Exception occurred: {e}")
        print("==============================")
        return jsonify({'error': str(e), 'board': game.get_board_fen()}), 500

@app.route('/api/game/reset', methods=['POST'])
def reset():
    game.reset()
    return jsonify({
        'message': 'Board reset',
        'board': game.get_board_fen(),
        'turn': 'white' if game.board.turn == chess.WHITE else 'black',
        'is_check': game.board.is_check(),
        'is_checkmate': game.board.is_checkmate(),
        'is_stalemate': game.board.is_stalemate(),
        'is_insufficient_material': game.board.is_insufficient_material()
    })

@app.route('/api/game/start_new_game', methods=['POST'])
def start_new_game():
    """Start a new game with specified settings."""
    global player_color, game
    data = request.get_json()
    game_type = data.get('gameType', 'ai')
    color = data.get('playerColor', 'white')
    ai_strategy = data.get('aiStrategy', 'model')  # "model" = Danibot, "stockfish" = Stockfish

    # Validate player color from request
    if color not in ['white', 'black']:
        return jsonify({'error': 'Invalid player color'}), 400

    # Validate AI strategy
    if ai_strategy not in ['model', 'stockfish']:
        ai_strategy = 'model'

    # Set player color dynamically based on request
    player_color = chess.WHITE if color == 'white' else chess.BLACK
    print(f"🎮 Starting new game. Player color: {color.upper()}, Game type: {game_type.upper()}, AI: {ai_strategy}")

    # Reset the game — AI uses the selected strategy
    ai_white = ChessAI(is_white=True, default_strategy=ai_strategy) if game_type == 'ai' and player_color == chess.BLACK else None
    ai_black = ChessAI(is_white=False, default_strategy=ai_strategy) if game_type == 'ai' and player_color == chess.WHITE else None
    game = Game(ai_white, ai_black)

    # If player is black, AI (white) needs to make the first move
    ai_first_move = None
    if player_color == chess.BLACK and ai_white is not None:
        ai_first_move = game.ai_move(chess.WHITE)
        print(f"🤖 AI (White) made first move: {ai_first_move}")

    return jsonify({
        'message': 'New game started',
        'playerColor': color,
        'gameType': game_type,
        'board': game.get_board_fen(),
        'ai_move': ai_first_move,
        'turn': 'white' if game.board.turn == chess.WHITE else 'black'
    })

@app.route('/api/admin/training/status', methods=['GET'])
def get_training_status():
    """Get current training status"""
    return jsonify(training_state)

@app.route('/api/admin/training/start', methods=['POST'])
def start_training():
    """Start model training with specified strategy and parameters"""
    global training_state

    if training_state["is_training"]:
        return jsonify({'error': 'Training already in progress'}), 400

    data = request.get_json()
    strategy = data.get('strategy', 'mirror_match')
    epochs = data.get('epochs', 100)
    max_moves = data.get('max_moves', 80)
    white_strategy = data.get('white_strategy', 'model')
    black_strategy = data.get('black_strategy', 'model')
    fen_type = data.get('fen_type', 'endgames')

    training_state["is_training"] = True
    training_state["strategy"] = strategy
    training_state["epochs"] = 0
    training_state["max_epochs"] = epochs
    training_state["games_played"] = 0
    training_state["wins_white"] = 0
    training_state["wins_black"] = 0
    training_state["draws"] = 0
    training_state["loss_value"] = 0.0
    training_state["accuracy"] = 0.0
    training_state["start_time"] = datetime.now().isoformat()
    training_state["current_status"] = f"Starting {strategy} training with {friendly_strategy(white_strategy)} vs {friendly_strategy(black_strategy)}..."

    # Start training in background thread
    thread = threading.Thread(
        target=run_training,
        args=(strategy, epochs, max_moves, white_strategy, black_strategy, fen_type)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'message': 'Training started',
        'strategy': strategy,
        'epochs': epochs,
        'max_moves': max_moves,
        'white_strategy': white_strategy,
        'black_strategy': black_strategy,
        'fen_type': fen_type,
        'status': training_state
    })

@app.route('/api/admin/training/stop', methods=['POST'])
def stop_training():
    """Stop training"""
    global training_state
    training_state["is_training"] = False
    training_state["current_status"] = "Training stopped by user"
    emit_training_status()
    return jsonify({'message': 'Training stopped', 'status': training_state})

@app.route('/api/admin/training/logs', methods=['GET'])
def get_training_logs():
    """Get training logs"""
    try:
        with open('training_log.json', 'r') as f:
            logs = json.load(f)
        return jsonify({'logs': logs})
    except FileNotFoundError:
        return jsonify({'logs': []})

@app.route('/api/admin/strategies', methods=['GET'])
def get_strategies():
    """Get available training strategies"""
    return jsonify({
        'strategies': [
            {
                'id': 'mirror_match',
                'name': 'Mirror Match',
                'description': 'Train two identical models against each other',
                'recommended_epochs': 100
            },
            {
                'id': 'stockfish_trainer',
                'name': 'Stockfish Trainer',
                'description': 'Train model by playing against Stockfish engine',
                'recommended_epochs': 50
            },
            {
                'id': 'archive_alpha',
                'name': 'Archive Alpha',
                'description': 'Train model from a database of real Lichess games (121K+ games)',
                'recommended_epochs': 3
            }
        ]
    })

def run_training(strategy, epochs, max_moves, white_strategy, black_strategy, fen_type):
    """Run training in background"""
    global training_state
    try:
        if strategy == 'mirror_match':
            run_mirror_match_training(epochs, max_moves, white_strategy, black_strategy, fen_type)
        elif strategy == 'stockfish_trainer':
            run_stockfish_training(epochs)
        elif strategy == 'archive_alpha':
            run_archive_alpha_training(epochs)
        # Only set completed if no exception occurred
        training_state["current_status"] = "Training completed"
    except Exception as e:
        training_state["current_status"] = f"Error: {str(e)}"
    finally:
        training_state["is_training"] = False
        emit_training_status()

def run_mirror_match_training(epochs, max_moves, white_strategy, black_strategy, fen_type):
    """Run MirrorMatch.py with specified parameters"""
    global training_state
    training_state["current_status"] = f"Starting Mirror Match: {friendly_strategy(white_strategy)} vs {friendly_strategy(black_strategy)}..."

    try:
        script_path = "MirrorMatch.py"

        if not os.path.exists(script_path):
            training_state["current_status"] = f"Error: {script_path} not found"
            return

        # Build command with parameters
        cmd = [
            sys.executable,
            script_path,
            "--epochs", str(epochs),
            "--max-moves", str(max_moves),
            "--games-per-epoch", "50",
            "--batch-size", "64",
            "--white-strategy", white_strategy,
            "--black-strategy", black_strategy,
            "--fen-type", fen_type
        ]

        print(f"Running: {' '.join(cmd)}")

        # Run the script and capture output in real-time
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Parse output from MirrorMatch.py in real-time
        for line in process.stdout:
            if not training_state["is_training"]:
                process.terminate()
                break

            line = line.strip()
            if not line:
                continue

            print(f"🔵 MirrorMatch: {line}")

            # Try to parse as JSON first (epoch summary, model_saved, training_complete)
            try:
                data = json.loads(line)

                if "status" in data and data["status"] == "model_saved":
                    print(f"✅ Model saved at epoch {data.get('epoch', '?')}")

                elif "status" in data and data["status"] == "training_complete":
                    print(f"💾 Training completed after {data.get('total_epochs', '?')} epochs")

                elif "epoch" in data:
                    epoch = data.get("epoch", 0)
                    max_ep = data.get("max_epochs", epochs)
                    loss = data.get("loss", 0.0)
                    acc = data.get("accuracy", 0.0)
                    stats = data.get("stats", {})
                    winner = data.get("winner", "Draw")
                    samples = data.get("moves", 0)

                    training_state["epochs"] = epoch
                    training_state["max_epochs"] = max_ep
                    training_state["loss_value"] = loss
                    training_state["accuracy"] = acc
                    training_state["games_played"] = samples
                    training_state["wins_white"] = stats.get("white_wins", 0)
                    training_state["wins_black"] = stats.get("black_wins", 0)
                    training_state["draws"] = stats.get("draws", 0)

                    winner_emoji = "⚪ White" if winner == "White" else "⚫ Black" if winner == "Black" else "🤝 Draw"
                    training_state["current_status"] = (
                        f"Mirror Match ({friendly_strategy(white_strategy)} vs {friendly_strategy(black_strategy)}): "
                        f"Epoch {epoch}/{max_ep} | "
                        f"Loss: {loss:.4f} | Acc: {acc:.1f}% | "
                        f"{winner_emoji} | "
                        f"⚪{stats.get('white_wins', 0)} ⚫{stats.get('black_wins', 0)} 🤝{stats.get('draws', 0)}"
                    )
                    emit_training_status()

                continue  # Successfully parsed as JSON, skip plain-text parsing

            except json.JSONDecodeError:
                pass

            # Plain text: parse Batch progress lines
            try:
                batch_match = re.search(r'Batch\s+(\d+)/(\d+)', line)
                if batch_match:
                    batch_num = int(batch_match.group(1))
                    total_batches = int(batch_match.group(2))

                    avg_loss_match = re.search(r'Avg Loss:\s*([0-9.]+)', line)
                    if avg_loss_match:
                        training_state["loss_value"] = float(avg_loss_match.group(1))

                    acc_match = re.search(r'Acc:\s*([0-9.]+)%', line)
                    if acc_match:
                        training_state["accuracy"] = float(acc_match.group(1))

                    training_state["current_status"] = (
                        f"Mirror Match ({friendly_strategy(white_strategy)} vs {friendly_strategy(black_strategy)}): "
                        f"Epoch {training_state['epochs']}/{training_state['max_epochs']} | "
                        f"Batch {batch_num}/{total_batches} | "
                        f"Loss: {training_state['loss_value']:.4f} | "
                        f"Acc: {training_state['accuracy']:.1f}%"
                    )
                    if batch_num % 5 == 0 or batch_num == total_batches:
                        emit_training_status()
            except Exception as e:
                print(f"Parse error: {e}")

        # Wait for process to complete
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("⚠️ Mirror Match process stuck, force killing...")
            process.kill()
            process.wait()

        # Check if script saved the model
        if os.path.exists("chessnet.pth"):
            training_state["current_status"] = "✅ Mirror Match training completed! Model saved."
            print("💾 Model saved successfully")
        else:
            training_state["current_status"] = "✅ Mirror Match training completed"
        emit_training_status()

    except Exception as e:
        training_state["current_status"] = f"❌ Error: {str(e)}"
        print(f"❌ Mirror Match error: {str(e)}")
        raise

def run_stockfish_training(epochs):
    """Run stockfish_trainer.py with specified epochs"""
    global training_state
    training_state["current_status"] = "Starting Stockfish training..."

    try:
        script_path = "stockfish_trainer.py"

        if not os.path.exists(script_path):
            training_state["current_status"] = f"Error: {script_path} not found"
            return

        # Run stockfish trainer with epochs from UI
        process = subprocess.Popen(
            [sys.executable, script_path, "--epochs", str(epochs)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        epoch_count = 0

        # Parse output from stockfish_trainer.py
        for line in process.stdout:
            if not training_state["is_training"]:
                process.terminate()
                break

            line = line.strip()
            if not line:
                continue

            print(f"🔵 Stockfish: {line}")

            # Parse training output
            try:
                # Parse Epoch summary line: "Epoch 1/5 - Average Loss: 0.1234"
                epoch_match = re.search(r'Epoch\s+(\d+)/(\d+)', line)
                if epoch_match:
                    epoch_count = int(epoch_match.group(1))
                    total = int(epoch_match.group(2))
                    training_state["epochs"] = epoch_count
                    training_state["max_epochs"] = total

                # Parse loss from any line (Avg Loss preferred)
                avg_loss_match = re.search(r'Avg Loss:\s*([0-9.]+)', line)
                if avg_loss_match:
                    training_state["loss_value"] = float(avg_loss_match.group(1))
                else:
                    loss_match = re.search(r'Loss:\s*([0-9.]+)', line)
                    if loss_match:
                        training_state["loss_value"] = float(loss_match.group(1))

                # Parse accuracy: "Acc: 80.0%" or "Accuracy: 80.0%"
                acc_match = re.search(r'Acc(?:uracy)?:\s*([0-9.]+)%', line)
                if acc_match:
                    training_state["accuracy"] = float(acc_match.group(1))

                # Parse batch progress
                batch_match = re.search(r'Batch\s+(\d+)/(\d+)', line)
                if batch_match:
                    batch_num = int(batch_match.group(1))
                    total_batches = int(batch_match.group(2))
                    training_state["current_status"] = (
                        f"Stockfish: Epoch {epoch_count}/{training_state['max_epochs']} | "
                        f"Batch {batch_num}/{total_batches} | "
                        f"Loss: {training_state['loss_value']:.4f} | "
                        f"Acc: {training_state['accuracy']:.1f}%"
                    )
                    # Emit every 5 batches to avoid flooding
                    if batch_num % 5 == 0 or batch_num == total_batches:
                        emit_training_status()
                elif epoch_match:
                    training_state["current_status"] = (
                        f"Stockfish: Epoch {epoch_count}/{training_state['max_epochs']} | "
                        f"Loss: {training_state['loss_value']:.4f} | "
                        f"Acc: {training_state['accuracy']:.1f}%"
                    )
                    emit_training_status()

                # Parse FEN processed count
                fen_match = re.search(r'FEN processed:\s*(\d+)', line)
                if fen_match:
                    training_state["games_played"] = int(fen_match.group(1))

            except Exception as e:
                print(f"Parse error: {e}")

        # Wait for process with timeout, force kill if stuck
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("⚠️ Stockfish trainer process stuck, force killing...")
            process.kill()
            process.wait()

        if os.path.exists("chessnet.pth"):
            training_state["current_status"] = "✅ Stockfish training completed! Model saved."
        else:
            training_state["current_status"] = "✅ Stockfish training completed"
        emit_training_status()

    except Exception as e:
        training_state["current_status"] = f"Error: {str(e)}"
        print(f"❌ Stockfish error: {str(e)}")
        raise

def run_archive_alpha_training(epochs):
    """Run ArchiveAlpha.py with specified epochs"""
    global training_state
    training_state["current_status"] = "Starting Archive Alpha training..."

    try:
        # First check if ArchiveAlpha.py needs to be run with generate_pgn first
        script_path = "ArchiveAlpha.py"

        if not os.path.exists(script_path):
            training_state["current_status"] = f"Error: {script_path} not found"
            return

        # Run Archive Alpha script
        process = subprocess.Popen(
            [sys.executable, script_path, "--epochs", str(epochs)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        epoch_count = 0

        # Parse output from ArchiveAlpha.py
        for line in process.stdout:
            if not training_state["is_training"]:
                process.terminate()
                break

            line = line.strip()
            if not line:
                continue

            print(f"🔵 Archive Alpha: {line}")

            try:
                # Parse Epoch header: "===== EPOCH 1/5 ====="
                epoch_match = re.search(r'EPOCH\s+(\d+)/(\d+)', line)
                if epoch_match:
                    epoch_count = int(epoch_match.group(1))
                    total = int(epoch_match.group(2))
                    training_state["epochs"] = epoch_count
                    training_state["max_epochs"] = total

                # Parse Epoch summary: "Epoch 1/5 - Avg Loss: 2.3 - Accuracy: 15.2%"
                epoch_summary = re.search(r'Epoch\s+(\d+)/(\d+)\s*-\s*Avg Loss:\s*([0-9.]+)\s*-\s*Accuracy:\s*([0-9.]+)%', line)
                if epoch_summary:
                    epoch_count = int(epoch_summary.group(1))
                    training_state["epochs"] = epoch_count
                    training_state["max_epochs"] = int(epoch_summary.group(2))
                    training_state["loss_value"] = float(epoch_summary.group(3))
                    training_state["accuracy"] = float(epoch_summary.group(4))
                    training_state["current_status"] = (
                        f"Archive Alpha: Epoch {epoch_count}/{training_state['max_epochs']} | "
                        f"Loss: {training_state['loss_value']:.4f} | "
                        f"Acc: {training_state['accuracy']:.1f}%"
                    )
                    emit_training_status()
                    continue

                # Parse Avg Loss from any line
                avg_loss_match = re.search(r'Avg Loss:\s*([0-9.]+)', line)
                if avg_loss_match:
                    training_state["loss_value"] = float(avg_loss_match.group(1))

                # Parse accuracy
                acc_match = re.search(r'Acc(?:uracy)?:\s*([0-9.]+)%', line)
                if acc_match:
                    training_state["accuracy"] = float(acc_match.group(1))

                # Parse Batch/chunk progress
                batch_match = re.search(r'Batch\s+(\d+)', line)
                if batch_match:
                    batch_num = int(batch_match.group(1))
                    training_state["current_status"] = (
                        f"Archive Alpha: Epoch {epoch_count}/{training_state['max_epochs']} | "
                        f"Chunk {batch_num} | "
                        f"Loss: {training_state['loss_value']:.4f} | "
                        f"Acc: {training_state['accuracy']:.1f}%"
                    )
                    if batch_num % 5 == 0:
                        emit_training_status()

                # Parse FEN processed count
                fen_match = re.search(r'FEN processed:\s*(\d+)', line)
                if fen_match:
                    training_state["games_played"] = int(fen_match.group(1))

            except Exception as e:
                print(f"Parse error: {e}")

        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("⚠️ Archive Alpha process stuck, force killing...")
            process.kill()
            process.wait()

        if os.path.exists("chessnet.pth"):
            training_state["current_status"] = "✅ Archive Alpha training completed! Model saved."
        else:
            training_state["current_status"] = "✅ Archive Alpha training completed"
        emit_training_status()

    except Exception as e:
        training_state["current_status"] = f"Error: {str(e)}"
        print(f"❌ Archive Alpha error: {str(e)}")
        raise

@app.route('/api/admin/elo/start', methods=['POST'])
def start_elo_estimation():
    """Start ELO estimation in background"""
    global elo_state

    if elo_state["is_running"]:
        return jsonify({'error': 'ELO estimation already in progress'}), 400

    data = request.get_json() or {}
    games_per_level = data.get('games_per_level', 20)
    max_level = data.get('max_level', 10)

    elo_state["is_running"] = True
    elo_state["games_per_level"] = games_per_level
    elo_state["max_level"] = max_level
    elo_state["current_level"] = 0
    elo_state["current_game"] = 0
    elo_state["results"] = {}
    elo_state["estimated_elo"] = None
    elo_state["status"] = "Starting ELO estimation..."
    emit_elo_status()

    thread = threading.Thread(target=run_elo_estimation, args=(games_per_level, max_level))
    thread.daemon = True
    thread.start()

    return jsonify({'message': f'ELO estimation started: {games_per_level} games/level, levels 0-{max_level}'})

@app.route('/api/admin/elo/stop', methods=['POST'])
def stop_elo_estimation():
    """Stop ELO estimation"""
    global elo_state
    elo_state["is_running"] = False
    elo_state["status"] = "Stopped by user"
    emit_elo_status()
    return jsonify({'message': 'ELO estimation stopped'})

@app.route('/api/admin/elo/status', methods=['GET'])
def get_elo_status():
    """Get current ELO estimation status"""
    return jsonify(elo_state)

def run_elo_estimation(games_per_level, max_level):
    """Run ELO estimation in background thread"""
    global elo_state
    import chess.engine as ce

    SKILL_TO_ELO = {
        0: 800, 1: 900, 2: 1000, 3: 1050, 4: 1100,
        5: 1200, 6: 1300, 7: 1400, 8: 1500, 9: 1600,
        10: 1700, 11: 1800, 12: 1900, 13: 2000, 14: 2100,
        15: 2200, 16: 2400, 17: 2600, 18: 2800, 19: 3000, 20: 3200,
    }

    engine_path = "/opt/homebrew/bin/stockfish"

    try:
        danibot = ChessAI(is_white=True, default_strategy='model')
        danibot.epsilon = 0.0  # No random moves during evaluation

        if not os.path.exists(engine_path):
            elo_state["status"] = "❌ Stockfish not found"
            elo_state["is_running"] = False
            emit_elo_status()
            return

        engine = ce.SimpleEngine.popen_uci(engine_path)

        for level in range(0, max_level + 1):
            if not elo_state["is_running"]:
                break

            elo_state["current_level"] = level
            elo_approx = SKILL_TO_ELO.get(level, "?")
            elo_state["status"] = f"Testing vs Stockfish Level {level} (ELO ~{elo_approx})..."
            emit_elo_status()

            try:
                engine.configure({"Skill Level": level})
            except Exception:
                pass

            wins, draws, losses = 0, 0, 0

            for g in range(games_per_level):
                if not elo_state["is_running"]:
                    break

                elo_state["current_game"] = g + 1
                elo_state["status"] = (
                    f"Level {level} (ELO ~{elo_approx}) | "
                    f"Game {g+1}/{games_per_level} | "
                    f"Score: {wins}W/{draws}D/{losses}L"
                )
                if (g + 1) % 2 == 0:
                    emit_elo_status()

                board = chess.Board()
                danibot_is_white = (g % 2 == 0)
                move_count = 0

                while not board.is_game_over() and move_count < 150:
                    move_count += 1
                    if (board.turn == chess.WHITE) == danibot_is_white:
                        move = danibot.get_best_move_from_model(board)
                        if move is None or move not in board.legal_moves:
                            legal = list(board.legal_moves)
                            move = legal[0] if legal else None
                    else:
                        result = engine.play(board, ce.Limit(time=0.01))
                        move = result.move

                    if move is None:
                        break
                    board.push(move)

                result = board.result()
                if result == "1-0":
                    if danibot_is_white:
                        wins += 1
                    else:
                        losses += 1
                elif result == "0-1":
                    if danibot_is_white:
                        losses += 1
                    else:
                        wins += 1
                else:
                    draws += 1

            total = wins + draws + losses
            wr = (wins + 0.5 * draws) / max(total, 1)

            elo_state["results"][str(level)] = {
                "wins": wins, "draws": draws, "losses": losses,
                "win_rate": round(wr, 3),
                "elo": SKILL_TO_ELO.get(level, 0)
            }
            emit_elo_status()

            print(f"⚡ ELO Test: Level {level} ({elo_approx}) → {wins}W/{draws}D/{losses}L (WR: {wr*100:.1f}%)")

            # Stop early if getting crushed
            if wr < 0.15 and level >= 2:
                elo_state["status"] = f"Stopped at level {level} — Danibot outmatched"
                break

        engine.quit()
        if hasattr(danibot, 'engine') and danibot.engine:
            danibot.engine.quit()

        # Calculate estimated ELO
        best_level = 0
        best_diff = float('inf')
        for lvl_str, data in elo_state["results"].items():
            diff = abs(data["win_rate"] - 0.5)
            if diff < best_diff:
                best_diff = diff
                best_level = int(lvl_str)

        base_elo = SKILL_TO_ELO.get(best_level, 800)
        wr_at_best = elo_state["results"].get(str(best_level), {}).get("win_rate", 0.5)

        if wr_at_best > 0.5 and best_level + 1 in SKILL_TO_ELO:
            next_elo = SKILL_TO_ELO[best_level + 1]
            estimated = base_elo + (next_elo - base_elo) * (wr_at_best - 0.5) * 2
        elif wr_at_best < 0.5 and best_level - 1 in SKILL_TO_ELO:
            prev_elo = SKILL_TO_ELO[best_level - 1]
            estimated = base_elo - (base_elo - prev_elo) * (0.5 - wr_at_best) * 2
        else:
            estimated = base_elo

        elo_state["estimated_elo"] = round(estimated)
        elo_state["status"] = f"✅ Estimated ELO: {elo_state['estimated_elo']}"

    except Exception as e:
        elo_state["status"] = f"❌ Error: {str(e)}"
        print(f"❌ ELO estimation error: {e}")
    finally:
        elo_state["is_running"] = False
        emit_elo_status()


@socketio.on('connect')
def handle_connect():
    """Send current training status when a client connects"""
    emit('training_status', training_state)
    emit('elo_status', elo_state)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5050, host='0.0.0.0', allow_unsafe_werkzeug=True)
