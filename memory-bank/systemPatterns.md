# System Patterns

## System Architecture

### High-Level Architecture
MayArbi follows a modular, event-driven architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Price Feeds   │    │ Bridge Monitor  │    │ Wallet Manager  │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────┐
                    │   Arbitrage Engine      │
                    │                         │
                    └─────────────┬───────────┘
                                  │
                    ┌─────────────▼───────────┐
                    │   Cross-Chain MEV       │
                    │                         │
                    └─────────────┬───────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│ Memory System   │    │ Health Monitor  │    │ Error Manager   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Design Patterns

#### 1. Event-Driven Architecture
- **Pattern**: Components communicate through events rather than direct calls
- **Implementation**: Data Flow Coordinator manages all inter-component communication
- **Benefits**: Loose coupling, easier testing, better fault isolation
- **Example**: Price updates trigger arbitrage analysis, which may trigger trade execution

#### 2. Circuit Breaker Pattern
- **Pattern**: Prevent cascading failures through automatic circuit breakers
- **Implementation**: Error Propagation & Recovery system monitors component health
- **Benefits**: System stability, graceful degradation, automatic recovery
- **Example**: If bridge monitor fails 5 times, circuit opens and cross-chain trades pause

#### 3. Memory-First Design
- **Pattern**: Every operation and decision is recorded for learning
- **Implementation**: MCP Memory Server stores all trading data and patterns
- **Benefits**: Continuous improvement, audit trail, pattern recognition
- **Example**: Failed trades are analyzed to improve future opportunity selection

#### 4. Layered Security
- **Pattern**: Multiple layers of validation and risk management
- **Implementation**: Wallet security, trade validation, circuit breakers, position limits
- **Benefits**: Capital protection, regulatory compliance, operational safety
- **Example**: Trade must pass profitability, slippage, and risk checks before execution

## Key Technical Decisions

### Technology Stack
- **Language**: Python 3.11+ for main application logic
- **Async Framework**: asyncio for concurrent operations
- **Blockchain Interaction**: web3.py for Ethereum-compatible chains
- **Memory System**: MCP Memory Server with ChromaDB for vector storage
- **Data Storage**: JSON for configuration, SQLite for operational data
- **API Integration**: aiohttp for async HTTP requests
- **Testing**: pytest with async support

### Component Relationships

#### Data Flow Hierarchy
1. **Price Feeds** → Collect market data from multiple DEXs
2. **Bridge Monitor** → Track cross-chain transfer costs
3. **Arbitrage Engine** → Analyze opportunities and calculate profitability
4. **Cross-Chain MEV** → Enhance opportunities with bridge arbitrage
5. **Wallet Manager** → Execute trades and manage balances
6. **Memory System** → Record all operations for learning

#### Error Propagation Chain
1. **Component Failure** → Detected by health monitoring
2. **Error Classification** → Severity and category assignment
3. **Impact Assessment** → Determine affected downstream components
4. **Recovery Strategy** → Automatic or manual intervention
5. **Learning Integration** → Pattern recognition for future prevention

#### Resource Management Flow
1. **Resource Allocation** → CPU, memory, network bandwidth distribution
2. **Performance Monitoring** → Real-time resource utilization tracking
3. **Bottleneck Detection** → Identify and resolve performance constraints
4. **Scaling Decisions** → Automatic resource adjustment based on load

### Critical Implementation Paths

#### Trade Execution Path
```python
# Critical path for trade execution
1. Opportunity Detection (Price Feeds)
   ├── Price differential calculation
   ├── Gas cost estimation
   └── Profitability validation

2. Risk Assessment (Arbitrage Engine)
   ├── Slippage analysis
   ├── Liquidity validation
   └── Circuit breaker check

3. Trade Preparation (Wallet Manager)
   ├── Balance verification
   ├── Nonce management
   └── Transaction construction

4. Execution (Wallet Manager)
   ├── Transaction submission
   ├── Confirmation monitoring
   └── Result validation

5. Recording (Memory System)
   ├── Trade outcome storage
   ├── Pattern analysis
   └── Performance metrics update
```

#### Error Recovery Path
```python
# Critical path for error recovery
1. Error Detection (Health Monitor)
   ├── Component health checks
   ├── Performance monitoring
   └── Anomaly detection

2. Error Classification (Error Manager)
   ├── Severity assessment
   ├── Category assignment
   └── Impact analysis

3. Recovery Strategy (Error Manager)
   ├── Automatic retry logic
   ├── Fallback mechanisms
   └── Circuit breaker activation

4. System Restoration (Health Monitor)
   ├── Component restart
   ├── State synchronization
   └── Normal operation resumption
```

### Design Principles

#### 1. Fail-Safe Defaults
- **Principle**: System defaults to safe states when uncertain
- **Implementation**: Conservative risk parameters, automatic trade halting on errors
- **Example**: Unknown market conditions → pause trading until analysis complete

#### 2. Gradual Degradation
- **Principle**: System continues operating with reduced functionality rather than complete failure
- **Implementation**: Component isolation, fallback mechanisms, partial operation modes
- **Example**: Bridge monitor failure → continue same-chain arbitrage only

#### 3. Observable Operations
- **Principle**: Every system operation is visible and auditable
- **Implementation**: Comprehensive logging, real-time dashboards, historical analysis
- **Example**: Every trade decision includes full reasoning chain and market context

#### 4. Adaptive Learning
- **Principle**: System improves performance through experience
- **Implementation**: Pattern recognition, parameter optimization, strategy evolution
- **Example**: Gas price prediction improves based on historical transaction outcomes

### Integration Patterns

#### MCP Integration Pattern
- **Memory Server**: Stores trading patterns, market insights, performance data
- **Knowledge Graph**: Maps relationships between tokens, DEXs, and market conditions
- **File Scope**: Manages configuration and operational data organization

#### API Integration Pattern
- **Rate Limiting**: Respect API limits while maintaining data freshness
- **Fallback Chains**: Multiple data sources for redundancy
- **Caching Strategy**: Balance data freshness with API efficiency

#### Blockchain Integration Pattern
- **Multi-Chain Support**: Unified interface for different blockchain networks
- **Gas Optimization**: Dynamic gas pricing based on network conditions
- **Transaction Management**: Nonce handling, retry logic, confirmation tracking

These system patterns ensure MayArbi operates reliably, learns continuously, and scales effectively while maintaining capital safety and operational transparency.