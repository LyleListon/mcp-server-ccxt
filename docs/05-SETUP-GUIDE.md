# ⚙️ MayArbi Setup Guide

## 🎯 Prerequisites

### Required Software
- **Node.js 18+** - For TypeScript MCP servers
- **Python 3.11+** - For Serena (managed by UV)
- **UV** - Python package manager (for Serena)
- **Git** - For cloning repositories

### Required Access
- **Augment Code Extension** - Primary AI interface
- **VSCode Insiders** - Recommended IDE
- **Ethereum Node** - Direct access (optional but recommended)
- **Vitruveo Node** - Direct access (optional but recommended)

## 📥 Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/LyleListon/MayArbi.git
cd MayArbi
```

### 2. Install DexMind (Core Memory System)
```bash
cd dexmind
npm install
npm run build
cd ..
```

### 3. Install Supporting MCP Servers

#### Filesystem MCP Server
```bash
cd filesystem-mcp-server
npm install
npm run build
cd ..
```

#### Serena (Semantic Analysis)
```bash
cd serena
uv sync
cd ..
```

#### MCP Compass (Service Discovery)
```bash
cd mcp-compass
npm install
npm run build
cd ..
```

## ⚙️ Configuration

### 1. Augment Code Extension Setup

Add all MCP servers to your Augment configuration:

```json
{
  "mcpServers": {
    "dexmind": {
      "command": "node",
      "args": ["/path/to/MayArbi/dexmind/dist/index.js"]
    },
    "filesystem-mcp-server": {
      "command": "node", 
      "args": ["/path/to/MayArbi/filesystem-mcp-server/dist/index.js"]
    },
    "serena": {
      "command": "/home/user/.local/bin/uv",
      "args": [
        "run", "--directory", "/path/to/MayArbi/serena",
        "serena-mcp-server"
      ]
    },
    "mcp-compass": {
      "command": "node",
      "args": ["/path/to/MayArbi/mcp-compass/build/index.js"]
    }
  }
}
```

### 2. Environment Variables (Optional)

Create `.env` file in project root:
```bash
# Node endpoints (if you have direct access)
ETHEREUM_NODE_URL=http://localhost:8545
VITRUVEO_NODE_URL=http://localhost:8546

# RPC endpoints for other chains
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
BASE_RPC_URL=https://mainnet.base.org

# DexMind configuration
DEXMIND_DB_PATH=./data/dexmind.db
DEXMIND_LOG_LEVEL=info
```

## 🧪 Testing the Setup

### 1. Test DexMind
```bash
cd dexmind
node dist/index.js
# Should show: "🧠 DexMind MCP Server running - Ready to hunt pennies! 🎯"
```

### 2. Test All MCP Servers
```bash
./test-all-mcp-servers.sh
```

Expected output:
```
🧪 Testing All MCP Servers
==========================
📁 Filesystem MCP Server: ✅ WORKING
🧠 Serena: ✅ WORKING  
🧭 MCP Compass: ✅ WORKING
🧠 DexMind: ✅ WORKING
```

### 3. Test Augment Integration

In Augment Code extension:
```
"Test DexMind by getting performance stats"
"Show me available MCP tools"
"Store a test penny trade"
```

## 🎯 First Steps

### 1. Initialize DexMind
```
"Get DexMind performance stats to initialize the database"
```

### 2. Store Your First Trade
```
"Store a penny trade: ETH/USDC on Uniswap vs SushiSwap, 
Ethereum chain, prices 2500 and 2501, profit $1, gas $0.50, 
executed successfully"
```

### 3. Check Your Success
```
"Show me my green trades"
"Get performance statistics"
```

## 🔧 Troubleshooting

### Common Issues

#### DexMind Won't Start
```bash
# Check Node.js version
node --version  # Should be 18+

# Rebuild if needed
cd dexmind
npm run build
```

#### Serena Issues
```bash
# Check UV installation
uv --version

# Reinstall if needed
cd serena
rm -rf .venv
uv sync
```

#### MCP Connection Issues
- Verify file paths in Augment configuration
- Check that all servers built successfully
- Restart Augment Code extension

### Getting Help

1. **Check logs** in each MCP server directory
2. **Test individual servers** before integration
3. **Verify permissions** on all executable files
4. **Review configuration** paths and syntax

## 🚀 Next Steps

Once setup is complete:

1. **Read the documentation** - Start with [01-PROJECT-OVERVIEW.md](01-PROJECT-OVERVIEW.md)
2. **Explore DexMind tools** - See [04-DEXMIND-TOOLS.md](04-DEXMIND-TOOLS.md)
3. **Plan your strategy** - Review [06-TRADING-STRATEGY.md](06-TRADING-STRATEGY.md)
4. **Start small** - Begin with micro-arbitrage opportunities

## 📊 Verification Checklist

- [ ] All MCP servers build successfully
- [ ] Augment Code extension connects to all servers
- [ ] DexMind database initializes
- [ ] Can store and retrieve test trades
- [ ] Performance stats display correctly
- [ ] All tools respond to queries

**You're ready to start hunting for those profitable pennies!** 🎯💰

**Next**: See [06-TRADING-STRATEGY.md](06-TRADING-STRATEGY.md) for strategy planning.
