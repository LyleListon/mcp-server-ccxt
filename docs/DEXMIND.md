# 🧠 DexMind - Custom MCP Memory Server Documentation

## 🎯 Overview

**DexMind** is a custom Model Context Protocol (MCP) memory server specifically designed for DEX arbitrage operations. It serves as the "brain" of the MayArbi system, remembering every trade, pattern, and insight to continuously improve trading performance.

## 🌟 Core Philosophy

> **"Every penny counts, every pattern matters"**

DexMind operates on the principle that even the smallest profitable trades contain valuable information. By tracking micro-arbitrage opportunities (even $0.01 profits), it builds a comprehensive understanding of market dynamics.

## 🏗️ Architecture

### Memory Storage
- **Database**: SQLite for reliability and speed
- **Schema**: Optimized for trading data and analytics
- **Indexing**: Fast queries on time, profit, and chain data
- **Backup**: Automatic data protection

### MCP Integration
- **Protocol**: Standard MCP server implementation
- **Tools**: 5+ specialized trading tools
- **Transport**: Stdio for seamless AI integration
- **Compatibility**: Works with Augment Code extension

## 📊 Data Models

### PennyTrade
The core data structure tracking every arbitrage attempt:

```typescript
interface PennyTrade {
  id: string;                    // Unique trade identifier
  tokenA: string;                // Source token symbol
  tokenB: string;                // Target token symbol
  dexA: string;                  // Source DEX name
  dexB: string;                  // Target DEX name
  chain: 'ethereum' | 'arbitrum' | 'base' | 'vitruveo';
  
  // Price data
  priceA: number;                // Price on source DEX
  priceB: number;                // Price on target DEX
  priceSpreadPercent: number;    // Calculated spread percentage
  
  // Profit tracking
  profitUSD: number;             // Gross profit in USD
  gasSpentUSD: number;           // Gas cost in USD
  netProfitUSD: number;          // Net profit (profit - gas)
  
  // Success metrics
  wasGreen: boolean;             // TRUE = profitable trade
  wasExecuted: boolean;          // Was trade actually executed
  
  // Timing
  timestamp: Date;               // When opportunity was detected
  blockNumber?: number;          // Blockchain block number
}
```

### GasTracker
Monitors gas costs across chains for optimization:

```typescript
interface GasTracker {
  chain: string;                 // Blockchain name
  averageGasPrice: number;       // Average gas price in gwei
  timestamp: Date;               // When recorded
  transactionCost: number;       // Total transaction cost in USD
}
```

### ArbitrageOpportunity
Tracks detected opportunities before execution:

```typescript
interface ArbitrageOpportunity {
  id: string;                    // Unique opportunity ID
  tokenPair: string;             // Token pair (e.g., "ETH/USDC")
  buyDex: string;                // Where to buy
  sellDex: string;               // Where to sell
  chain: string;                 // Blockchain
  spread: number;                // Price spread percentage
  estimatedProfit: number;       // Expected profit in USD
  confidence: number;            // Confidence score (0-1)
  timestamp: Date;               // Detection time
}
```

## 🛠️ MCP Tools

### Core Memory Operations

#### `store_penny_trade`
**Purpose**: Store the result of an arbitrage attempt
**Input**: Trade details including prices, DEXs, profit/loss
**Output**: Confirmation with trade classification (green/red)

```json
{
  "tokenA": "ETH",
  "tokenB": "USDC", 
  "dexA": "Uniswap",
  "dexB": "SushiSwap",
  "chain": "ethereum",
  "priceA": 2500.50,
  "priceB": 2501.25,
  "profitUSD": 0.75,
  "gasSpentUSD": 0.50,
  "wasExecuted": true
}
```

#### `get_green_trades`
**Purpose**: Retrieve all profitable trades
**Input**: Optional limit parameter
**Output**: List of successful trades sorted by profit

#### `get_performance_stats`
**Purpose**: Get overall trading performance metrics
**Output**: Success rate, total profit, average profit, trade counts

### Analytics Tools

#### `find_best_pairs`
**Purpose**: Identify the most profitable token pairs
**Input**: Optional chain filter, minimum trade count
**Output**: Ranked list of profitable pairs

