#!/usr/bin/env python3
"""
Memory-Enhanced Arbitrage Bot
Integrates MCP Memory Service with arbitrage trading for intelligent decision making
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add memory service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp-memory-service', 'src'))

try:
    from mcp_memory_service.server import MemoryServer
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    print("Warning: Memory service not available. Running without memory features.")

try:
    from enhanced_arbitrage_bot import EnhancedArbitrageBot
    from models import ArbitrageOpportunity
    BOT_AVAILABLE = True
except ImportError:
    BOT_AVAILABLE = False
    print("Warning: Enhanced arbitrage bot not available. Running memory tests only.")

    # Create mock classes for testing
    class EnhancedArbitrageBot:
        def __init__(self, config_path=None):
            pass
        async def execute_arbitrage(self, opportunity):
            return {"success": True, "profit": 10.5, "gas_cost": 2.1}

    class ArbitrageOpportunity:
        def __init__(self):
            self.token_symbol = "ETH"
            self.dex_a = "uniswap"
            self.dex_b = "sushiswap"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TradingMemory:
    """Structure for trading-related memories"""
    content: str
    tags: List[str]
    memory_type: str
    metadata: Dict[str, Any]

class MemoryEnhancedArbitrageBot(EnhancedArbitrageBot):
    """
    Enhanced Arbitrage Bot with Memory System Integration
    
    Features:
    - Remembers successful trading strategies
    - Learns from failed opportunities
    - Tracks market patterns over time
    - Stores bridge cost optimizations
    - Maintains DEX performance metrics
    """
    
    def __init__(self, config_path: str = "config/capital_efficient_config.json"):
        # Load config from JSON file
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Pass config dictionary to parent class
        super().__init__(config)
        self.memory_server = None
        self.memory_enabled = MEMORY_AVAILABLE

        if self.memory_enabled:
            asyncio.create_task(self._initialize_memory())
    
    async def _initialize_memory(self):
        """Initialize the memory server"""
        try:
            self.memory_server = MemoryServer()
            await self.memory_server.initialize()
            logger.info("Memory system initialized successfully")
            
            # Store initialization memory
            await self._store_memory(
                "Memory-Enhanced Arbitrage Bot initialized",
                ["initialization", "arbitrage-bot", "memory-system"],
                "system_event",
                {"timestamp": datetime.now().isoformat(), "version": "1.0"}
            )
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            self.memory_enabled = False
    
    async def _store_memory(self, content: str, tags: List[str], memory_type: str, metadata: Dict[str, Any] = None):
        """Store a memory in the system"""
        if not self.memory_enabled or not self.memory_server:
            return
        
        try:
            memory_data = {
                "content": content,
                "metadata": {
                    "tags": ",".join(tags),
                    "type": memory_type,
                    **(metadata or {})
                }
            }
            await self.memory_server.handle_store_memory(memory_data)
            logger.debug(f"Stored memory: {content[:50]}...")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
    
    async def _recall_memories(self, query: str, n_results: int = 5) -> List[str]:
        """Recall memories based on query"""
        if not self.memory_enabled or not self.memory_server:
            return []
        
        try:
            response = await self.memory_server.handle_retrieve_memory({
                "query": query,
                "n_results": n_results
            })
            # Parse the response to extract memory contents
            memories = []
            if response and response[0].text:
                # Simple parsing - in production, you'd want more robust parsing
                text = response[0].text
                if "Found the following memories:" in text:
                    # Extract memory contents from the formatted response
                    lines = text.split('\n')
                    for line in lines:
                        if line.strip().startswith('Content:'):
                            content = line.replace('Content:', '').strip()
                            memories.append(content)
            return memories
        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []
    
    async def analyze_opportunity_with_memory(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Analyze arbitrage opportunity using historical memory"""
        analysis = {
            "opportunity": opportunity,
            "memory_insights": [],
            "confidence_score": 0.5,
            "recommended_action": "analyze"
        }
        
        if not self.memory_enabled:
            return analysis
        
        # Recall similar opportunities
        query = f"arbitrage {opportunity.token_symbol} {opportunity.dex_a} {opportunity.dex_b}"
        similar_memories = await self._recall_memories(query, 3)
        
        # Recall bridge cost memories for cross-chain opportunities
        if hasattr(opportunity, 'chain_a') and hasattr(opportunity, 'chain_b'):
            bridge_query = f"bridge cost {opportunity.chain_a} {opportunity.chain_b}"
            bridge_memories = await self._recall_memories(bridge_query, 2)
            similar_memories.extend(bridge_memories)
        
        analysis["memory_insights"] = similar_memories
        
        # Adjust confidence based on historical success
        if any("successful" in memory.lower() for memory in similar_memories):
            analysis["confidence_score"] += 0.2
        if any("failed" in memory.lower() for memory in similar_memories):
            analysis["confidence_score"] -= 0.1
        
        # Recommend action based on analysis
        if analysis["confidence_score"] > 0.7:
            analysis["recommended_action"] = "execute"
        elif analysis["confidence_score"] < 0.3:
            analysis["recommended_action"] = "skip"
        
        return analysis
    
    async def execute_trade_with_memory(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Execute trade and store the result in memory"""
        # Get memory-enhanced analysis first
        analysis = await self.analyze_opportunity_with_memory(opportunity)
        
        # Execute the trade (using parent class method)
        result = await super().execute_arbitrage(opportunity)
        
        # Store the trading result in memory
        success = result.get("success", False)
        profit = result.get("profit", 0)
        
        memory_content = f"Arbitrage trade {opportunity.token_symbol} on {opportunity.dex_a}/{opportunity.dex_b}: "
        memory_content += f"{'SUCCESS' if success else 'FAILED'}, "
        memory_content += f"Profit: ${profit:.2f}, "
        memory_content += f"Confidence: {analysis['confidence_score']:.2f}"
        
        tags = [
            "arbitrage-trade",
            opportunity.token_symbol.lower(),
            opportunity.dex_a.lower(),
            opportunity.dex_b.lower(),
            "success" if success else "failed"
        ]
        
        metadata = {
            "profit": profit,
            "confidence_score": analysis["confidence_score"],
            "gas_cost": result.get("gas_cost", 0),
            "execution_time": result.get("execution_time", 0)
        }
        
        await self._store_memory(memory_content, tags, "trade_execution", metadata)
        
        return {**result, "memory_analysis": analysis}
    
    async def store_market_insight(self, insight: str, tags: List[str], metadata: Dict[str, Any] = None):
        """Store a market insight or pattern observation"""
        await self._store_memory(
            f"MARKET INSIGHT: {insight}",
            ["market-insight"] + tags,
            "market_analysis",
            metadata
        )
    
    async def get_trading_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of trading performance from memory"""
        if not self.memory_enabled:
            return {"error": "Memory system not available"}
        
        # Recall recent trading memories
        recent_trades = await self._recall_memories("arbitrage trade", 20)
        
        # Recall successful strategies
        successful_strategies = await self._recall_memories("SUCCESS profit", 10)
        
        # Recall market insights
        market_insights = await self._recall_memories("MARKET INSIGHT", 5)
        
        return {
            "recent_trades_count": len(recent_trades),
            "recent_trades": recent_trades[:5],  # Show last 5
            "successful_strategies": successful_strategies,
            "market_insights": market_insights,
            "memory_system_status": "active" if self.memory_enabled else "inactive"
        }
    
    async def learn_from_failed_opportunity(self, opportunity: ArbitrageOpportunity, reason: str):
        """Learn from failed opportunities"""
        memory_content = f"FAILED OPPORTUNITY: {opportunity.token_symbol} on {opportunity.dex_a}/{opportunity.dex_b} - {reason}"
        
        tags = [
            "failed-opportunity",
            "learning",
            opportunity.token_symbol.lower(),
            opportunity.dex_a.lower(),
            opportunity.dex_b.lower()
        ]
        
        metadata = {
            "failure_reason": reason,
            "potential_profit": getattr(opportunity, 'potential_profit', 0),
            "timestamp": datetime.now().isoformat()
        }
        
        await self._store_memory(memory_content, tags, "learning", metadata)
    
    async def optimize_bridge_costs(self, chain_a: str, chain_b: str, amount: float) -> Dict[str, Any]:
        """Get bridge cost optimization suggestions from memory"""
        query = f"bridge cost {chain_a} {chain_b} optimization"
        bridge_memories = await self._recall_memories(query, 5)
        
        # Default bridge costs (you'd replace with actual API calls)
        default_cost = amount * 0.001  # 0.1% default
        
        optimization = {
            "recommended_bridge": "synapse",  # From your memories
            "estimated_cost": default_cost,
            "historical_insights": bridge_memories,
            "confidence": "medium"
        }
        
        # Adjust based on historical data
        if any("synapse" in memory.lower() and "0.90" in memory for memory in bridge_memories):
            optimization["estimated_cost"] = min(default_cost, 0.90)
            optimization["confidence"] = "high"
        
        return optimization

async def main():
    """Test the memory-enhanced arbitrage bot"""
    print("🧠 Testing Memory-Enhanced Arbitrage Bot")
    print("=" * 50)
    
    # Initialize the bot
    bot = MemoryEnhancedArbitrageBot()
    
    # Wait for memory initialization
    await asyncio.sleep(2)
    
    # Test storing a market insight
    await bot.store_market_insight(
        "ETH/USDC pair showing increased volatility on smaller DEXes during US market hours",
        ["eth", "usdc", "volatility", "us-hours"],
        {"volatility_increase": 15.2, "time_period": "9am-4pm EST"}
    )
    
    # Test getting performance summary
    summary = await bot.get_trading_performance_summary()
    print(f"Trading Performance Summary:")
    print(f"- Recent trades: {summary.get('recent_trades_count', 0)}")
    print(f"- Memory system: {summary.get('memory_system_status', 'unknown')}")
    
    # Test bridge cost optimization
    bridge_opt = await bot.optimize_bridge_costs("ethereum", "arbitrum", 500)
    print(f"\nBridge Optimization for ETH->ARB ($500):")
    print(f"- Recommended: {bridge_opt['recommended_bridge']}")
    print(f"- Estimated cost: ${bridge_opt['estimated_cost']:.2f}")
    print(f"- Confidence: {bridge_opt['confidence']}")
    
    print("\n✅ Memory-Enhanced Arbitrage Bot test completed!")

if __name__ == "__main__":
    asyncio.run(main())
