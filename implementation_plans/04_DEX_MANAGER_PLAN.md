# DEX Manager Implementation Plan

## Overview
**Priority: HIGH** - Required for comprehensive opportunity detection
**Current Status: 70% Complete** - Good foundation, missing implementations
**Estimated Time: 1-2 weeks**

## Current State Analysis

### What Exists (70%):
- Excellent architecture with 15+ DEX support
- Async connection management
- Basic arbitrage detection logic
- Market data caching (30-second TTL)
- Common pair discovery

### What's Missing (30%):
- **Many DEX adapters are placeholders** without real implementations
- No rate limiting for API calls
- Missing real-time WebSocket feeds
- Limited error handling and retry logic
- No connection pooling

## Implementation Plan

### Phase 1: Complete DEX Adapter Implementations (Days 1-7)

#### Day 1-2: Major DEX Adapters
```python
# File: src/dex_adapters/uniswap_v3_adapter.py
class UniswapV3Adapter:
    """Complete Uniswap V3 integration"""
    
    def __init__(self, config: Dict):
        self.web3_connections = {}
        self.factory_addresses = {
            'ethereum': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
            'arbitrum': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
            'optimism': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
            'base': '0x33128a8fC17869897dcE68Ed026d694621f6FDfD',
            'polygon': '0x1F98431c8aD98523631AE4a59f267346ea31F984'
        }
        
    async def get_pair_price(self, token_a: str, token_b: str, chain: str) -> float:
        """Get price from Uniswap V3 pool"""
        try:
            # Find the best pool (highest liquidity)
            pool_address = await self.find_best_pool(token_a, token_b, chain)
            if not pool_address:
                raise DEXError(f"No Uniswap V3 pool found for {token_a}/{token_b}")
            
            # Get current price from pool
            pool_contract = self.get_pool_contract(pool_address, chain)
            slot0 = await pool_contract.functions.slot0().call()
            
            # Calculate price from sqrtPriceX96
            sqrt_price_x96 = slot0[0]
            price = self.sqrt_price_to_price(sqrt_price_x96, token_a, token_b)
            
            return price
            
        except Exception as e:
            logger.error(f"Uniswap V3 price fetch failed: {e}")
            raise DEXError(f"Uniswap V3 error: {e}")
    
    async def get_liquidity_info(self, token_a: str, token_b: str, chain: str) -> Dict:
        """Get liquidity information for pair"""
        try:
            pool_address = await self.find_best_pool(token_a, token_b, chain)
            pool_contract = self.get_pool_contract(pool_address, chain)
            
            # Get pool liquidity
            liquidity = await pool_contract.functions.liquidity().call()
            
            # Get token balances
            token0_balance = await self.get_token_balance(pool_address, token_a, chain)
            token1_balance = await self.get_token_balance(pool_address, token_b, chain)
            
            return {
                'liquidity': liquidity,
                'token0_balance': token0_balance,
                'token1_balance': token1_balance,
                'pool_address': pool_address
            }
            
        except Exception as e:
            logger.error(f"Liquidity info fetch failed: {e}")
            return {'liquidity': 0, 'token0_balance': 0, 'token1_balance': 0}

# File: src/dex_adapters/sushiswap_adapter.py
class SushiSwapAdapter:
    """Complete SushiSwap integration"""
    
    async def get_pair_price(self, token_a: str, token_b: str, chain: str) -> float:
        """Get price from SushiSwap pair"""
        try:
            pair_address = await self.get_pair_address(token_a, token_b, chain)
            if not pair_address:
                raise DEXError(f"No SushiSwap pair found for {token_a}/{token_b}")
            
            pair_contract = self.get_pair_contract(pair_address, chain)
            reserves = await pair_contract.functions.getReserves().call()
            
            # Calculate price from reserves
            price = self.calculate_price_from_reserves(reserves, token_a, token_b)
            return price
            
        except Exception as e:
            logger.error(f"SushiSwap price fetch failed: {e}")
            raise DEXError(f"SushiSwap error: {e}")
```

