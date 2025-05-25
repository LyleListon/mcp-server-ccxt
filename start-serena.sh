#!/bin/bash

# Script to start Serena MCP server with proper environment isolation
cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena

# Clear Python path to avoid conflicts
unset PYTHONPATH
unset PYTHONUSERBASE

# Activate virtual environment and run serena
source .venv/bin/activate
exec python -m serena.mcp "$@"
