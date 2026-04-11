#!/bin/bash
# Build all Cython extensions for the chess AI engine.
# Usage: ./build.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════════════════"
echo "  Building Cython extensions..."
echo "═══════════════════════════════════════════════════════"

# Clean old builds
rm -f fastgame/*.so fastgame/*.pyd
rm -rf build/

# Build with optimizations
python setup_cython.py build_ext --inplace 2>&1

# Verify
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Verifying compiled modules..."
echo "═══════════════════════════════════════════════════════"

python -c "
modules = [
    'fastgame.board_encode',
    'fastgame.game_core',
    'fastgame.game_eval',
    'fastgame.fast_training_loop',
]
ok = 0
for m in modules:
    try:
        __import__(m)
        print(f'  ✅ {m}')
        ok += 1
    except ImportError as e:
        print(f'  ❌ {m}: {e}')
print(f'\n  {ok}/{len(modules)} modules compiled successfully.')
"

echo ""
echo "  Done! Run: python benchmark_game_1000.py --games 1000"
echo "═══════════════════════════════════════════════════════"

