# Price Feeds Implementation Plan

## Overview
**Priority: CRITICAL** - Single point of failure prevents reliable operation
**Current Status: 60% Complete** - Only Alchemy SDK, no redundancy
**Estimated Time: 1 week**

## Current State Analysis

### What Exists (60%):
- Alchemy SDK integration working
- L2-optimized opportunity scanning
- Basic caching mechanism
- Cross-chain token mapping

### What's Missing (40%):
- **Single point of failure** - Only Alchemy SDK
- No redundancy or fallback mechanisms
- No cross-validation of price data
- No real-time WebSocket feeds
- Limited error handling

## Implementation Plan

### Phase 1: Add Secondary Price Sources (Days 1-3)

#### Day 1: CoinGecko Integration
```python
# File: src/price_feeds/coingecko_adapter.py
class CoinGeckoAdapter:
    """CoinGecko API integration for price validation"""
    
    def __init__(self, config: Dict):
        self.api_key = os.getenv('COINGECKO_API_KEY')
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = aiohttp.ClientSession()
        
    async def get_token_price(self, token: str, chain: str) -> float:
        """Get token price from CoinGecko"""
        try:
            # Map token to CoinGecko ID
            coin_id = self.get_coingecko_id(token, chain)
            
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            if self.api_key:
                params['x_cg_demo_api_key'] = self.api_key
                
            async with self.session.get(
                f"{self.base_url}/simple/price",
                params=params,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data[coin_id]['usd'])
                else:
                    raise PriceFeedError(f"CoinGecko API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"CoinGecko price fetch failed for {token}: {e}")
            raise PriceFeedError(f"CoinGecko error: {e}")
    
    def get_coingecko_id(self, token: str, chain: str) -> str:
        """Map token symbol to CoinGecko coin ID"""
        token_mapping = {
            'ETH': 'ethereum',
            'USDC': 'usd-coin',
            'USDT': 'tether',
            'WBTC': 'wrapped-bitcoin',
            'DAI': 'dai'
        }
        return token_mapping.get(token, token.lower())
```

#### Day 2: DEX Direct Price Feeds
```python
# File: src/price_feeds/dex_price_adapter.py
class DEXPriceAdapter:
    """Get prices directly from DEX contracts"""
    
    def __init__(self, config: Dict):
        self.web3_connections = {}
        self.dex_contracts = {}
        
    async def get_uniswap_v3_price(self, token_pair: str, chain: str) -> float:
        """Get price from Uniswap V3 pool"""
        try:
            # Get pool contract
            pool_address = self.get_pool_address(token_pair, chain)
            pool_contract = self.get_contract(pool_address, 'uniswap_v3_pool', chain)
            
            # Get current tick and calculate price
            slot0 = await pool_contract.functions.slot0().call()
            current_tick = slot0[1]
            
            # Calculate price from tick
            price = self.tick_to_price(current_tick, token_pair)
            return price
            
        except Exception as e:
            logger.error(f"Uniswap V3 price fetch failed: {e}")
            raise PriceFeedError(f"Uniswap V3 error: {e}")
    
    def tick_to_price(self, tick: int, token_pair: str) -> float:
        """Convert Uniswap V3 tick to price"""
        # Price = 1.0001^tick
        # Adjust for token decimals
        price = (1.0001 ** tick)
        return self.adjust_for_decimals(price, token_pair)
```

#### Day 3: Premium Feed Integration
```python
# File: src/price_feeds/premium_feeds.py
class PremiumFeeds:
    """Integration with premium price feed services"""
    
    def __init__(self, config: Dict):
        self.chainlink_feeds = {}
        self.pyth_feeds = {}
        
    async def get_chainlink_price(self, token: str, chain: str) -> float:
        """Get price from Chainlink price feeds"""
        try:
            feed_address = self.get_chainlink_feed_address(token, chain)
            if not feed_address:
                raise PriceFeedError(f"No Chainlink feed for {token} on {chain}")
                
            feed_contract = self.get_contract(feed_address, 'chainlink_aggregator', chain)
            latest_data = await feed_contract.functions.latestRoundData().call()
            
            price = latest_data[1] / (10 ** 8)  # Chainlink uses 8 decimals
            return float(price)
            
        except Exception as e:
            logger.error(f"Chainlink price fetch failed: {e}")
            raise PriceFeedError(f"Chainlink error: {e}")
```