#### Day 3-4: DEX Aggregator Adapters
```python
# File: src/dex_adapters/oneinch_adapter.py
class OneInchAdapter:
    """1inch DEX aggregator integration"""
    
    def __init__(self, config: Dict):
        self.api_key = config.get('oneinch_api_key')
        self.base_url = "https://api.1inch.dev"
        self.session = aiohttp.ClientSession()
        
    async def get_quote(self, token_in: str, token_out: str, amount: float, chain: str) -> Dict:
        """Get quote from 1inch aggregator"""
        try:
            chain_id = self.get_chain_id(chain)
            token_in_address = self.get_token_address(token_in, chain)
            token_out_address = self.get_token_address(token_out, chain)
            amount_wei = self.to_wei(amount, token_in)
            
            params = {
                'src': token_in_address,
                'dst': token_out_address,
                'amount': str(amount_wei),
                'includeTokensInfo': 'true',
                'includeProtocols': 'true'
            }
            
            headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
            
            async with self.session.get(
                f"{self.base_url}/swap/v6.0/{chain_id}/quote",
                params=params,
                headers=headers,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_oneinch_quote(data)
                else:
                    raise DEXError(f"1inch API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"1inch quote failed: {e}")
            raise DEXError(f"1inch error: {e}")

# File: src/dex_adapters/paraswap_adapter.py
class ParaswapAdapter:
    """Paraswap DEX aggregator integration"""
    
    async def get_quote(self, token_in: str, token_out: str, amount: float, chain: str) -> Dict:
        """Get quote from Paraswap aggregator"""
        try:
            network_id = self.get_network_id(chain)
            
            params = {
                'srcToken': self.get_token_address(token_in, chain),
                'destToken': self.get_token_address(token_out, chain),
                'amount': str(self.to_wei(amount, token_in)),
                'network': network_id,
                'side': 'SELL'
            }
            
            async with self.session.get(
                f"https://apiv5.paraswap.io/prices",
                params=params,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_paraswap_quote(data)
                else:
                    raise DEXError(f"Paraswap API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Paraswap quote failed: {e}")
            raise DEXError(f"Paraswap error: {e}")
```

#### Day 5-6: Specialized DEX Adapters
```python
# File: src/dex_adapters/camelot_adapter.py
class CamelotAdapter:
    """Camelot DEX (Arbitrum native) integration"""
    
    async def get_pair_price(self, token_a: str, token_b: str, chain: str = 'arbitrum') -> float:
        """Get price from Camelot pair"""
        # Camelot is Arbitrum-specific
        if chain != 'arbitrum':
            raise DEXError("Camelot only available on Arbitrum")
        
        # Implementation similar to SushiSwap but with Camelot contracts

# File: src/dex_adapters/aerodrome_adapter.py
class AerodromeAdapter:
    """Aerodrome DEX (Base native) integration"""
    
    async def get_pair_price(self, token_a: str, token_b: str, chain: str = 'base') -> float:
        """Get price from Aerodrome pair"""
        # Aerodrome is Base-specific
        if chain != 'base':
            raise DEXError("Aerodrome only available on Base")
        
        # Implementation for Aerodrome's unique AMM model

# File: src/dex_adapters/traderjoe_adapter.py
class TraderJoeAdapter:
    """Trader Joe DEX integration"""
    
    async def get_pair_price(self, token_a: str, token_b: str, chain: str) -> float:
        """Get price from Trader Joe pair"""
        # Available on Arbitrum and Avalanche
        if chain not in ['arbitrum', 'avalanche']:
            raise DEXError("Trader Joe not available on this chain")
```

#### Day 7: Adapter Integration and Testing
- Integrate all new adapters into DEX manager
- Test each adapter with real API calls
- Validate price accuracy and error handling

### Phase 2: Enhanced Connection Management (Days 8-10)

