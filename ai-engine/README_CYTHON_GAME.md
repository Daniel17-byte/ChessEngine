# Cython Game Logic

This project can use compiled Cython modules for:
- `Game` hot paths (`auto promotion` and `reward` calculation)
- `ChessAI` board evaluation (`evaluate_board`)
- `ArchiveAlpha` board encoding (`encode_board`)

## 1) Build Cython extensions

```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/ai-engine
source venv/bin/activate
pip install -r requirements.txt
python setup_cython.py build_ext --inplace
```

## 2) Verify Game benchmark (1000 sequential games)

```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/ai-engine
source venv/bin/activate
python benchmark_game_1000.py --games 1000 --max-moves 200
```

## 3) Verify evaluation benchmark (Python vs Cython)

```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/ai-engine
source venv/bin/activate
python benchmark_eval.py --positions 300 --iterations 200
```

## 4) Verify ArchiveAlpha encode benchmark

```bash
cd /Users/daniellungu/Desktop/ChessEngine/ChessEngine/ai-engine
source venv/bin/activate
python benchmark_archivealpha_encode.py --iters 20000
```

## 5) Force Python fallbacks

```bash
export CHESS_GAME_FORCE_PYTHON=1
export CHESS_EVAL_FORCE_PYTHON=1
export CHESS_ENCODE_FORCE_PYTHON=1
python benchmark_game_1000.py --games 1000 --max-moves 200
python benchmark_eval.py --positions 300 --iterations 200
python benchmark_archivealpha_encode.py --iters 20000
```

If compiled modules are present and fallback flags are not set, Python code uses Cython automatically.