### Phase 2: Price Validation System (Days 4-5)

#### Day 4: Multi-Source Price Validation
```python
# File: src/price_feeds/price_validator.py
class PriceValidator:
    """Validate prices across multiple sources"""
    
    def __init__(self):
        self.deviation_threshold = 0.02  # 2% maximum deviation
        self.min_sources = 2
        
    async def get_validated_price(self, token: str, chain: str) -> float:
        """Get price validated across multiple sources"""
        try:
            # Collect prices from all available sources
            prices = await self.collect_prices_from_sources(token, chain)
            
            if len(prices) < self.min_sources:
                logger.warning(f"Only {len(prices)} price sources available for {token}")
                return list(prices.values())[0] if prices else None
            
            # Validate prices are consistent
            validated_price = self.validate_and_select_price(prices, token)
            
            return validated_price
            
        except Exception as e:
            logger.error(f"Price validation failed for {token}: {e}")
            raise PriceFeedError(f"Validation error: {e}")
    
    async def collect_prices_from_sources(self, token: str, chain: str) -> Dict[str, float]:
        """Collect prices from all available sources"""
        sources = {
            'alchemy': self.alchemy_feeds,
            'coingecko': self.coingecko_adapter,
            'dex_direct': self.dex_adapter,
            'chainlink': self.premium_feeds
        }
        
        prices = {}
        tasks = []
        
        for source_name, source_adapter in sources.items():
            task = asyncio.create_task(
                self.get_price_from_source(source_adapter, token, chain, source_name),
                name=f"price_{source_name}_{token}"
            )
            tasks.append(task)
        
        # Wait for all price fetches (with timeout)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            source_name = list(sources.keys())[i]
            if isinstance(result, Exception):
                logger.warning(f"Price source {source_name} failed: {result}")
            elif result is not None:
                prices[source_name] = result
                
        return prices
    
    def validate_and_select_price(self, prices: Dict[str, float], token: str) -> float:
        """Validate prices and select best one"""
        if not prices:
            raise PriceFeedError(f"No valid prices found for {token}")
        
        # Remove outliers
        clean_prices = self.remove_outliers(prices)
        
        if not clean_prices:
            logger.warning(f"All prices were outliers for {token}, using raw data")
            clean_prices = prices
        
        # Calculate weighted average (prefer more reliable sources)
        weights = {
            'alchemy': 0.4,      # Primary source
            'chainlink': 0.3,    # High reliability
            'coingecko': 0.2,    # Good for validation
            'dex_direct': 0.1    # Can be manipulated
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for source, price in clean_prices.items():
            weight = weights.get(source, 0.1)
            weighted_sum += price * weight
            total_weight += weight
        
        if total_weight == 0:
            return statistics.mean(clean_prices.values())
        
        return weighted_sum / total_weight
    
    def remove_outliers(self, prices: Dict[str, float]) -> Dict[str, float]:
        """Remove price outliers using statistical analysis"""
        if len(prices) < 3:
            return prices  # Need at least 3 prices for outlier detection
        
        price_values = list(prices.values())
        mean_price = statistics.mean(price_values)
        std_dev = statistics.stdev(price_values)
        
        # Remove prices more than 2 standard deviations from mean
        clean_prices = {}
        for source, price in prices.items():
            z_score = abs((price - mean_price) / std_dev) if std_dev > 0 else 0
            if z_score <= 2.0:  # Within 2 standard deviations
                clean_prices[source] = price
            else:
                logger.warning(f"Removing outlier price from {source}: ${price:.4f} (z-score: {z_score:.2f})")
        
        return clean_prices
```

