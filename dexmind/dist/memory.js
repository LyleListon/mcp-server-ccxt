// DexMind Memory Engine - SQLite Backend
// Every penny counts! 💰
import sqlite3 from 'sqlite3';
export class DexMindMemory {
    db;
    constructor(dbPath = './dexmind.db') {
        this.db = new sqlite3.Database(dbPath);
        this.initializeTables();
    }
    initializeTables() {
        // Penny trades table - the heart of DexMind
        this.db.run(`
      CREATE TABLE IF NOT EXISTS penny_trades (
        id TEXT PRIMARY KEY,
        token_a TEXT NOT NULL,
        token_b TEXT NOT NULL,
        dex_a TEXT NOT NULL,
        dex_b TEXT NOT NULL,
        chain TEXT NOT NULL,
        price_a REAL NOT NULL,
        price_b REAL NOT NULL,
        price_spread_percent REAL NOT NULL,
        profit_usd REAL NOT NULL,
        gas_spent_usd REAL NOT NULL,
        net_profit_usd REAL NOT NULL,
        was_green BOOLEAN NOT NULL,
        was_executed BOOLEAN NOT NULL,
        timestamp DATETIME NOT NULL,
        block_number INTEGER
      )
    `);
        // Gas tracking table
        this.db.run(`
      CREATE TABLE IF NOT EXISTS gas_tracker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chain TEXT NOT NULL,
        average_gas_price REAL NOT NULL,
        transaction_cost REAL NOT NULL,
        timestamp DATETIME NOT NULL
      )
    `);
        // Arbitrage opportunities table
        this.db.run(`
      CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
        id TEXT PRIMARY KEY,
        token_pair TEXT NOT NULL,
        buy_dex TEXT NOT NULL,
        sell_dex TEXT NOT NULL,
        chain TEXT NOT NULL,
        spread REAL NOT NULL,
        estimated_profit REAL NOT NULL,
        confidence REAL NOT NULL,
        timestamp DATETIME NOT NULL
      )
    `);
        console.log('🧠 DexMind memory tables initialized!');
    }
    // Store a penny trade (even $0.01 is worth remembering!)
    async storePennyTrade(trade) {
        return new Promise((resolve, reject) => {
            const stmt = this.db.prepare(`
        INSERT INTO penny_trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);
            stmt.run([
                trade.id,
                trade.tokenA,
                trade.tokenB,
                trade.dexA,
                trade.dexB,
                trade.chain,
                trade.priceA,
                trade.priceB,
                trade.priceSpreadPercent,
                trade.profitUSD,
                trade.gasSpentUSD,
                trade.netProfitUSD,
                trade.wasGreen ? 1 : 0,
                trade.wasExecuted ? 1 : 0,
                trade.timestamp.toISOString(),
                trade.blockNumber
            ], function (err) {
                if (err)
                    reject(err);
                else {
                    console.log(`💰 Stored ${trade.wasGreen ? 'GREEN' : 'RED'} trade: $${trade.netProfitUSD.toFixed(4)}`);
                    resolve();
                }
            });
            stmt.finalize();
        });
    }
    // Find all green trades (our success stories!)
    async getGreenTrades(limit = 100) {
        return new Promise((resolve, reject) => {
            this.db.all(`
        SELECT * FROM penny_trades
        WHERE was_green = 1
        ORDER BY net_profit_usd DESC
        LIMIT ?
      `, [limit], (err, rows) => {
                if (err)
                    reject(err);
                else
                    resolve(rows.map(this.rowToPennyTrade));
            });
        });
    }
    // Get performance stats
    async getPerformanceStats() {
        return new Promise((resolve, reject) => {
            this.db.get(`
        SELECT
          COUNT(*) as total_trades,
          SUM(CASE WHEN was_green = 1 THEN 1 ELSE 0 END) as green_trades,
          SUM(CASE WHEN was_green = 0 THEN 1 ELSE 0 END) as red_trades,
          SUM(net_profit_usd) as total_profit,
          AVG(net_profit_usd) as avg_profit,
          MAX(net_profit_usd) as best_profit,
          MIN(net_profit_usd) as worst_profit
        FROM penny_trades
      `, (err, row) => {
                if (err)
                    reject(err);
                else {
                    const stats = {
                        totalTrades: row.total_trades || 0,
                        greenTrades: row.green_trades || 0,
                        redTrades: row.red_trades || 0,
                        totalProfitUSD: row.total_profit || 0,
                        averageProfitUSD: row.avg_profit || 0,
                        successRate: row.total_trades > 0 ? (row.green_trades / row.total_trades) : 0,
                        bestTrade: null, // TODO: Implement
                        worstTrade: null // TODO: Implement
                    };
                    resolve(stats);
                }
            });
        });
    }
    // Store gas data for optimization
    async storeGasData(gasData) {
        return new Promise((resolve, reject) => {
            const stmt = this.db.prepare(`
        INSERT INTO gas_tracker (chain, average_gas_price, transaction_cost, timestamp)
        VALUES (?, ?, ?, ?)
      `);
            stmt.run([
                gasData.chain,
                gasData.averageGasPrice,
                gasData.transactionCost,
                gasData.timestamp.toISOString()
            ], function (err) {
                if (err)
                    reject(err);
                else
                    resolve();
            });
            stmt.finalize();
        });
    }
    rowToPennyTrade(row) {
        return {
            id: row.id,
            tokenA: row.token_a,
            tokenB: row.token_b,
            dexA: row.dex_a,
            dexB: row.dex_b,
            chain: row.chain,
            priceA: row.price_a,
            priceB: row.price_b,
            priceSpreadPercent: row.price_spread_percent,
            profitUSD: row.profit_usd,
            gasSpentUSD: row.gas_spent_usd,
            netProfitUSD: row.net_profit_usd,
            wasGreen: row.was_green === 1,
            wasExecuted: row.was_executed === 1,
            timestamp: new Date(row.timestamp),
            blockNumber: row.block_number
        };
    }
    close() {
        this.db.close();
    }
}
//# sourceMappingURL=memory.js.map