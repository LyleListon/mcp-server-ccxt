#!/bin/bash

# Completely isolated Serena MCP server startup script
# This avoids all Python environment conflicts

cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena

# Completely isolate from user packages and system conflicts
export PYTHONNOUSERSITE=1
export PYTHONPATH=""
export PYTHONUSERBASE=""
unset PYTHONHOME

# Use uv with explicit Python version and isolation
exec /home/lylepaul78/.local/bin/uv run --python 3.11 --isolated python -m serena.mcp "$@"
