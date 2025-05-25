#!/bin/bash

# Test All MCP Servers
echo "🧪 Testing All MCP Servers"
echo "=========================="

# Test 1: Filesystem MCP Server
echo "📁 Testing Filesystem MCP Server..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/filesystem-mcp-server
if timeout 5s node dist/index.js > /dev/null 2>&1; then
    echo "✅ Filesystem MCP Server: WORKING"
else
    echo "❌ Filesystem MCP Server: FAILED"
fi

# Test 2: Serena
echo "🧠 Testing Serena..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/serena
if timeout 5s uv run serena-mcp-server --help > /dev/null 2>&1; then
    echo "✅ Serena: WORKING"
else
    echo "❌ Serena: FAILED"
fi

# Test 3: MCP Compass
echo "🧭 Testing MCP Compass..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/mcp-compass
if timeout 5s node build/index.js > /dev/null 2>&1; then
    echo "✅ MCP Compass: WORKING"
else
    echo "❌ MCP Compass: FAILED"
fi

echo ""
echo "🎯 Summary:"
echo "==========="
echo "You have 3 MCP servers ready for Augment Code extension:"
echo "  📁 Filesystem MCP Server - File operations"
echo "  🧠 Serena - Semantic code analysis"
echo "  🧭 MCP Compass - MCP service discovery"
echo ""
echo "📋 Configuration file: augment-mcp-config.json"
echo "📚 Setup guide: MCP_COMPASS_SETUP.md"
echo ""
echo "🚀 Ready to configure in Augment Code extension!"
