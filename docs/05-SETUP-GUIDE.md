# Setup Guide

## Prerequisites
- Node.js 18+
- Python 3.11+
- UV package manager
- Git

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/LyleListon/MayArbi.git
cd MayArbi
```

### 2. Install DexMind
```bash
cd dexmind
npm install
npm run build
cd ..
```

### 3. Install Other MCP Servers
```bash
# Filesystem MCP
cd filesystem-mcp-server
npm install
npm run build
cd ..

# Serena
cd serena
uv sync
cd ..

# MCP Compass
cd mcp-compass
npm install
npm run build
cd ..
```

## Configuration

Add to Augment Code extension:

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
      "args": ["run", "--directory", "/path/to/MayArbi/serena", "serena-mcp-server"]
    },
    "mcp-compass": {
      "command": "node",
      "args": ["/path/to/MayArbi/mcp-compass/build/index.js"]
    }
  }
}
```

## Testing

Test DexMind:
```bash
cd dexmind
node dist/index.js
```

Test in Augment:
```
"Get DexMind performance stats"
"Store a test penny trade"
```

## Next Steps

1. Read [01-PROJECT-OVERVIEW.md](01-PROJECT-OVERVIEW.md)
2. Explore [04-DEXMIND-TOOLS.md](04-DEXMIND-TOOLS.md)
3. Plan with [06-TRADING-STRATEGY.md](06-TRADING-STRATEGY.md)

Ready to hunt pennies! 🎾💰