#### Day 8: Rate Limiting System
```python
# File: src/dex_manager/rate_limiter.py
class DEXRateLimiter:
    """Manage rate limits across all DEX APIs"""
    
    def __init__(self):
        self.rate_limits = {
            'uniswap_v3': {'requests_per_second': 10, 'burst_limit': 50},
            'sushiswap': {'requests_per_second': 5, 'burst_limit': 20},
            'oneinch': {'requests_per_second': 2, 'burst_limit': 10},  # Stricter limits
            'paraswap': {'requests_per_second': 3, 'burst_limit': 15},
            'camelot': {'requests_per_second': 5, 'burst_limit': 25},
            'aerodrome': {'requests_per_second': 5, 'burst_limit': 25}
        }
        self.request_history = {}
        
    async def acquire_permit(self, dex_name: str) -> bool:
        """Acquire permission to make API request"""
        now = time.time()
        
        # Clean old requests
        self.cleanup_old_requests(dex_name, now)
        
        # Check if we can make request
        if self.can_make_request(dex_name, now):
            self.record_request(dex_name, now)
            return True
        else:
            # Calculate wait time
            wait_time = self.calculate_wait_time(dex_name, now)
            await asyncio.sleep(wait_time)
            return await self.acquire_permit(dex_name)
    
    def can_make_request(self, dex_name: str, now: float) -> bool:
        """Check if request can be made without violating limits"""
        history = self.request_history.get(dex_name, [])
        limits = self.rate_limits.get(dex_name, {'requests_per_second': 1})
        
        # Check requests in last second
        recent_requests = [req for req in history if now - req < 1.0]
        
        return len(recent_requests) < limits['requests_per_second']
```

#### Day 9: Connection Pooling
```python
# File: src/dex_manager/connection_pool.py
class DEXConnectionPool:
    """Manage persistent connections to DEXs"""
    
    def __init__(self, max_connections_per_dex: int = 5):
        self.pools = {}
        self.max_connections = max_connections_per_dex
        
    async def get_connection(self, dex_name: str, chain: str) -> aiohttp.ClientSession:
        """Get connection from pool"""
        pool_key = f"{dex_name}_{chain}"
        
        if pool_key not in self.pools:
            self.pools[pool_key] = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    limit=self.max_connections,
                    limit_per_host=self.max_connections
                ),
                timeout=aiohttp.ClientTimeout(total=30)
            )
        
        return self.pools[pool_key]
    
    async def cleanup(self):
        """Cleanup all connection pools"""
        for session in self.pools.values():
            await session.close()
        self.pools.clear()
```

#### Day 10: Enhanced Error Handling
```python
# File: src/dex_manager/error_handler.py
class DEXErrorHandler:
    """Handle DEX-specific errors and retries"""
    
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 0.5,
            'max_delay': 5.0
        }
        
    async def execute_with_retry(self, dex_call, dex_name: str, *args, **kwargs):
        """Execute DEX call with retry logic"""
        last_exception = None
        
        for attempt in range(self.retry_config['max_retries']):
            try:
                # Acquire rate limit permit
                await self.rate_limiter.acquire_permit(dex_name)
                
                # Execute the call
                result = await dex_call(*args, **kwargs)
                return result
                
            except DEXRateLimitError as e:
                # Rate limited, wait longer
                wait_time = self.retry_config['base_delay'] * (2 ** attempt)
                await asyncio.sleep(min(wait_time, self.retry_config['max_delay']))
                last_exception = e
                
            except DEXTemporaryError as e:
                # Temporary error, retry with backoff
                wait_time = self.retry_config['base_delay'] * (2 ** attempt)
                await asyncio.sleep(wait_time)
                last_exception = e
                
            except DEXPermanentError as e:
                # Permanent error, don't retry
                raise e
                
        # All retries failed
        raise DEXError(f"All retries failed for {dex_name}: {last_exception}")
```

### Phase 3: Real-Time Features and Optimization (Days 11-14)

