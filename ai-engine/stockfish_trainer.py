import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from ChessNet import ChessNet
import chess
import chess.engine


# ===== Dataset =====
class FENDataset(Dataset):
    def __init__(self, fens, engine_path, time_limit=0.2, mapping_path="move_mapping.json"):
        self.fens = fens
        self.time_limit = time_limit

        # === încărcăm mapping-ul mutărilor ===
        with open(mapping_path) as f:
            self.idx_to_move = json.load(f)
        self.move_to_idx = {uci: i for i, uci in enumerate(self.idx_to_move)}
        self.n_moves = len(self.idx_to_move)   # număr real de mutări

        # === pornim Stockfish dacă există ===
        if os.path.exists(engine_path):
            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        else:
            self.engine = None
            print(f"Warning: Stockfish nu a fost găsit la {engine_path}. Folosim mutări dummy.")

    def __len__(self):
        return len(self.fens)

    def __getitem__(self, idx):
        fen = self.fens[idx]
        board_tensor = self.fen_to_tensor(fen)

        best_move = self.get_stockfish_move(fen)
        move_idx = self.move_to_index(best_move)

        return board_tensor, move_idx

    def fen_to_tensor(self, fen):
        piece_to_idx = {
            "P": 0, "N": 1, "B": 2, "R": 3, "Q": 4, "K": 5,
            "p": 6, "n": 7, "b": 8, "r": 9, "q": 10, "k": 11
        }
        board_tensor = torch.zeros(12, 8, 8, dtype=torch.float32)
        rows = fen.split(" ")[0].split("/")
        for i, row in enumerate(rows):
            col = 0
            for c in row:
                if c.isdigit():
                    col += int(c)
                else:
                    board_tensor[piece_to_idx[c], i, col] = 1.0
                    col += 1
        return board_tensor

    def get_stockfish_move(self, fen):
        if self.engine is None:
            return "0000"
        board = chess.Board(fen)
        if board.is_game_over():
            return "0000"
        result = self.engine.play(board, chess.engine.Limit(time=self.time_limit))
        if result.move is None:
            return "0000"
        return result.move.uci()

    def move_to_index(self, move_uci: str) -> int:
        # fallback la index 0 dacă mutarea nu există în mapping
        return self.move_to_idx.get(move_uci, 0)

    def __del__(self):
        if hasattr(self, "engine") and self.engine is not None:
            self.engine.quit()


# ===== Utils =====
def load_fens_from_files(filepath="generated_games.json"):
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            return json.load(file)
    return []


# ===== Parametri =====
batch_size = 256      # mic pentru debug
epochs = 2           # mic pentru debug
lr = 1e-3
engine_path = "/opt/homebrew/bin/stockfish"
model_path = "chessnet.pth"

# ===== Încarcăm FEN-urile =====
fens = load_fens_from_files("generated_games.json")
if len(fens) == 0:
    raise ValueError("Fișierul generated_games.json este gol sau nu există!")

dataset = FENDataset(fens, engine_path=engine_path)
dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

# ===== Model, loss, optimizer =====
n_moves = dataset.n_moves   # determinat din mapping
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Device folosit: {device}, număr mutări posibile: {n_moves}")

model = ChessNet(n_moves).to(device)
optimizer = optim.Adam(model.parameters(), lr=lr)
criterion = nn.CrossEntropyLoss()

# ===== Încarcă model existent dacă există =====
if os.path.exists(model_path):
    model.load_state_dict(torch.load(model_path, map_location=device))
    print("Modelul existent a fost încărcat, continuăm antrenarea.")

save_every = 256
processed = 0

# ===== Antrenare =====
for epoch in range(epochs):
    total_loss = 0
    print(f"===== EPOCH {epoch+1} =====")
    for i, (X, y) in enumerate(dataloader):
        X, y = X.to(device), y.to(device)

        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        processed += X.size(0)  # numărul de FEN-uri procesate

        print(
            f"Batch {i+1}/{len(dataloader)} | "
            f"Loss: {loss.item():.4f} | "
            f"Outputs sum: {outputs.sum().item():.1f} | "
            f"Labels sum: {y.sum().item()} | "
            f"FEN processed: {processed}"
        )

        if processed % save_every == 0:
            torch.save(model.state_dict(), model_path)
            print(f"Model salvat după {processed} FEN-uri procesate.")

    print(f"Epoch {epoch+1} - Average Loss: {total_loss/len(dataloader):.4f}\n")

# ===== Salvăm modelul =====
torch.save(model.state_dict(), model_path)
print(f"Model salvat în '{model_path}'")
