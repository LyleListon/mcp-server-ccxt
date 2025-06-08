#!/bin/bash

# DEXMIND MCP Server Startup Script
# Ensures proper working directory and environment

# Change to the correct directory
cd "$(dirname "$0")"

# Verify the build exists
if [ ! -f "dist/index.js" ]; then
    echo "Error: dist/index.js not found. Run 'npm run build' first." >&2
    exit 1
fi

# Start the MCP server
exec node dist/index.js "$@"