#### Day 5: Fallback Mechanisms
```python
# File: src/price_feeds/fallback_manager.py
class FallbackManager:
    """Manage fallback strategies when price feeds fail"""
    
    def __init__(self):
        self.source_priority = ['alchemy', 'chainlink', 'coingecko', 'dex_direct']
        self.cache_fallback_duration = 300  # 5 minutes
        
    async def get_price_with_fallback(self, token: str, chain: str) -> float:
        """Get price with automatic fallback"""
        last_error = None
        
        # Try sources in priority order
        for source in self.source_priority:
            try:
                price = await self.get_price_from_source(source, token, chain)
                if price and price > 0:
                    logger.info(f"Got price for {token} from {source}: ${price:.4f}")
                    return price
            except Exception as e:
                logger.warning(f"Price source {source} failed: {e}")
                last_error = e
                continue
        
        # All sources failed, try cache
        cached_price = await self.get_cached_price(token, chain)
        if cached_price:
            cache_age = await self.get_cache_age(token, chain)
            if cache_age < self.cache_fallback_duration:
                logger.warning(f"Using cached price for {token} (age: {cache_age}s)")
                return cached_price
        
        # Everything failed
        raise PriceFeedError(f"All price sources failed for {token}: {last_error}")
```

### Phase 3: Real-Time Feeds and Optimization (Days 6-7)

#### Day 6: WebSocket Price Streams
```python
# File: src/price_feeds/websocket_feeds.py
class WebSocketPriceFeeds:
    """Real-time price streaming via WebSocket"""
    
    def __init__(self):
        self.active_streams = {}
        self.price_callbacks = []
        
    async def start_price_stream(self, tokens: List[str]):
        """Start real-time price streaming for tokens"""
        for token in tokens:
            try:
                # Start WebSocket connection for token
                stream_task = asyncio.create_task(
                    self.stream_token_price(token),
                    name=f"stream_{token}"
                )
                self.active_streams[token] = stream_task
                
            except Exception as e:
                logger.error(f"Failed to start stream for {token}: {e}")
    
    async def stream_token_price(self, token: str):
        """Stream price updates for specific token"""
        while True:
            try:
                # Connect to WebSocket feed (implementation depends on provider)
                async with websockets.connect(self.get_websocket_url(token)) as websocket:
                    async for message in websocket:
                        price_data = json.loads(message)
                        await self.handle_price_update(token, price_data)
                        
            except Exception as e:
                logger.error(f"WebSocket stream error for {token}: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
```

#### Day 7: Performance Optimization
```python
# File: src/price_feeds/optimized_feeds.py
class OptimizedPriceFeeds:
    """Optimized price feed manager"""
    
    def __init__(self):
        self.batch_size = 10
        self.cache_ttl = 30  # 30 seconds
        
    async def get_batch_prices(self, token_requests: List[tuple]) -> Dict:
        """Get multiple prices in optimized batches"""
        results = {}
        
        # Group requests by source for batching
        source_batches = self.group_requests_by_source(token_requests)
        
        # Execute batches in parallel
        batch_tasks = []
        for source, requests in source_batches.items():
            task = asyncio.create_task(
                self.execute_batch_for_source(source, requests),
                name=f"batch_{source}"
            )
            batch_tasks.append(task)
        
        # Collect results
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, dict):
                results.update(result)
            elif isinstance(result, Exception):
                logger.error(f"Batch request failed: {result}")
        
        return results
```

## Success Criteria

### Phase 1 Success:
- ✅ 3+ price sources working (Alchemy, CoinGecko, DEX direct)
- ✅ All sources return reasonable prices
- ✅ Error handling prevents crashes

### Phase 2 Success:
- ✅ Price validation catches outliers
- ✅ Fallback mechanisms work when sources fail
- ✅ System continues operating with degraded feeds

### Phase 3 Success:
- ✅ Real-time price updates working
- ✅ Performance optimized (<2 seconds for batch requests)
- ✅ System resilient to any single source failure

## Risk Mitigation

### Source Reliability
1. **Multiple sources** - No single point of failure
2. **Automatic fallback** - Graceful degradation
3. **Price validation** - Catch bad data

### Performance
1. **Intelligent caching** - Reduce API calls
2. **Batch processing** - Optimize requests
3. **WebSocket streams** - Real-time updates

## Testing Strategy

### Unit Tests
- Test each price source individually
- Test price validation logic
- Test fallback mechanisms

### Integration Tests
- Test with real API calls
- Test source failure scenarios
- Test performance under load

This implementation will eliminate the single point of failure and provide robust, validated price data essential for reliable arbitrage detection.
