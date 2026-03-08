#!/bin/bash

# 🚀 QUICK START SCRIPT - Chess Engine

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🎉 CHESS ENGINE - QUICK START SCRIPT 🎉            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get directory
CHESS_DIR="/Users/daniellungu/Desktop/ChessEngine/ChessEngine"

echo "📁 Project directory: $CHESS_DIR"
echo ""

# Check if directories exist
if [ ! -d "$CHESS_DIR/ai-engine" ]; then
    echo "❌ ai-engine directory not found!"
    exit 1
fi

if [ ! -d "$CHESS_DIR/chess-web-ui" ]; then
    echo "❌ chess-web-ui directory not found!"
    exit 1
fi

echo "✅ All directories found!"
echo ""

# Create tmux session (if tmux available)
if command -v tmux &> /dev/null; then
    echo "🚀 Starting services with tmux..."

    # Kill existing session
    tmux kill-session -t chess 2>/dev/null

    # Create new session
    tmux new-session -d -s chess -x 200 -y 50

    # Window 1: Flask AI Engine
    tmux new-window -t chess -n "AI-Engine"
    tmux send-keys -t chess:AI-Engine "cd $CHESS_DIR/ai-engine && python3 app.py" Enter
    tmux send-keys -t chess:AI-Engine "# Flask running on http://127.0.0.1:5050" Enter

    # Window 2: Next.js Frontend
    tmux new-window -t chess -n "Frontend"
    tmux send-keys -t chess:Frontend "cd $CHESS_DIR/chess-web-ui && npm run dev" Enter
    tmux send-keys -t chess:Frontend "# Frontend running on http://localhost:3000" Enter

    echo "✅ Services started!"
    echo ""
    echo "📺 To view logs:"
    echo "   tmux attach-session -t chess:AI-Engine    # Flask logs"
    echo "   tmux attach-session -t chess:Frontend     # Frontend logs"
    echo ""
else
    echo "📋 tmux not available. Starting services manually..."
    echo ""
    echo "Open 3 separate terminals and run:"
    echo ""
    echo "Terminal 1 - Flask AI Engine:"
    echo "  cd $CHESS_DIR/ai-engine"
    echo "  python3 app.py"
    echo ""
    echo "Terminal 2 - Next.js Frontend:"
    echo "  cd $CHESS_DIR/chess-web-ui"
    echo "  npm install && npm run dev"
    echo ""
    echo "Terminal 3 - Java Backend (optional):"
    echo "  cd $CHESS_DIR/users-be"
    echo "  mvn spring-boot:run"
    echo ""
fi

echo "════════════════════════════════════════════════════════════"
echo ""
echo "🌐 OPEN IN BROWSER:"
echo "   http://localhost:3000"
echo ""
echo "📝 DEFAULT FLOW:"
echo "   1. Register: http://localhost:3000/register"
echo "   2. Login: http://localhost:3000/login"
echo "   3. Play: http://localhost:3000/play"
echo "   4. Admin: http://localhost:3000/admin"
echo "   5. Stats: http://localhost:3000/leaderboard"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "✅ Ready to use! Happy chess playing! 🎉"
echo ""

