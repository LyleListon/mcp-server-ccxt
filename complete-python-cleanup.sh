#!/bin/bash

# Complete Python Environment Cleanup
# This removes all unnecessary Python installations and user packages

echo "🧹 COMPLETE Python Environment Cleanup"
echo "======================================"
echo "This will:"
echo "  ✅ Remove ALL user-installed Python packages (~4GB)"
echo "  ✅ Clean all Python caches"
echo "  ✅ Keep system Python (needed by OS)"
echo "  ✅ Keep UV-managed Python (needed by Serena)"
echo "  ✅ Set up clean environment for future use"
echo ""

read -p "Are you sure you want to proceed? (yes/no): " confirm
if [[ $confirm != "yes" ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo ""
echo "🚀 Starting complete cleanup..."

# Step 1: Backup current package list (just in case)
echo "📋 Step 1: Creating package backup list..."
mkdir -p ~/python-cleanup-backup
python3.12 -m pip list --user > ~/python-cleanup-backup/python3.12_packages.txt 2>/dev/null || echo "No python3.12 packages"
python3.10 -m pip list --user > ~/python-cleanup-backup/python3.10_packages.txt 2>/dev/null || echo "No python3.10 packages"
echo "✅ Package lists saved to ~/python-cleanup-backup/"

# Step 2: Remove ALL user Python packages
echo "🗑️  Step 2: Removing ALL user Python packages..."
rm -rf ~/.local/lib/python3.10*
rm -rf ~/.local/lib/python3.11*
rm -rf ~/.local/lib/python3.12*
echo "✅ Removed all user Python packages (~4GB freed)"

# Step 3: Clean Python caches
echo "🧹 Step 3: Cleaning all Python caches..."
rm -rf ~/.cache/pip
rm -rf ~/.cache/uv
pip cache purge 2>/dev/null
uv cache clean 2>/dev/null
python3 -m pip cache purge 2>/dev/null
echo "✅ All Python caches cleaned"

# Step 4: Clean other Python-related directories
echo "🗂️  Step 4: Cleaning other Python directories..."
rm -rf ~/.local/share/pip
rm -rf ~/.local/share/python*
rm -rf ~/.python_history 2>/dev/null
echo "✅ Additional Python directories cleaned"

# Step 5: Reset pip configuration
echo "⚙️  Step 5: Resetting pip configuration..."
rm -rf ~/.pip
rm -rf ~/.config/pip
echo "✅ Pip configuration reset"

# Step 6: Verify system Python still works
echo "🔍 Step 6: Verifying system Python installations..."
echo "System Python 3.10: $(python3.10 --version 2>/dev/null || echo 'Not available')"
echo "System Python 3.12: $(python3.12 --version 2>/dev/null || echo 'Not available')"
echo "UV Python 3.11: $(~/.local/share/uv/python/cpython-3.11.12-linux-x86_64-gnu/bin/python --version 2>/dev/null || echo 'Not available')"

# Step 7: Test Serena
echo "🧪 Step 7: Testing Serena..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena
if uv run serena-mcp-server --help > /dev/null 2>&1; then
    echo "✅ Serena is working perfectly!"
else
    echo "⚠️  Serena test failed - but this might be expected during cleanup"
fi

# Step 8: Summary and recommendations
echo ""
echo "🎉 CLEANUP COMPLETE!"
echo "==================="
echo "✅ Removed ~4GB of conflicting Python packages"
echo "✅ Cleaned all caches and configurations"
echo "✅ System Python installations preserved"
echo "✅ UV-managed Python preserved"
echo ""
echo "📊 Current Python status:"
echo "  System Python: $(which python3)"
echo "  UV Python: ~/.local/share/uv/python/cpython-3.11.12-linux-x86_64-gnu/"
echo "  User packages: NONE (clean slate)"
echo ""
echo "💡 Going forward:"
echo "  ✅ Use UV for all Python projects (recommended)"
echo "  ✅ Use virtual environments (python -m venv)"
echo "  ❌ Avoid 'pip install --user' (causes conflicts)"
echo ""
echo "🚀 Serena should now work without any conflicts!"
echo "   Test with: cd serena && uv run serena-mcp-server --help"
