# 🚀 Enhanced Arbitrage Bot - Quick Start Guide

## Running the Bot

### **Basic Startup**
```bash
cd src
python enhanced_arbitrage_bot.py
```

### **What You'll See**
```
🚀 Starting Enhanced Arbitrage Bot...
✅ MCP servers connected successfully
🎯 Starting arbitrage detection loop...
🔍 Found 2 potential opportunities
💎 Viable opportunity: ['BTC', 'USDT'] profit=$41.00 risk=24.8 score=1.39
🎯 Executing opportunity...
📊 Simulated execution: SUCCESS
```

## Configuration Options

### **Trading Settings** (in `enhanced_arbitrage_bot.py`)
```python
config = {
    'trading': {
        'min_profit_threshold': 0.5,    # Minimum 0.5% profit
        'max_risk_score': 60,           # Maximum risk tolerance
        'trading_enabled': False,       # True for real trading
        'scan_interval': 5              # Scan every 5 seconds
    }
}
```

### **Risk Management**
```python
'max_slippage': 1.0,        # 1% maximum slippage
'min_liquidity': 10000,     # $10k minimum liquidity
'gas_price_gwei': 20,       # 20 gwei gas price
'eth_price_usd': 3000       # ETH price for gas calculations
```

## Key Features

### **🔍 Opportunity Detection**
- Scans multiple DEXs every 5 seconds
- Identifies price discrepancies
- Calculates profit potential
- Assesses execution risk

### **🧠 MCP Intelligence**
- Learns from historical patterns
- Provides confidence scoring
- Aggregates multi-source market data
- Stores execution results for improvement

### **⚡ Real-time Analysis**
- Profit calculation with gas costs
- Multi-factor risk assessment
- Enhanced scoring algorithm
- Intelligent filtering

### **📊 Performance Tracking**
- Success/failure rates
- Total profit tracking
- Execution statistics
- Pattern learning metrics

## Testing Components

### **Individual Component Tests**
```bash
python test_simple_components.py
```

### **Full Integration Test**
```bash
python test_basic_setup.py
```

## MCP Server Status

### **Connected Servers**
- ✅ **DexMind**: Custom memory for arbitrage patterns
- ✅ **Memory Service**: General pattern storage
- ✅ **Knowledge Graph**: Token relationships
- ✅ **Coincap**: Real-time price data
- ✅ **Coinmarket**: Market cap data
- ✅ **CCXT**: Exchange data
- ✅ **FileScopeMCP**: Project organization

### **Check MCP Status**
```bash
./test-all-mcp-servers.sh
```

## Switching to Real Trading

### **1. Enable Real Trading**
```python
'trading_enabled': True
```

### **2. Add Real DEX Connections**
- Configure Uniswap V3 API
- Set up SushiSwap integration
- Add wallet connection

### **3. Security Setup**
- Configure private keys securely
- Set up MEV protection
- Enable transaction signing

### **4. Risk Management**
- Start with small amounts
- Monitor closely
- Adjust thresholds based on performance

## Monitoring and Logs

### **Log Levels**
- `INFO`: General operation status
- `DEBUG`: Detailed analysis information
- `WARNING`: Risk alerts and issues
- `ERROR`: Execution failures

### **Key Metrics to Watch**
- Opportunities found per minute
- Success rate percentage
- Average profit per trade
- Risk score distribution

## Troubleshooting

### **Common Issues**

**MCP Connection Failed**
```bash
# Check MCP server status
./test-all-mcp-servers.sh

# Restart specific servers if needed
```

**No Opportunities Found**
- Check market volatility
- Adjust profit thresholds
- Verify DEX data feeds

**High Risk Scores**
- Review liquidity requirements
- Adjust slippage tolerance
- Check gas price settings

**Execution Failures**
- Monitor gas prices
- Check wallet balance
- Verify network connectivity

## Advanced Configuration

### **Custom DEX List**
```python
'dexs': ['uniswap_v3', 'sushiswap', 'curve', 'balancer']
```

### **Enhanced Scoring Weights**
```python
def _calculate_enhanced_score(self, profit, risk, intelligence):
    base_profit = profit.get('net_profit_percentage', 0)
    risk_factor = (100 - risk.get('risk_score', 50)) / 100
    confidence_factor = intelligence.get('confidence_score', 0.5)
    
    # Customize this formula
    enhanced_score = base_profit * risk_factor * (1 + confidence_factor)
    return enhanced_score
```

### **Pattern Learning Tuning**
```python
# Adjust confidence calculation
if similar_opps:
    successful = sum(1 for opp in similar_opps if opp.get('success', False))
    confidence = successful / len(similar_opps)
    
    # Add time decay for older patterns
    # Add volume weighting
    # Add market condition matching
```

## Performance Optimization

### **Scan Frequency**
- High frequency (1-2 seconds): More opportunities, higher CPU
- Medium frequency (5-10 seconds): Balanced performance
- Low frequency (30+ seconds): Conservative, lower resource usage

### **Filtering Efficiency**
- Set appropriate profit thresholds
- Use risk score limits
- Filter by liquidity requirements
- Consider gas cost ratios

### **Memory Management**
- Limit historical pattern storage
- Clean up old execution data
- Monitor MCP server memory usage

## Next Steps

1. **Test thoroughly** in simulation mode
2. **Adjust parameters** based on market conditions
3. **Add real DEX integrations** when ready
4. **Monitor performance** and optimize
5. **Scale up** gradually with proven strategies

**Remember: Start small, test extensively, and scale gradually! 🎯**
