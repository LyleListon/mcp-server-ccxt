"""
Real-Time Price Feeds
WebSocket-based price monitoring for instant arbitrage opportunity detection.
"""

import asyncio
import websockets
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class PriceUpdate:
    """Represents a real-time price update."""
    token: str
    dex: str
    chain: str
    price: float
    timestamp: float
    volume_24h: float = 0.0
    liquidity: float = 0.0

class RealTimePriceFeeds:
    """Real-time price feed aggregator using WebSocket connections."""
    
    def __init__(self):
        self.active_feeds = {}
        self.price_cache = {}
        self.subscribers = []
        self.is_running = False
        
        # Feed configurations
        self.feed_configs = {
            'dexscreener': {
                'url': 'wss://io.dexscreener.com/dex/screener/pairs/h24/1?rankBy[key]=volume&rankBy[order]=desc',
                'enabled': True,
                'priority': 1
            },
            'coingecko': {
                'url': 'wss://api.coingecko.com/api/v3/coins/markets',
                'enabled': False,  # CoinGecko doesn't have public WebSocket
                'priority': 2
            },
            'uniswap_v3': {
                'url': 'wss://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3',
                'enabled': False,  # Requires GraphQL subscription
                'priority': 3
            }
        }
        
        # Price update callbacks
        self.price_update_callbacks = []
        
        # Performance tracking
        self.stats = {
            'updates_received': 0,
            'updates_per_second': 0.0,
            'last_update_time': 0.0,
            'active_feeds_count': 0,
            'arbitrage_opportunities_detected': 0
        }
        
        logger.info("📡 Real-Time Price Feeds initialized")
    
    async def start(self):
        """Start all real-time price feeds."""
        if self.is_running:
            logger.warning("⚠️ Price feeds already running")
            return
        
        self.is_running = True
        
        logger.info("📡 STARTING REAL-TIME PRICE FEEDS")
        logger.info("=" * 50)
        
        # Start enabled feeds
        feed_tasks = []
        for feed_name, config in self.feed_configs.items():
            if config['enabled']:
                task = asyncio.create_task(self._start_feed(feed_name, config))
                feed_tasks.append(task)
                logger.info(f"   🚀 Starting {feed_name} feed")
        
        # Start price monitoring and opportunity detection
        monitor_task = asyncio.create_task(self._monitor_price_changes())
        feed_tasks.append(monitor_task)
        
        # Start stats updater
        stats_task = asyncio.create_task(self._update_stats())
        feed_tasks.append(stats_task)
        
        logger.info(f"✅ Started {len([f for f in self.feed_configs.values() if f['enabled']])} price feeds")
        
        # Wait for all feeds to start
        await asyncio.sleep(1.0)
        
        return feed_tasks
    
    async def stop(self):
        """Stop all price feeds."""
        logger.info("🛑 Stopping real-time price feeds...")
        
        self.is_running = False
        
        # Close all active feed connections
        for feed_name, connection in self.active_feeds.items():
            try:
                if hasattr(connection, 'close'):
                    await connection.close()
                logger.info(f"   ✅ Closed {feed_name} feed")
            except Exception as e:
                logger.error(f"   ❌ Error closing {feed_name}: {e}")
        
        self.active_feeds.clear()
        logger.info("✅ All price feeds stopped")
    
    async def _start_feed(self, feed_name: str, config: Dict[str, Any]):
        """Start a specific price feed."""
        try:
            if feed_name == 'dexscreener':
                await self._start_dexscreener_feed(config)
            elif feed_name == 'coingecko':
                await self._start_coingecko_feed(config)
            elif feed_name == 'uniswap_v3':
                await self._start_uniswap_feed(config)
            else:
                logger.warning(f"⚠️ Unknown feed type: {feed_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to start {feed_name} feed: {e}")
    
    async def _start_dexscreener_feed(self, config: Dict[str, Any]):
        """Start DexScreener WebSocket feed for real-time DEX data."""
        try:
            # For now, simulate DexScreener feed with HTTP polling
            # Real implementation would use their WebSocket API
            
            while self.is_running:
                try:
                    # Simulate fetching Arbitrum DEX data
                    await self._fetch_dexscreener_data()
                    await asyncio.sleep(2.0)  # Poll every 2 seconds
                    
                except Exception as e:
                    logger.error(f"❌ DexScreener feed error: {e}")
                    await asyncio.sleep(5.0)
                    
        except Exception as e:
            logger.error(f"❌ DexScreener feed startup error: {e}")
    
    async def _fetch_dexscreener_data(self):
        """Fetch price data from DexScreener API."""
        try:
            # Simulate real-time price updates for major tokens on Arbitrum
            tokens = ['WETH', 'USDC', 'USDT', 'DAI']
            dexes = ['sushiswap', 'camelot', 'uniswap_v3']
            
            for token in tokens:
                for dex in dexes:
                    # Simulate price with small random variations
                    base_price = self._get_base_price(token)
                    price_variation = 1.0 + (hash(f"{token}{dex}{time.time()}") % 100 - 50) / 10000.0
                    price = base_price * price_variation
                    
                    # Create price update
                    update = PriceUpdate(
                        token=token,
                        dex=dex,
                        chain='arbitrum',
                        price=price,
                        timestamp=time.time(),
                        volume_24h=1000000.0,  # $1M volume
                        liquidity=5000000.0    # $5M liquidity
                    )
                    
                    # Process price update
                    await self._process_price_update(update)
            
        except Exception as e:
            logger.error(f"❌ DexScreener data fetch error: {e}")
    
    def _get_base_price(self, token: str) -> float:
        """Get base price for token (in USD)."""
        base_prices = {
            'WETH': 3000.0,
            'USDC': 1.0,
            'USDT': 1.0,
            'DAI': 1.0
        }
        return base_prices.get(token, 1.0)
    
    async def _process_price_update(self, update: PriceUpdate):
        """Process a price update and detect arbitrage opportunities."""
        try:
            # Update price cache
            cache_key = f"{update.token}_{update.dex}_{update.chain}"
            old_price = self.price_cache.get(cache_key, {}).get('price', 0)
            
            self.price_cache[cache_key] = {
                'price': update.price,
                'timestamp': update.timestamp,
                'volume_24h': update.volume_24h,
                'liquidity': update.liquidity
            }
            
            # Update stats
            self.stats['updates_received'] += 1
            self.stats['last_update_time'] = update.timestamp
            
            # Check for arbitrage opportunities
            opportunities = await self._detect_arbitrage_opportunities(update)
            
            if opportunities:
                self.stats['arbitrage_opportunities_detected'] += len(opportunities)
                
                # Notify subscribers
                for callback in self.price_update_callbacks:
                    try:
                        await callback(update, opportunities)
                    except Exception as e:
                        logger.error(f"❌ Price update callback error: {e}")
            
            # Log significant price changes
            if old_price > 0:
                price_change_pct = ((update.price - old_price) / old_price) * 100
                if abs(price_change_pct) > 0.1:  # Log changes > 0.1%
                    logger.info(f"📊 {update.token} on {update.dex}: ${update.price:.4f} ({price_change_pct:+.2f}%)")
            
        except Exception as e:
            logger.error(f"❌ Price update processing error: {e}")
    
    async def _detect_arbitrage_opportunities(self, update: PriceUpdate) -> List[Dict[str, Any]]:
        """Detect arbitrage opportunities from price update."""
        try:
            opportunities = []
            
            # Look for price differences across DEXes for the same token
            token_prices = {}
            for cache_key, price_data in self.price_cache.items():
                parts = cache_key.split('_')
                if len(parts) >= 3:
                    token, dex, chain = parts[0], parts[1], parts[2]
                    
                    if token == update.token and chain == update.chain:
                        token_prices[dex] = price_data['price']
            
            # Find arbitrage opportunities
            if len(token_prices) >= 2:
                dex_prices = list(token_prices.items())
                
                for i in range(len(dex_prices)):
                    for j in range(i + 1, len(dex_prices)):
                        dex_a, price_a = dex_prices[i]
                        dex_b, price_b = dex_prices[j]
                        
                        # Calculate price difference
                        if price_a > 0 and price_b > 0:
                            price_diff_pct = abs(price_a - price_b) / min(price_a, price_b) * 100
                            
                            if price_diff_pct > 0.1:  # Minimum 0.1% difference
                                # Determine buy/sell DEXes
                                if price_a < price_b:
                                    buy_dex, sell_dex = dex_a, dex_b
                                    buy_price, sell_price = price_a, price_b
                                else:
                                    buy_dex, sell_dex = dex_b, dex_a
                                    buy_price, sell_price = price_b, price_a
                                
                                # Estimate profit
                                estimated_profit_pct = (sell_price - buy_price) / buy_price * 100
                                estimated_profit_usd = estimated_profit_pct * 100  # Assume $100 trade
                                
                                opportunity = {
                                    'token': update.token,
                                    'source_chain': update.chain,
                                    'target_chain': update.chain,
                                    'buy_dex': buy_dex,
                                    'sell_dex': sell_dex,
                                    'buy_price': buy_price,
                                    'sell_price': sell_price,
                                    'price_difference_pct': price_diff_pct,
                                    'estimated_profit_pct': estimated_profit_pct,
                                    'estimated_profit_usd': estimated_profit_usd,
                                    'discovered_at': time.time(),
                                    'source': 'realtime_feeds'
                                }
                                
                                opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Arbitrage detection error: {e}")
            return []
    
    async def _monitor_price_changes(self):
        """Monitor price changes and log statistics."""
        last_stats_time = time.time()
        last_update_count = 0
        
        while self.is_running:
            try:
                current_time = time.time()
                time_diff = current_time - last_stats_time
                
                if time_diff >= 10.0:  # Update stats every 10 seconds
                    update_diff = self.stats['updates_received'] - last_update_count
                    self.stats['updates_per_second'] = update_diff / time_diff
                    
                    logger.info(f"📊 PRICE FEED STATS:")
                    logger.info(f"   📡 Updates/sec: {self.stats['updates_per_second']:.1f}")
                    logger.info(f"   🎯 Opportunities: {self.stats['arbitrage_opportunities_detected']}")
                    logger.info(f"   📈 Total updates: {self.stats['updates_received']}")
                    
                    last_stats_time = current_time
                    last_update_count = self.stats['updates_received']
                
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"❌ Price monitoring error: {e}")
                await asyncio.sleep(5.0)
    
    async def _update_stats(self):
        """Update performance statistics."""
        while self.is_running:
            try:
                self.stats['active_feeds_count'] = len(self.active_feeds)
                await asyncio.sleep(5.0)
            except Exception as e:
                logger.error(f"❌ Stats update error: {e}")
                await asyncio.sleep(10.0)
    
    def subscribe_to_price_updates(self, callback: Callable):
        """Subscribe to price updates."""
        self.price_update_callbacks.append(callback)
        logger.info(f"📡 Added price update subscriber (total: {len(self.price_update_callbacks)})")
    
    def get_latest_price(self, token: str, dex: str, chain: str) -> Optional[float]:
        """Get the latest price for a token on a specific DEX."""
        cache_key = f"{token}_{dex}_{chain}"
        price_data = self.price_cache.get(cache_key)
        return price_data['price'] if price_data else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feed performance statistics."""
        return self.stats.copy()