#### `analyze_gas_efficiency`
**Purpose**: Analyze gas costs vs profits by chain
**Input**: Chain to analyze
**Output**: Gas efficiency metrics and recommendations

## 📈 Performance Tracking

### Key Metrics
- **Success Rate**: Percentage of profitable trades
- **Average Profit**: Mean profit per trade
- **Total Profit**: Cumulative earnings
- **Gas Efficiency**: Profit-to-gas ratio
- **Best/Worst Trades**: Extreme performance examples

### Real-time Analytics
```sql
-- Example queries DexMind performs
SELECT 
  COUNT(*) as total_trades,
  SUM(CASE WHEN was_green = 1 THEN 1 ELSE 0 END) as green_trades,
  AVG(net_profit_usd) as avg_profit,
  SUM(net_profit_usd) as total_profit
FROM penny_trades 
WHERE timestamp > datetime('now', '-24 hours');
```

## 🎯 Learning Capabilities

### Pattern Recognition
DexMind automatically identifies:
- **Time-based patterns**: When arbitrage is most profitable
- **Chain preferences**: Which chains offer best opportunities
- **DEX relationships**: Which DEX pairs have consistent spreads
- **Gas optimization**: Optimal gas prices for profitability

### Strategy Evolution
As data accumulates, DexMind helps evolve strategies:
1. **Phase 1**: Track all micro-arbitrage (current)
2. **Phase 2**: Identify profitable patterns
3. **Phase 3**: Optimize for higher-value opportunities
4. **Phase 4**: Advanced MEV strategies

## 🔧 Configuration

### Database Setup
```bash
# DexMind automatically creates SQLite database
# Default location: ./dexmind.db
# Tables created on first run
```

### MCP Server Configuration
```json
{
  "name": "dexmind",
  "command": "node",
  "args": ["/path/to/MayArbi/dexmind/dist/index.js"]
}
```

### Environment Variables
```bash
# Optional configuration
DEXMIND_DB_PATH=./custom_path/dexmind.db
DEXMIND_LOG_LEVEL=info
```

## 🚀 Usage Examples

### Storing a Trade Result
```
"Store a penny trade: ETH/USDC on Uniswap vs SushiSwap, Ethereum chain, 
prices 2500.50 and 2501.25, profit $0.75, gas $0.50, executed successfully"
```

### Analyzing Performance
```
"Show me my green trades from the last week"
"What's my overall performance statistics?"
"Which token pairs are most profitable?"
```

### Gas Optimization
```
"Analyze gas efficiency on Ethereum"
"What's the optimal gas price for profitable trades?"
```

## 🔮 Future Enhancements

### Advanced Analytics
- **Machine Learning**: Pattern prediction models
- **Market Correlation**: Cross-chain opportunity detection
- **Risk Scoring**: Automated risk assessment
- **Backtesting**: Historical strategy validation

### Integration Expansions
- **Price Feeds**: Real-time market data integration
- **Execution Engine**: Direct trading integration
- **Alert System**: Opportunity notifications
- **Dashboard**: Visual performance monitoring

## 🛡️ Security & Reliability

### Data Protection
- **Local Storage**: No sensitive data leaves your system
- **Backup Strategy**: Regular database backups
- **Error Handling**: Graceful failure recovery
- **Validation**: Input sanitization and validation

### Performance Optimization
- **Indexing**: Optimized database queries
- **Caching**: Frequently accessed data caching
- **Cleanup**: Automatic old data archival
- **Monitoring**: Performance metrics tracking

## 📚 Integration with MayArbi Ecosystem

### Synergy with Other Components
- **Serena**: Code analysis and optimization
- **Filesystem MCP**: Data export and backup
- **MCP Compass**: Discovery of new trading tools
- **Augment Code**: AI-assisted development and analysis

### Data Flow
```
Market Data → Opportunity Detection → DexMind Storage → 
Pattern Analysis → Strategy Optimization → Execution → 
Result Tracking → DexMind Learning
```

**DexMind is the memory that makes MayArbi smarter with every trade!** 🧠✨
