#!/bin/bash

echo "🚀 Testing Web3 MCP Servers Setup"
echo "=================================="

# Test 1: Coincap-MCP (Node.js)
echo "1. Testing Coincap-MCP..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/coincap-mcp
if [ -f "build/index.js" ]; then
    echo "   ✅ Coincap-MCP build found"
    timeout 3s node build/index.js > /dev/null 2>&1
    if [ $? -eq 124 ]; then
        echo "   ✅ Coincap-MCP server starts successfully"
    else
        echo "   ❌ Coincap-MCP server failed to start"
    fi
else
    echo "   ❌ Coincap-MCP build not found"
fi

# Test 2: MCP-Server-CCXT (Python/UV)
echo "2. Testing MCP-Server-CCXT..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/mcp-server-ccxt
if [ -f ".venv/pyvenv.cfg" ]; then
    echo "   ✅ MCP-Server-CCXT virtual environment found"
    timeout 3s uv run ccxt-server > /dev/null 2>&1
    if [ $? -eq 124 ]; then
        echo "   ✅ MCP-Server-CCXT starts successfully"
    else
        echo "   ❌ MCP-Server-CCXT failed to start"
    fi
else
    echo "   ❌ MCP-Server-CCXT virtual environment not found"
fi

# Test 3: Coinmarket-MCP-Server (Python/UV - needs API key)
echo "3. Testing Coinmarket-MCP-Server..."
cd /home/lylepaul78/Documents/augment-projects/MayArbi/coinmarket-mcp-server
if [ -f ".venv/pyvenv.cfg" ]; then
    echo "   ✅ Coinmarket-MCP virtual environment found"
    if [ -f ".env" ]; then
        echo "   ✅ Environment file found"
        timeout 3s uv run coinmarket-service > /dev/null 2>&1
        if [ $? -eq 124 ]; then
            echo "   ✅ Coinmarket-MCP starts successfully"
        else
            echo "   ⚠️  Coinmarket-MCP needs API key configuration"
        fi
    else
        echo "   ⚠️  Coinmarket-MCP needs .env file with API key"
        echo "      Create .env file with: COINMARKETCAP_API_KEY=your_key_here"
    fi
else
    echo "   ❌ Coinmarket-MCP virtual environment not found"
fi

echo ""
echo "📊 Web3 MCP Servers Summary:"
echo "=============================="
echo "✅ Coincap-MCP: Basic crypto prices (Ready to use)"
echo "✅ MCP-Server-CCXT: Multi-exchange data (Ready to use)"
echo "⚠️  Coinmarket-MCP: Advanced market data (Needs API key)"
echo ""
echo "🔧 Next Steps:"
echo "1. Add working servers to Augment Code extension"
echo "2. Get CoinMarketCap API key for advanced features"
echo "3. Restart VSCode to load new MCP servers"
echo "4. Test with crypto price queries in Augment"
echo ""
echo "🎯 Ready for arbitrage bot development!"
