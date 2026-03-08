#!/bin/bash

echo "🧹 Cleaning up Chess Engine Web UI..."

# Remove src/pages directory
if [ -d "src/pages" ]; then
    echo "Removing src/pages/ directory..."
    rm -rf src/pages/
    echo "✅ src/pages/ deleted"
else
    echo "ℹ️  src/pages/ not found (already deleted)"
fi

# Remove Next.js build cache
if [ -d ".next" ]; then
    echo "Removing .next/ build cache..."
    rm -rf .next/
    echo "✅ .next/ deleted"
else
    echo "ℹ️  .next/ not found"
fi

echo ""
echo "✨ Cleanup complete!"
echo ""
echo "Next steps:"
echo "1. npm install"
echo "2. npm run dev"
echo ""

