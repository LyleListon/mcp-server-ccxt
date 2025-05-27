import { PennyTrade, GasTracker, PerformanceStats } from './types';
export declare class DexMindMemory {
    private db;
    constructor(dbPath?: string);
    private initializeTables;
    storePennyTrade(trade: PennyTrade): Promise<void>;
    getGreenTrades(limit?: number): Promise<PennyTrade[]>;
    getPerformanceStats(): Promise<PerformanceStats>;
    storeGasData(gasData: GasTracker): Promise<void>;
    private rowToPennyTrade;
    close(): void;
}
//# sourceMappingURL=memory.d.ts.map