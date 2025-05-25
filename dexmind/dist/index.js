#!/usr/bin/env node
// DexMind MCP Server - Penny Hunter Edition
// Every green trade matters! 🎯💰
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema, } from '@modelcontextprotocol/sdk/types.js';
import { DexMindMemory } from './memory';
class DexMindServer {
    server;
    memory;
    constructor() {
        this.server = new Server({
            name: 'dexmind',
            version: '1.0.0',
        }, {
            capabilities: {
                tools: {},
            },
        });
        this.memory = new DexMindMemory();
        this.setupToolHandlers();
    }
    setupToolHandlers() {
        // List available tools
        this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
            tools: [
                {
                    name: 'store_penny_trade',
                    description: 'Store a penny trade result (even $0.01 profits count!)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            tokenA: { type: 'string', description: 'First token symbol' },
                            tokenB: { type: 'string', description: 'Second token symbol' },
                            dexA: { type: 'string', description: 'Source DEX' },
                            dexB: { type: 'string', description: 'Target DEX' },
                            chain: { type: 'string', enum: ['ethereum', 'arbitrum', 'base', 'vitruveo'] },
                            priceA: { type: 'number', description: 'Price on DEX A' },
                            priceB: { type: 'number', description: 'Price on DEX B' },
                            profitUSD: { type: 'number', description: 'Gross profit in USD' },
                            gasSpentUSD: { type: 'number', description: 'Gas cost in USD' },
                            wasExecuted: { type: 'boolean', description: 'Was the trade executed?' }
                        },
                        required: ['tokenA', 'tokenB', 'dexA', 'dexB', 'chain', 'priceA', 'priceB', 'profitUSD', 'gasSpentUSD', 'wasExecuted']
                    }
                },
                {
                    name: 'get_green_trades',
                    description: 'Get all profitable trades (our success stories!)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            limit: { type: 'number', description: 'Max number of trades to return', default: 50 }
                        }
                    }
                },
                {
                    name: 'get_performance_stats',
                    description: 'Get overall performance statistics',
                    inputSchema: {
                        type: 'object',
                        properties: {}
                    }
                },
                {
                    name: 'find_best_pairs',
                    description: 'Find the most profitable token pairs',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            chain: { type: 'string', description: 'Filter by chain (optional)' },
                            minTrades: { type: 'number', description: 'Minimum number of trades', default: 5 }
                        }
                    }
                },
                {
                    name: 'analyze_gas_efficiency',
                    description: 'Analyze gas costs vs profits',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            chain: { type: 'string', description: 'Chain to analyze' }
                        }
                    }
                }
            ]
        }));
        // Handle tool calls
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const { name, arguments: args } = request.params;
            try {
                switch (name) {
                    case 'store_penny_trade':
                        return await this.storePennyTrade(args);
                    case 'get_green_trades':
                        return await this.getGreenTrades(args);
                    case 'get_performance_stats':
                        return await this.getPerformanceStats();
                    case 'find_best_pairs':
                        return await this.findBestPairs(args);
                    case 'analyze_gas_efficiency':
                        return await this.analyzeGasEfficiency(args);
                    default:
                        throw new Error(`Unknown tool: ${name}`);
                }
            }
            catch (error) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Error: ${error instanceof Error ? error.message : String(error)}`
                        }
                    ]
                };
            }
        });
    }
    async storePennyTrade(args) {
        const trade = {
            id: `trade_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            tokenA: args.tokenA,
            tokenB: args.tokenB,
            dexA: args.dexA,
            dexB: args.dexB,
            chain: args.chain,
            priceA: args.priceA,
            priceB: args.priceB,
            priceSpreadPercent: ((args.priceB - args.priceA) / args.priceA) * 100,
            profitUSD: args.profitUSD,
            gasSpentUSD: args.gasSpentUSD,
            netProfitUSD: args.profitUSD - args.gasSpentUSD,
            wasGreen: (args.profitUSD - args.gasSpentUSD) > 0,
            wasExecuted: args.wasExecuted,
            timestamp: new Date()
        };
        await this.memory.storePennyTrade(trade);
        const emoji = trade.wasGreen ? '🟢' : '🔴';
        const status = trade.wasGreen ? 'PROFIT' : 'LOSS';
        return {
            content: [
                {
                    type: 'text',
                    text: `${emoji} Trade stored! ${status}: $${trade.netProfitUSD.toFixed(4)}\n` +
                        `Pair: ${trade.tokenA}/${trade.tokenB}\n` +
                        `DEXs: ${trade.dexA} → ${trade.dexB}\n` +
                        `Chain: ${trade.chain}\n` +
                        `Spread: ${trade.priceSpreadPercent.toFixed(2)}%`
                }
            ]
        };
    }
    async getGreenTrades(args) {
        const limit = args.limit || 50;
        const trades = await this.memory.getGreenTrades(limit);
        if (trades.length === 0) {
            return {
                content: [
                    {
                        type: 'text',
                        text: '📊 No green trades found yet. Keep hunting for those pennies! 🎯'
                    }
                ]
            };
        }
        const tradeList = trades.map(trade => `🟢 $${trade.netProfitUSD.toFixed(4)} | ${trade.tokenA}/${trade.tokenB} | ${trade.dexA}→${trade.dexB} | ${trade.chain}`).join('\n');
        return {
            content: [
                {
                    type: 'text',
                    text: `💰 Green Trades (${trades.length} found):\n\n${tradeList}`
                }
            ]
        };
    }
    async getPerformanceStats() {
        const stats = await this.memory.getPerformanceStats();
        return {
            content: [
                {
                    type: 'text',
                    text: `📊 DexMind Performance Stats:\n\n` +
                        `Total Trades: ${stats.totalTrades}\n` +
                        `🟢 Green Trades: ${stats.greenTrades}\n` +
                        `🔴 Red Trades: ${stats.redTrades}\n` +
                        `Success Rate: ${(stats.successRate * 100).toFixed(1)}%\n` +
                        `Total Profit: $${stats.totalProfitUSD.toFixed(4)}\n` +
                        `Average Profit: $${stats.averageProfitUSD.toFixed(4)}\n\n` +
                        `${stats.totalProfitUSD > 0 ? '🎉 In the green overall!' : '📈 Keep hunting for profits!'}`
                }
            ]
        };
    }
    async findBestPairs(args) {
        // TODO: Implement best pairs analysis
        return {
            content: [
                {
                    type: 'text',
                    text: '🔍 Best pairs analysis coming soon! For now, check your green trades to see patterns.'
                }
            ]
        };
    }
    async analyzeGasEfficiency(args) {
        // TODO: Implement gas efficiency analysis
        return {
            content: [
                {
                    type: 'text',
                    text: '⛽ Gas efficiency analysis coming soon! Track your gas costs in each trade.'
                }
            ]
        };
    }
    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('🧠 DexMind MCP Server running - Ready to hunt pennies! 🎯');
    }
}
// Start the server
const server = new DexMindServer();
server.run().catch(console.error);
//# sourceMappingURL=index.js.map