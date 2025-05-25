export interface PennyTrade {
    id: string;
    tokenA: string;
    tokenB: string;
    dexA: string;
    dexB: string;
    chain: 'ethereum' | 'arbitrum' | 'base' | 'vitruveo';
    priceA: number;
    priceB: number;
    priceSpreadPercent: number;
    profitUSD: number;
    gasSpentUSD: number;
    netProfitUSD: number;
    wasGreen: boolean;
    wasExecuted: boolean;
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
    confidence: number;
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
//# sourceMappingURL=types.d.ts.map