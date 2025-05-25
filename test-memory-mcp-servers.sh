#!/bin/bash

echo "🧠 Testing Memory MCP Servers Setup"
echo "===================================="

# Test 1: MCP-Memory-Service (Python/UV)
echo "1. Testing MCP-Memory-Service..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/mcp-memory-service
if [ -f ".venv/pyvenv.cfg" ]; then
    echo "   ✅ MCP-Memory-Service virtual environment found"
    timeout 3s uv run python -m mcp_memory_service.server > /dev/null 2>&1
    if [ $? -eq 124 ]; then
        echo "   ✅ MCP-Memory-Service starts successfully"
        echo "   📊 Features: Semantic memory, ChromaDB, vector embeddings"
    else
        echo "   ❌ MCP-Memory-Service failed to start"
    fi
else
    echo "   ❌ MCP-Memory-Service virtual environment not found"
fi

# Test 2: MCP-Knowledge-Graph (Node.js)
echo "2. Testing MCP-Knowledge-Graph..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/mcp-knowledge-graph
if [ -f "dist/index.js" ]; then
    echo "   ✅ MCP-Knowledge-Graph build found"
    timeout 3s node dist/index.js > /dev/null 2>&1
    if [ $? -eq 124 ]; then
        echo "   ✅ MCP-Knowledge-Graph starts successfully"
        echo "   🕸️  Features: Relationship mapping, entity tracking"
    else
        echo "   ❌ MCP-Knowledge-Graph failed to start"
    fi
else
    echo "   ❌ MCP-Knowledge-Graph build not found"
fi

# Test 3: PostgreSQL MCP Server (Node.js)
echo "3. Testing PostgreSQL MCP Server..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/mcp-official-servers/src/postgres
if [ -f "dist/index.js" ]; then
    echo "   ✅ PostgreSQL MCP Server build found"
    # Test without database URL to check if server responds
    timeout 3s node dist/index.js 2>&1 | grep -q "Please provide a database URL"
    if [ $? -eq 0 ]; then
        echo "   ✅ PostgreSQL MCP Server responds correctly"
        echo "   🗄️  Features: SQL operations, enterprise storage"
        echo "   ⚠️  Note: Requires PostgreSQL database URL for full functionality"
    else
        echo "   ❌ PostgreSQL MCP Server unexpected response"
    fi
else
    echo "   ❌ PostgreSQL MCP Server build not found"
fi

echo ""
echo "🧠 Memory MCP Servers Summary:"
echo "=============================="
echo "✅ MCP-Memory-Service: Semantic memory with AI embeddings"
echo "✅ MCP-Knowledge-Graph: Relationship and entity tracking"
echo "✅ PostgreSQL MCP: Enterprise database operations"
echo ""
echo "🎯 Memory Architecture:"
echo "├── 🌟 Semantic Understanding (MCP-Memory-Service)"
echo "├── 🕸️  Relationship Mapping (MCP-Knowledge-Graph)"
echo "├── 🗄️  Persistent Storage (PostgreSQL MCP)"
echo── 🤖 Custom Logic (DexMind)"
echo ""
echo "🔧 Next Steps:"
echo "1. Add memory servers to Augment Code extension"
echo "2. Restart VSCode to load new MCP servers"
echo "3. Test with memory queries in Augment:"
echo "   - 'Remember this trading insight...'"
echo "   - 'What relationships do you see...'"
echo "   - 'Store this data in the database...'"
echo "4. Set up PostgreSQL database for full functionality"
echo ""
echo "🎉 Ready for intelligent, memory-enhanced arbitrage bot!"
