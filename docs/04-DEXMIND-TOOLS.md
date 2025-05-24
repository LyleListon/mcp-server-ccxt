# 💠 DexMind MCP Tools Reference

## Tool Overview

DexMind provides 5 specialized MCP tools for arbitrage intelligence. Each tool is designed for specific aspects of trading memory and analysis.

## 💰 `store_penny_trade`

**Purpose**: Store the result of an arbitrage attempt (even $0.01 profits!)

### Input Parameters
```json
{
  "tokenA": "ETH",           // Source token symbol
  "tokenB": "USDC",          // Target token symbol  
  "dexA": "Uniswap",         // Source DEX name
  "dexB": "SushiSwap",       // Target DEX name
  "chain": "ethereum",       // Chain: ethereum|arbitrum|base|vitruveo
  "priceA": 2500.50,         // Price on source DEX
  "priceB": 2501.25,         // Price on target DEX
  "profitUSD": 0.75,         // Gross profit in USD
  "gasSpentUSD": 0.50,       // Gas cost in USD
  "wasExecuted": true        // Was trade actually executed?
}
```

### Output
```
🟢 Trade stored! PROFIT: $0.25
Pair: ETH/USDC
DEXs: Uniswap → SushiSwap
Chain: ethereum
Spread: 0.03%
```

### Why Important
- Builds the core knowledge base
- Tracks even micro-profits
- Learns from both successes and failures
- Enables pattern recognition over time

## 📊 `get_green_trades`

**Purpose**: Retrieve all profitable trades (our success stories!)

### Input Parameters
```json
{
  "limit": 50    // Optional: max trades to return (default: 50)
}
```

### Output
```
💰 Green Trades (23 found):

🟢 $0.45 | ETH/USDC | UniswapₒSushiSwap | ethereum
🟢 $0.32 | WBTA/ETH | Curve→Balancer | ethereum  
🟢 $0.28 | ARB/USDC | Camelot→TraderJoe | arbitrum
🟢 $0.15 | ETH/USDC u�Uniswap→Aerodrome | base
...
```

### Use Cases
- Review successful strategies
- Identify profitable patterns
- Celebrate wins (even small ones!)
- Share success stories

## 📈 `get_performance_stats`

**Purpose**: Get overall trading performance metrics

### Input Parameters
```json
{}  // No parameters needed
```

### Output
```
📊 DexMind Performance Stats:

Total Trades: 127
🟢 Green Trades: 73
💴 Red Trades: 54
Success Rate: 57.5%
Total Profit: $18.42
Average Profit: $0.145

🎉 In the green overall!
```

### Key Metrics
- 
📊 Success Rate**: Percentage of profitable trades
- **Total Profit**: Cumulative earnings
- 
📊 Average Profit**: Mean profit per trade
- **Trade Volume**: Total number of attempts

## 🐍 `find_best_pairs`

**Purpose**: Identify the most profitable token pairs

### Input Parameters
```json
{
  "chain": "ethereum",     // Optional: filter by chain
  "minTrades": 5          // Optional: minimum trades needed (default: 5)
}
```

### Output
```
💍 Mest pairs analysis coming soon! 
For now, check your green trades to see patterns.
```

### Future Implementation
Will analyze:
- Most profitable token pairs
- Best DEX combinations
- Optimal trading times
- Success rate by pair

## ⚡‍ `analyze_gas_efficiency`

**Purpose**: Analyze gas costs vs profits for optimization

### Input Parameters
```json
{
  "chain": "ethereum"    // Chain to analyze
}
```

### Output
```
⚡‍ Gas efficiency analysis coming soon! 
Track your gas costs in each trade.
```

### Future Implementation
Will provide:
- Gas cost trends over time
- Optimal gas price recommendations
- Profit vs gas efficiency ratios
- Best trading times for gas costs

## 🎯 Usage Examples

### Storing a Successful Trade
```
"Store a penny trade: ETH/USDC on Uniswap vs SushiSwap, 
Ethereum chain, prices 2500.50 and 2501.25, 
profit $0.75, gas $0.50, executed successfully"
```

### Analyzing Performance
```
"Show me my green trades from this week"
"What are my overall performance statistics?"
"Get my last 20 profitable trades"
```

### Pattern Discovery
```
"Find my best performing token pairs"
"Which DEX combinations are most profitable?"
"Analyze gas efficiency on Arbitrum"
```

## 🔄 Tool Integration

### With Other MCP Servers
- **Serena**: Analyze DexMind code for optimization
- 
📁 Filesystem MCP**: Export trade data for analysis
- **MCP Compass**: Discover new trading tools

### With Augment Code
- **Natural Language**: Use conversational queries
- **Context Aware**: Remembers previous analysis
- **Code Generation**: Generate trading strategies from data

## 📊 Data Flow

```
Market Opportunity → store_penny_trade → DexMind Database
                                                            ↓
Performance Analysis ← get_performance_stats ← Pattern Recognition
                                                            ↓
Strategy Optimization ← find_best_pairs ← get_green_trades
```

## 🚀 Future Tools (Planned)

### `predict_opportunity`
- Use ML to predict profitable trades
- Based on historical patterns
- Confidence scoring

### `optimize_gas_timing`
- Recommend optimal execution times
- Based on gas price patterns
- Profit vs cost analysis

### `generate_strategy`
- Create trading strategies from data
- Backtest against historical trades
- Risk assessment

**Next**: See [05-SETUP-GUIDE.md](05-SETUP-GUIDE.md) for installation instructions.