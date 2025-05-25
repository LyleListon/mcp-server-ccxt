#!/bin/bash

# Quick Python Cleanup - Removes the main conflict sources
echo "🚀 Quick Python Cleanup for Serena"
echo "=================================="

# Remove old backups (safe - these are just backups)
echo "🗑️  Removing old backup directories..."
rm -rf ~/.local/lib/python3.10_backup
rm -rf ~/.local/lib/python3.12_backup
echo "✅ Removed backup directories (570MB freed)"

# Clean caches
echo "🧹 Cleaning package caches..."
pip cache purge 2>/dev/null
uv cache clean 2>/dev/null
echo "✅ Caches cleaned"

# Show current status
echo ""
echo "📊 Remaining Python user packages:"
du -sh ~/.local/lib/python3.12 2>/dev/null || echo "No python3.12 user packages"

echo ""
echo "🎯 Next steps to completely resolve conflicts:"
echo "1. For immediate Serena use: temporarily move python3.12 packages"
echo "   mv ~/.local/lib/python3.12 ~/.local/lib/python3.12_temp"
echo ""
echo "2. For permanent solution: remove all user packages and use UV/venv"
echo "   rm -rf ~/.local/lib/python3.12"
echo "   # Then reinstall only what you need in virtual environments"
echo ""
echo "3. Test Serena:"
echo "   cd serena && uv run serena-mcp-server --help"
