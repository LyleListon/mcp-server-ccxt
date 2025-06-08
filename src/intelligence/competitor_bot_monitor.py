#!/usr/bin/env python3
"""
🕵️‍♂️ COMPETITOR BOT MONITOR
Monitor and exploit competitor arbitrage bots on Arbitrum
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from web3 import Web3
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class BotActivity:
    """Competitor bot activity data."""
    bot_address: str
    transaction_hash: str
    function_called: str
    tokens_involved: List[str]
    profit_made: Optional[float]
    gas_used: int
    gas_price: int
    timestamp: datetime
    success: bool

@dataclass
class BotIntelligence:
    """Intelligence data about a competitor bot."""
    address: str
    name: str
    total_trades: int
    successful_trades: int
    failed_trades: int
    total_profit: float
    average_profit: float
    favorite_tokens: List[str]
    active_hours: List[int]
    gas_strategy: Dict[str, Any]
    last_activity: datetime

class CompetitorBotMonitor:
    """Monitor competitor arbitrage bots and learn from them."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize bot monitor."""
        self.config = config
        
        # Web3 connection
        alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
        self.w3 = Web3(Web3.HTTPProvider(f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_api_key}"))
        
        # Load competitor bot addresses from ABI exports
        self.competitor_bots = self._load_competitor_bots()
        
        # Intelligence database
        self.bot_intelligence: Dict[str, BotIntelligence] = {}
        self.recent_activities: List[BotActivity] = []
        
        # Monitoring settings
        self.monitoring_enabled = True
        self.profit_threshold = 0.01  # $0.01 minimum to track
        
        logger.info(f"🕵️ Competitor monitor initialized with {len(self.competitor_bots)} bots")
    
    def _load_competitor_bots(self) -> Dict[str, Dict[str, Any]]:
        """Load competitor bot addresses and ABIs from exports."""
        bots = {}
        
        try:
            abi_dir = "abi_exports/arbitrum"
            if os.path.exists(abi_dir):
                for filename in os.listdir(abi_dir):
                    if filename.endswith('.json'):
                        # Extract address from filename
                        address = filename.split('_')[-1].replace('.json', '')
                        if address.startswith('0x') and len(address) == 42:
                            
                            # Load ABI
                            with open(os.path.join(abi_dir, filename), 'r') as f:
                                abi = json.load(f)
                            
                            # Check if it's an arbitrage bot
                            if self._is_arbitrage_bot(abi):
                                bots[address] = {
                                    'abi': abi,
                                    'name': self._extract_bot_name(abi),
                                    'functions': self._extract_key_functions(abi)
                                }
                                logger.info(f"🤖 Found arbitrage bot: {address}")
            
            logger.info(f"🕵️ Loaded {len(bots)} competitor arbitrage bots")
            return bots
            
        except Exception as e:
            logger.error(f"Error loading competitor bots: {e}")
            return {}
    
    def _is_arbitrage_bot(self, abi: List[Dict]) -> bool:
        """Check if ABI belongs to an arbitrage bot."""
        arbitrage_indicators = [
            'executeArbitrage',
            'flashLoan',
            'ArbExecuted',
            'ProfitMade',
            'FlashLoanStarted'
        ]
        
        abi_text = json.dumps(abi).lower()
        return any(indicator.lower() in abi_text for indicator in arbitrage_indicators)
    
    def _extract_bot_name(self, abi: List[Dict]) -> str:
        """Extract bot name from ABI."""
        # Look for contract name or identifier
        for item in abi:
            if item.get('type') == 'function' and 'name' in item.get('name', '').lower():
                return item['name']
        return "Unknown Bot"
    
    def _extract_key_functions(self, abi: List[Dict]) -> List[str]:
        """Extract key function signatures."""
        key_functions = []
        important_functions = [
            'executeArbitrage',
            'flashLoan',
            'swap',
            'trade',
            'arbitrage'
        ]
        
        for item in abi:
            if item.get('type') == 'function':
                func_name = item.get('name', '')
                if any(keyword in func_name.lower() for keyword in important_functions):
                    key_functions.append(func_name)
        
        return key_functions
    
    async def start_monitoring(self):
        """Start monitoring competitor bots."""
        logger.info("🕵️ Starting competitor bot monitoring...")
        
        tasks = [
            self._monitor_bot_transactions(),
            self._analyze_bot_patterns(),
            self._generate_intelligence_reports()
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _monitor_bot_transactions(self):
        """Monitor transactions from competitor bots."""
        while self.monitoring_enabled:
            try:
                # Get latest block
                latest_block = self.w3.eth.get_block('latest', full_transactions=True)
                
                # Check transactions for bot activity
                for tx in latest_block.transactions:
                    if tx['from'] in self.competitor_bots:
                        await self._analyze_bot_transaction(tx)
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Bot monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _analyze_bot_transaction(self, tx):
        """Analyze a transaction from a competitor bot."""
        try:
            bot_address = tx['from']
            bot_info = self.competitor_bots[bot_address]
            
            # Get transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(tx['hash'])
            
            # Analyze the transaction
            activity = BotActivity(
                bot_address=bot_address,
                transaction_hash=tx['hash'].hex(),
                function_called=self._decode_function_call(tx['input'], bot_info['abi']),
                tokens_involved=self._extract_tokens_from_logs(receipt['logs']),
                profit_made=self._calculate_profit_from_logs(receipt['logs']),
                gas_used=receipt['gasUsed'],
                gas_price=tx['gasPrice'],
                timestamp=datetime.now(),
                success=receipt['status'] == 1
            )
            
            # Store activity
            self.recent_activities.append(activity)
            
            # Log interesting activities
            if activity.success and activity.profit_made and activity.profit_made > self.profit_threshold:
                logger.info(f"🎯 PROFITABLE BOT ACTIVITY!")
                logger.info(f"   Bot: {bot_address[:10]}...")
                logger.info(f"   Function: {activity.function_called}")
                logger.info(f"   Profit: ${activity.profit_made:.4f}")
                logger.info(f"   Tokens: {activity.tokens_involved}")
                logger.info(f"   Gas: {activity.gas_used:,} @ {activity.gas_price/1e9:.2f} Gwei")
                
                # 🚀 OPPORTUNITY: Try to copy this trade!
                await self._attempt_copy_trade(activity)
            
        except Exception as e:
            logger.error(f"Transaction analysis error: {e}")
    
    def _decode_function_call(self, input_data: str, abi: List[Dict]) -> str:
        """Decode function call from input data."""
        if len(input_data) < 10:
            return "unknown"
        
        function_selector = input_data[:10]
        
        # Try to match with ABI
        for item in abi:
            if item.get('type') == 'function':
                # This is simplified - in reality you'd use web3.py's contract interface
                return item.get('name', 'unknown')
        
        return f"selector_{function_selector}"
    
    def _extract_tokens_from_logs(self, logs: List[Dict]) -> List[str]:
        """Extract token addresses from transaction logs."""
        tokens = set()
        
        for log in logs:
            # Look for ERC20 Transfer events and DEX swap events
            if len(log['topics']) > 0:
                # This is simplified - you'd decode the actual events
                tokens.add(log['address'])
        
        return list(tokens)[:5]  # Limit to 5 tokens
    
    def _calculate_profit_from_logs(self, logs: List[Dict]) -> Optional[float]:
        """Calculate profit from transaction logs."""
        # This is simplified - you'd need to decode actual profit events
        # Look for ProfitMade events or balance changes
        return None  # Placeholder
    
    async def _attempt_copy_trade(self, activity: BotActivity):
        """Attempt to copy a profitable trade."""
        logger.info(f"🎯 ATTEMPTING TO COPY PROFITABLE TRADE!")
        logger.info(f"   Original bot: {activity.bot_address[:10]}...")
        logger.info(f"   Tokens: {activity.tokens_involved}")
        logger.info(f"   Profit: ${activity.profit_made:.4f}")
        logger.info(f"   Gas used: {activity.gas_used:,} @ {activity.gas_price/1e9:.2f} Gwei")

        try:
            # 🚀 PROFIT COPYING STRATEGY

            # 1. Extract trade parameters from the successful transaction
            trade_params = await self._extract_trade_parameters(activity)

            if trade_params:
                logger.info(f"   📊 Extracted trade parameters:")
                logger.info(f"      Token A: {trade_params.get('token_a', 'Unknown')}")
                logger.info(f"      Token B: {trade_params.get('token_b', 'Unknown')}")
                logger.info(f"      Amount: {trade_params.get('amount', 'Unknown')}")

                # 2. Check if similar opportunity still exists
                opportunity_exists = await self._check_opportunity_exists(trade_params)

                if opportunity_exists:
                    logger.info(f"   ✅ Similar opportunity still available!")

                    # 3. Execute copy trade with higher gas
                    copy_success = await self._execute_copy_trade(trade_params, activity)

                    if copy_success:
                        logger.info(f"   🎉 COPY TRADE SUCCESSFUL!")
                    else:
                        logger.info(f"   ❌ Copy trade failed")
                else:
                    logger.info(f"   ⚠️  Opportunity no longer available")
            else:
                logger.info(f"   ❌ Could not extract trade parameters")

        except Exception as e:
            logger.error(f"Copy trade error: {e}")

    async def _extract_trade_parameters(self, activity: BotActivity) -> Optional[Dict[str, Any]]:
        """Extract trade parameters from successful bot transaction."""
        try:
            # Get transaction details
            tx = self.w3.eth.get_transaction(activity.transaction_hash)
            receipt = self.w3.eth.get_transaction_receipt(activity.transaction_hash)

            # Basic parameters
            params = {
                'transaction_hash': activity.transaction_hash,
                'gas_used': activity.gas_used,
                'gas_price': activity.gas_price,
                'tokens': activity.tokens_involved,
                'profit': activity.profit_made
            }

            # Try to decode more specific parameters from logs
            if receipt['logs']:
                # Look for swap events, transfer events, etc.
                for log in receipt['logs']:
                    # This is simplified - you'd decode actual events
                    if len(log['topics']) > 0:
                        params['dex_address'] = log['address']
                        break

            return params

        except Exception as e:
            logger.error(f"Parameter extraction error: {e}")
            return None

    async def _check_opportunity_exists(self, trade_params: Dict[str, Any]) -> bool:
        """Check if similar arbitrage opportunity still exists."""
        try:
            # This is simplified - you'd check actual DEX prices
            # For now, assume opportunity exists for a short time
            return True

        except Exception as e:
            logger.error(f"Opportunity check error: {e}")
            return False

    async def _execute_copy_trade(self, trade_params: Dict[str, Any], original_activity: BotActivity) -> bool:
        """Execute a copy of the profitable trade."""
        try:
            logger.info(f"   🚀 EXECUTING COPY TRADE...")

            # Calculate higher gas price to beat the original
            original_gas_price = original_activity.gas_price
            our_gas_price = int(original_gas_price * 1.2)  # 20% higher

            logger.info(f"   ⚡ Using {our_gas_price/1e9:.2f} Gwei (vs {original_gas_price/1e9:.2f} Gwei)")

            # TODO: Integrate with your arbitrage executor
            # This would call your flashloan system or wallet arbitrage

            # For now, just log the attempt
            logger.info(f"   📝 Copy trade parameters:")
            logger.info(f"      Tokens: {trade_params.get('tokens', [])}")
            logger.info(f"      Gas Price: {our_gas_price/1e9:.2f} Gwei")
            logger.info(f"      Expected Profit: ${trade_params.get('profit', 0):.4f}")

            # Simulate execution (replace with actual arbitrage call)
            await asyncio.sleep(0.1)  # Simulate execution time

            return True  # Placeholder success

        except Exception as e:
            logger.error(f"Copy trade execution error: {e}")
            return False
        
    async def _analyze_bot_patterns(self):
        """Analyze patterns in bot behavior."""
        while self.monitoring_enabled:
            try:
                # Analyze recent activities every 5 minutes
                await asyncio.sleep(300)
                
                if len(self.recent_activities) > 10:
                    logger.info("📊 Analyzing bot patterns...")
                    
                    # Group by bot
                    bot_activities = {}
                    for activity in self.recent_activities[-100:]:  # Last 100 activities
                        if activity.bot_address not in bot_activities:
                            bot_activities[activity.bot_address] = []
                        bot_activities[activity.bot_address].append(activity)
                    
                    # Analyze each bot
                    for bot_address, activities in bot_activities.items():
                        self._update_bot_intelligence(bot_address, activities)
                
            except Exception as e:
                logger.error(f"Pattern analysis error: {e}")
    
    def _update_bot_intelligence(self, bot_address: str, activities: List[BotActivity]):
        """Update intelligence data for a bot."""
        successful_activities = [a for a in activities if a.success]
        profitable_activities = [a for a in successful_activities if a.profit_made and a.profit_made > 0]
        
        # Update or create intelligence
        if bot_address not in self.bot_intelligence:
            self.bot_intelligence[bot_address] = BotIntelligence(
                address=bot_address,
                name=self.competitor_bots.get(bot_address, {}).get('name', 'Unknown'),
                total_trades=0,
                successful_trades=0,
                failed_trades=0,
                total_profit=0.0,
                average_profit=0.0,
                favorite_tokens=[],
                active_hours=[],
                gas_strategy={},
                last_activity=datetime.now()
            )
        
        intel = self.bot_intelligence[bot_address]
        intel.total_trades = len(activities)
        intel.successful_trades = len(successful_activities)
        intel.failed_trades = len(activities) - len(successful_activities)
        intel.total_profit = sum(a.profit_made or 0 for a in profitable_activities)
        intel.average_profit = intel.total_profit / max(len(profitable_activities), 1)
        intel.last_activity = max(a.timestamp for a in activities)
        
        # Log intelligence updates
        if intel.successful_trades > 0:
            success_rate = intel.successful_trades / intel.total_trades * 100
            logger.info(f"📊 BOT INTELLIGENCE UPDATE:")
            logger.info(f"   Bot: {bot_address[:10]}...")
            logger.info(f"   Success Rate: {success_rate:.1f}%")
            logger.info(f"   Total Profit: ${intel.total_profit:.4f}")
            logger.info(f"   Avg Profit: ${intel.average_profit:.4f}")
    
    async def _generate_intelligence_reports(self):
        """Generate periodic intelligence reports."""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(600)  # Every 10 minutes
                
                if self.bot_intelligence:
                    logger.info("📋 COMPETITOR INTELLIGENCE REPORT:")
                    
                    # Sort bots by profitability
                    sorted_bots = sorted(
                        self.bot_intelligence.values(),
                        key=lambda x: x.total_profit,
                        reverse=True
                    )
                    
                    for i, intel in enumerate(sorted_bots[:5]):  # Top 5
                        logger.info(f"   #{i+1} {intel.address[:10]}... - ${intel.total_profit:.4f} profit")
                
            except Exception as e:
                logger.error(f"Report generation error: {e}")
    
    def get_top_performers(self, limit: int = 5) -> List[BotIntelligence]:
        """Get top performing competitor bots."""
        return sorted(
            self.bot_intelligence.values(),
            key=lambda x: x.total_profit,
            reverse=True
        )[:limit]
    
    async def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring_enabled = False
        logger.info("🛑 Competitor monitoring stopped")
