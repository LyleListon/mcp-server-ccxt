// DexMind Types - Penny Hunter Edition
// Starting small, thinking big! 🎯

export interface PennyTrade {
  id: string;
  tokenA: string;
  tokenB: string;
  dexA: string;
  dexB: string;
  chain: 'ethereum' | 'arbitrum' | 'base' | 'vitruveo';
  
  // Price data
  priceA: number;
  priceB: number;
  priceSpreadPercent: number;
  
  // Profit tracking (even pennies!)
  profitUSD: number;
  gasSpentUSD: number;
  netProfitUSD: number;
  
  // Success metrics
  wasGreen: boolean; // The holy grail!
  wasExecuted: boolean;
  
  // Timing
  timestamp: Date;
  blockNumber?: number;
}

export interface GasTracker {
  chain: string;
  averageGasPrice: number;
  timestamp: Date;
  transactionCost: number;
}

export interface DexPair {
  dex: string;
  chain: string;
  tokenA: string;
  tokenB: string;
  poolAddress: string;
  liquidity: number;
  lastUpdated: Date;
}

export interface ArbitrageOpportunity {
  id: string;
  tokenPair: string;
  buyDex: string;
  sellDex: string;
  chain: string;
  spread: number;
  estimatedProfit: number;
  confidence: number; // 0-1 scale
  timestamp: Date;
}

export interface MemoryQuery {
  timeframe?: {
    start: Date;
    end: Date;
  };
  chain?: string;
  tokenPair?: string;
  minProfit?: number;
  onlyGreen?: boolean;
}

export interface PerformanceStats {
  totalTrades: number;
  greenTrades: number;
  redTrades: number;
  totalProfitUSD: number;
  averageProfitUSD: number;
  successRate: number;
  bestTrade: PennyTrade | null;
  worstTrade: PennyTrade | null;
}
