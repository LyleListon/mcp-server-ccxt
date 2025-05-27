#!/bin/bash
# Start the MCP Memory Server with CUDA support

echo "🚀 Starting MCP Memory Server with CUDA acceleration..."

cd mcp-memory-service
source .venv/bin/activate

# Start the simplified memory server in the background
python simple_memory_server.py &
MEMORY_PID=$!

echo "📝 Memory server started with PID: $MEMORY_PID"
echo "💾 Storing PID for cleanup..."
echo $MEMORY_PID > ../data/memory_server.pid

echo "✅ MCP Memory Server is running with CUDA acceleration"
echo "🔗 Ready for arbitrage bot integration"

# Keep the script running to show logs
wait $MEMORY_PID