#### Day 11-12: WebSocket Integration
```python
# File: src/dex_manager/websocket_manager.py
class DEXWebSocketManager:
    """Manage WebSocket connections for real-time data"""
    
    def __init__(self):
        self.active_streams = {}
        self.price_callbacks = []
        
    async def start_price_streams(self, pairs: List[tuple]):
        """Start real-time price streams for pairs"""
        for token_a, token_b, chain in pairs:
            try:
                # Start streams for DEXs that support WebSocket
                if self.supports_websocket('uniswap_v3', chain):
                    stream_task = asyncio.create_task(
                        self.stream_uniswap_prices(token_a, token_b, chain),
                        name=f"uniswap_stream_{token_a}_{token_b}_{chain}"
                    )
                    self.active_streams[f"uniswap_{token_a}_{token_b}_{chain}"] = stream_task
                    
            except Exception as e:
                logger.error(f"Failed to start stream for {token_a}/{token_b}: {e}")
    
    async def stream_uniswap_prices(self, token_a: str, token_b: str, chain: str):
        """Stream real-time prices from Uniswap"""
        while True:
            try:
                # Connect to Uniswap WebSocket (if available)
                # Or poll at high frequency
                await self.poll_uniswap_price(token_a, token_b, chain)
                await asyncio.sleep(1)  # 1-second updates
                
            except Exception as e:
                logger.error(f"WebSocket stream error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
```

#### Day 13-14: Performance Optimization
```python
# File: src/dex_manager/optimized_manager.py
class OptimizedDEXManager:
    """Performance-optimized DEX manager"""
    
    async def get_batch_prices(self, pair_requests: List[tuple]) -> Dict:
        """Get prices for multiple pairs efficiently"""
        # Group requests by DEX for batching
        dex_batches = self.group_requests_by_dex(pair_requests)
        
        # Execute batches in parallel
        batch_tasks = []
        for dex_name, requests in dex_batches.items():
            if self.supports_batch_requests(dex_name):
                task = asyncio.create_task(
                    self.execute_batch_request(dex_name, requests),
                    name=f"batch_{dex_name}"
                )
            else:
                # Execute individual requests in parallel
                task = asyncio.create_task(
                    self.execute_parallel_requests(dex_name, requests),
                    name=f"parallel_{dex_name}"
                )
            batch_tasks.append(task)
        
        # Collect results
        results = {}
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, dict):
                results.update(result)
            elif isinstance(result, Exception):
                logger.error(f"Batch request failed: {result}")
        
        return results
    
    async def find_arbitrage_opportunities_optimized(self, min_profit_percentage: float = 0.5) -> List[Dict]:
        """Optimized arbitrage opportunity detection"""
        # Get all pairs from all DEXs efficiently
        all_pairs = await self.get_all_pairs_optimized()
        
        # Find common pairs across DEXs
        common_pairs = self.find_common_pairs_optimized(all_pairs)
        
        # Filter pairs by volume and liquidity
        high_value_pairs = self.filter_high_value_pairs(common_pairs)
        
        # Get prices for high-value pairs only
        price_data = await self.get_batch_prices(high_value_pairs)
        
        # Detect arbitrage opportunities
        opportunities = self.detect_opportunities_from_prices(price_data, min_profit_percentage)
        
        return opportunities
```

## Success Criteria

### Phase 1 Success:
- ✅ All 15+ DEX adapters implemented and working
- ✅ Real price data from all major DEXs
- ✅ Error handling prevents adapter failures

### Phase 2 Success:
- ✅ Rate limiting prevents API abuse
- ✅ Connection pooling improves performance
- ✅ Retry logic handles temporary failures

### Phase 3 Success:
- ✅ Real-time price updates working
- ✅ Batch processing optimizes API usage
- ✅ Opportunity detection is fast (<5 seconds)

## Risk Mitigation

### API Reliability
1. **Multiple DEX sources** - Redundancy across protocols
2. **Retry logic** - Handle temporary failures
3. **Rate limiting** - Prevent API bans

### Performance
1. **Connection pooling** - Reuse connections
2. **Batch processing** - Optimize API calls
3. **Intelligent caching** - Reduce redundant requests

## Testing Strategy

### Unit Tests
- Test each DEX adapter individually
- Test rate limiting functionality
- Test error handling scenarios

### Integration Tests
- Test with real DEX APIs
- Test batch processing performance
- Test arbitrage detection accuracy

This implementation will complete the DEX manager with real integrations, providing comprehensive market coverage essential for maximum arbitrage opportunity detection.
