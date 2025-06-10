# 🚀 MayArbi Arbitrage System - Quick Reference Cheat Sheet

## 📋 **STARTUP COMMANDS**

### 🤖 **Arbitrage Servers**
```bash
# Main Enhanced Arbitrage Bot (RECOMMENDED)
python spy_enhanced_arbitrage.py

# Alternative Arbitrage Bots
python speed_optimized_arbitrage.py
python multi_chain_arbitrage_live.py
python flashloan_arbitrage_live.py
python wallet_arbitrage_live.py
```

### 📊 **Dashboard**
```bash
# Windows Dashboard (Port 9999)
cd dashboard && python app.py

# Alternative Dashboards
python windows_dashboard.py
python mev_empire_dashboard.py
python simple_dashboard.py
```

### 🔍 **DEX Scanner**
```bash
# Main DEX Scanner
python dex_scanner.py

# Speed Optimized Scanner
python speed_optimized_dex_scanner.py

# Ethereum-specific Scanner
python ethereum_dex_scanner.py

# Simple Scanner
python simple_speed_dex_scanner.py
```

## 🏗️ **SYSTEM ARCHITECTURE**

### 📁 **Core Components**
- **`src/core/`** - Master arbitrage system & batch executor
- **`src/execution/`** - Trade execution engines
- **`src/dex/`** - DEX managers & integrations
- **`src/bridges/`** - Cross-chain bridge handlers
- **`src/flashloan/`** - Flashloan providers & contracts
- **`src/wallet/`** - Wallet management & balancing
- **`src/integrations/`** - Dashboard bridge & external APIs
- **`src/monitoring/`** - Health monitoring & analytics

### 🌐 **Network Support**
- **Arbitrum** ✅ (Primary)
- **Base** ✅ (Primary) 
- **Optimism** ✅ (Primary)
- **Polygon** ✅
- **BSC** ✅
- **Ethereum** ✅ (MEV Empire)
- **Scroll, Mantle, Blast** ✅

### 💰 **Trading Strategies**
1. **Cross-Chain Arbitrage** (Primary)
2. **Flashloan Arbitrage** (Unlimited capital)
3. **DEX-to-DEX Arbitrage**
4. **MEV Strategies** (Ethereum node)
5. **Liquidation Bots**

## 🔧 **CONFIGURATION FILES**

### 📋 **Main Config**
- **`config/dex_config.json`** - DEX settings & endpoints
- **`config/capital_efficient_config.json`** - Capital management
- **`config/flash_loan_strategy_config.json`** - Flashloan settings

### 🌉 **Bridge Config**
- **`base_deployment.json`** - Base network contracts
- **`optimism_deployment.json`** - Optimism contracts
- **`deployment_info.json`** - General deployment info

## 📊 **MONITORING & DASHBOARDS**

### 🖥️ **Dashboard URLs**
- **Main Dashboard**: `http://localhost:9999`
- **MEV Empire**: `http://localhost:8080`
- **Simple Dashboard**: `http://localhost:5000`

### 📈 **Data Sources**
- **File Bridge**: `/mnt/c/temp/mayarbi_dashboard_data.json` (WSL2 → Windows)
- **MCP Knowledge Graph**: Trading patterns & insights
- **MCP Memory Service**: Historical data & learning

## 🗄️ **DATABASE FILES**
- **`arbitrum_dexes.db`** - Arbitrum DEX data
- **`base_dexes.db`** - Base DEX data  
- **`optimism_dexes.db`** - Optimism DEX data
- **`ethereum_dexes.db`** - Ethereum DEX data
- **`polygon_dexes.db`** - Polygon DEX data
- **`bsc_dexes.db`** - BSC DEX data

## 🔗 **SMART CONTRACTS**
- **`contracts/ProductionFlashloan.sol`** - Main flashloan contract
- **`contracts/MultiChainFlashloan.sol`** - Cross-chain flashloan
- **`contracts/BatchFlashloanArbitrage.sol`** - Batch execution
- **`contracts/StealthContracts/`** - MEV protection contracts

