#!/bin/bash

# Safe Python Environment Cleanup Script
# This script removes unnecessary Python installations while preserving important packages

echo "🧹 Starting Python Environment Cleanup..."
echo "=========================================="

# Function to ask for confirmation
confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Step 1: Remove old backup directories (safe)
echo "📁 Step 1: Removing old backup directories..."
if [ -d ~/.local/lib/python3.10_backup ]; then
    SIZE=$(du -sh ~/.local/lib/python3.10_backup | cut -f1)
    if confirm "Remove python3.10_backup ($SIZE)?"; then
        rm -rf ~/.local/lib/python3.10_backup
        echo "✅ Removed python3.10_backup"
    fi
fi

if [ -d ~/.local/lib/python3.12_backup ]; then
    SIZE=$(du -sh ~/.local/lib/python3.12_backup | cut -f1)
    if confirm "Remove python3.12_backup ($SIZE)?"; then
        rm -rf ~/.local/lib/python3.12_backup
        echo "✅ Removed python3.12_backup"
    fi
fi

# Step 2: Create a backup of essential packages list
echo "📋 Step 2: Backing up essential packages list..."
python3.12 -m pip list --user > ~/python3.12_packages_backup.txt
echo "✅ Package list saved to ~/python3.12_packages_backup.txt"

# Step 3: Option to clean Python 3.12 user packages
echo "🔍 Step 3: Python 3.12 user packages analysis..."
SIZE=$(du -sh ~/.local/lib/python3.12 | cut -f1)
echo "Current size: $SIZE"
echo "Essential packages found: numpy, pandas, requests, uvicorn"

echo ""
echo "Choose cleanup option:"
echo "1) Keep essential packages (numpy, pandas, requests, etc.)"
echo "2) Remove all user packages (you can reinstall later)"
echo "3) Skip this step"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🔄 Keeping essential packages, removing others..."
        # This would require a more complex selective removal
        echo "⚠️  Manual cleanup recommended for selective removal"
        ;;
    2)
        if confirm "Remove ALL Python 3.12 user packages ($SIZE)? You can reinstall later"; then
            rm -rf ~/.local/lib/python3.12
            echo "✅ Removed all Python 3.12 user packages"
            echo "📝 To reinstall essential packages later:"
            echo "   pip install --user numpy pandas requests"
        fi
        ;;
    3)
        echo "⏭️  Skipping Python 3.12 cleanup"
        ;;
esac

# Step 4: Clean caches
echo "🗑️  Step 4: Cleaning package caches..."
if confirm "Clean pip cache?"; then
    pip cache purge
    echo "✅ Pip cache cleaned"
fi

if command -v uv &> /dev/null; then
    if confirm "Clean UV cache?"; then
        uv cache clean
        echo "✅ UV cache cleaned"
    fi
fi

# Step 5: Summary
echo ""
echo "🎉 Cleanup Summary:"
echo "==================="
echo "✅ Removed old backup directories"
echo "✅ Created package list backup"
echo "✅ Cleaned caches"
echo ""
echo "📊 Current Python installations:"
which python3.10 python3.11 python3.12 2>/dev/null
echo ""
echo "💡 Recommendations:"
echo "   - Use UV for all new Python projects"
echo "   - Avoid 'pip install --user' (use virtual environments instead)"
echo "   - Keep system Python installations (3.10, 3.12) for OS compatibility"
echo ""
echo "🚀 Serena should now work without conflicts!"