## 🛠️ **UTILITY SCRIPTS**
```bash
# Check wallet balances across chains
python check_chain_balances.py

# Deploy flashloan contracts
python deploy_flashloan_contract.py

# Clean up ports
python cleanup_ports.py

# Install dashboard dependencies
python install_dashboard_deps.py

# Test dashboard bridge
python test_dashboard_bridge.py

# Enable Ethereum WebSocket
python enable_ethereum_websocket.py
```

## 📊 **MERMAID CHARTS & DOCUMENTATION**

### 🗺️ **System Architecture Charts**
- **`memory-bank/graph TB.mmd`** - Main system flow diagram
- **`docs/02-SYSTEM-ARCHITECTURE.md`** - Detailed architecture docs
- **`PROJECT_SYSTEM_MAP.md`** - Complete system mapping
- **`MayArbi_complete_project_map.json`** - JSON project structure

### 📚 **Key Documentation**
- **`memory-bank/ONBOARDING_GUIDE_FOR_NEXT_ASSISTANT.md`** - Setup guide
- **`memory-bank/activeContext.md`** - Current work context
- **`memory-bank/progress.md`** - Project progress tracking
- **`docs/06-TRADING-STRATEGY.md`** - Trading strategy details

## 🚨 **TROUBLESHOOTING**

### 🔧 **Common Issues**
```bash
# WSL2 Dashboard Connection Issue
# Solution: File bridge at /mnt/c/temp/mayarbi_dashboard_data.json

# Port Conflicts
python cleanup_ports.py

# Missing Dependencies
pip install -r requirements.txt
cd dashboard && pip install -r requirements.txt

# Gas Price Issues
# Check config/dex_config.json gas settings

# Wallet Balance Sync
python check_chain_balances.py
```

### 📱 **Process Management**
```bash
# Check running arbitrage bots
ps aux | grep python | grep -E "(arbitrage|spy|mayarbi)"

# Check dashboard processes
ps aux | grep python | grep dashboard

# Kill specific processes
pkill -f "python.*arbitrage"
pkill -f "python.*dashboard"
```

## 🎯 **QUICK START SEQUENCE**

### 🚀 **Full System Startup**
```bash
# 1. Start Dashboard (Windows)
cd dashboard && python app.py

# 2. Start Main Arbitrage Bot (WSL2)
python spy_enhanced_arbitrage.py

# 3. Optional: Start DEX Scanner
python dex_scanner.py

# 4. Monitor at http://localhost:9999
```

### 💰 **Current Wallet Status**
- **Total Value**: $3,656.00 (CORRECTED)
- **Pre-Positioning**: WETH, USDC, USDT, PEPE ($909 each)
- **Networks**: Arbitrum, Base, Optimism, Polygon, BSC, Scroll, Mantle, Blast
- **Gas Reserves**: $20 across all chains
- **Node**: Ethereum @ 192.168.1.18:8546

### 🐸 **PRE-POSITIONING SYSTEM (NEW)**
```bash
# Enhanced Bot with Pre-Positioning
export ENABLE_REAL_TRANSACTIONS=true
python src/enhanced_arbitrage_bot_with_positioning.py
```

**Features:**
- **Lightning Execution**: Sub-second trades
- **4-Token Portfolio**: WETH, USDC, USDT, PEPE
- **Auto-Rebalancing**: Maintains 25% allocation
- **2.15x Slippage Protection**: Tuned for real conditions
- **Conservative Strategy**: $4 profit target

## 🔗 **IMPORTANT PATHS**
- **Project Root**: `/home/lylepaul78/Documents/augment-projects/MayArbi/`
- **Memory Bank**: `memory-bank/`
- **Source Code**: `src/`
- **Contracts**: `contracts/`
- **Configuration**: `config/`
- **Documentation**: `docs/`
- **Dashboard Bridge**: `/mnt/c/temp/mayarbi_dashboard_data.json`

---
*Last Updated: 2025-06-07 | Version: 1.0*
