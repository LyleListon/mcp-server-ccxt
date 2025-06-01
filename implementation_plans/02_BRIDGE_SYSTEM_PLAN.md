# Bridge System Implementation Plan

## Overview
**Priority: CRITICAL** - Required for cross-chain arbitrage
**Current Status: 40% Complete** - All quotes are simulated
**Estimated Time: 1-2 weeks**

## Current State Analysis

### What Exists (40%):
```python
# Good foundation in bridge_cost_monitor.py
bridge_apis = {
    'synapse': {'name': 'Synapse Protocol', 'test_priority': 1},
    'across': {'name': 'Across Protocol', 'test_priority': 2},
    'hop': {'name': 'Hop Protocol', 'test_priority': 3},
    'stargate': {'name': 'Stargate Finance', 'test_priority': 4},
    'cbridge': {'name': 'Celer cBridge', 'test_priority': 5}
}

# Good monitoring framework
monitoring_config = {
    'update_interval_minutes': 5,
    'test_amounts': [100, 500, 1000, 2000],
    'priority_routes': [('ethereum', 'arbitrum', 'ETH'), ...]
}
```

### What's Missing (60%):
```python
# CRITICAL ISSUE: All quotes are simulated
async def _get_real_bridge_quote(self, bridge_name: str, ...):
    # For now, simulate real API calls with realistic data
    # In production, this would make actual HTTP requests to bridge APIs
    
    if bridge_name == 'synapse':
        fee_percentage = 0.18  # HARDCODED!
        fee_usd = amount_usd * (fee_percentage / 100)  # FAKE!
```

## Implementation Plan

### Phase 1: Real API Integration (Days 1-7)
**Goal: Replace all simulated quotes with real API calls**

#### Day 1-2: Synapse Protocol Integration
```python
# File: src/bridges/synapse_api.py
class SynapseAPI:
    """Real Synapse Protocol API integration"""
    
    def __init__(self, config: Dict):
        self.base_url = "https://api.synapseprotocol.com"
        self.session = aiohttp.ClientSession()
        self.chain_ids = {
            'ethereum': 1, 'arbitrum': 42161, 'optimism': 10,
            'base': 8453, 'polygon': 137, 'bsc': 56
        }
        
    async def get_quote(self, source_chain: str, target_chain: str, 
                       token: str, amount_usd: float) -> BridgeQuote:
        """Get real quote from Synapse API"""
        try:
            # Convert to proper format
            source_chain_id = self.chain_ids[source_chain]
            target_chain_id = self.chain_ids[target_chain]
            token_address = self.get_token_address(token, source_chain)
            amount_wei = self.usd_to_wei(amount_usd, token)
            
            # Build API request
            params = {
                'fromChain': source_chain_id,
                'toChain': target_chain_id,
                'fromToken': token_address,
                'toToken': self.get_token_address(token, target_chain),
                'amount': str(amount_wei)
            }
            
            # Make API call
            async with self.session.get(
                f"{self.base_url}/v1/bridge/quote",
                params=params,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_synapse_response(data, amount_usd)
                else:
                    raise BridgeAPIError(f"Synapse API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Synapse quote failed: {e}")
            return BridgeQuote(
                bridge_name='synapse',
                success=False,
                error_message=str(e),
                # ... other fields
            )
    
    def parse_synapse_response(self, data: Dict, amount_usd: float) -> BridgeQuote:
        """Parse Synapse API response"""
        try:
            # Extract fee information
            fee_wei = int(data.get('feeAmount', 0))
            fee_usd = self.wei_to_usd(fee_wei, data.get('feeToken'))
            fee_percentage = (fee_usd / amount_usd) * 100
            
            # Extract time estimate
            time_minutes = data.get('estimatedTime', 300) / 60  # Convert seconds to minutes
            
            # Extract gas estimate
            gas_estimate_usd = self.wei_to_usd(
                int(data.get('gasEstimate', 0)) * int(data.get('gasPrice', 0)),
                'ETH'
            )
            
            return BridgeQuote(
                bridge_name='synapse',
                source_chain=self.chain_id_to_name(data['fromChain']),
                target_chain=self.chain_id_to_name(data['toChain']),
                token=data.get('tokenSymbol', 'ETH'),
                amount_usd=amount_usd,
                fee_usd=fee_usd,
                fee_percentage=fee_percentage,
                estimated_time_minutes=time_minutes,
                gas_estimate_usd=gas_estimate_usd,
                total_cost_usd=fee_usd + gas_estimate_usd,
                timestamp=datetime.now(),
                quote_id=data.get('quoteId'),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Failed to parse Synapse response: {e}")
            raise BridgeAPIError(f"Invalid Synapse response: {e}")
```

#### Day 3-4: Across Protocol Integration
```python
# File: src/bridges/across_api.py
class AcrossAPI:
    """Real Across Protocol API integration"""
    
    def __init__(self, config: Dict):
        self.base_url = "https://api.across.to"
        self.session = aiohttp.ClientSession()
        
    async def get_quote(self, source_chain: str, target_chain: str,
                       token: str, amount_usd: float) -> BridgeQuote:
        """Get real quote from Across API"""
        try:
            # Across uses different API structure
            params = {
                'originChainId': self.chain_ids[source_chain],
                'destinationChainId': self.chain_ids[target_chain],
                'token': self.get_token_address(token, source_chain),
                'amount': str(self.usd_to_wei(amount_usd, token))
            }
            
            async with self.session.get(
                f"{self.base_url}/api/suggested-fees",
                params=params,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_across_response(data, amount_usd)
                else:
                    raise BridgeAPIError(f"Across API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Across quote failed: {e}")
            return BridgeQuote(bridge_name='across', success=False, error_message=str(e))
    
    def parse_across_response(self, data: Dict, amount_usd: float) -> BridgeQuote:
        """Parse Across API response"""
        # Across returns fees in different format
        relay_fee_pct = float(data.get('relayFeePct', 0))
        lp_fee_pct = float(data.get('lpFeePct', 0))
        
        total_fee_percentage = (relay_fee_pct + lp_fee_pct) * 100
        fee_usd = amount_usd * (total_fee_percentage / 100)
        
        return BridgeQuote(
            bridge_name='across',
            fee_usd=fee_usd,
            fee_percentage=total_fee_percentage,
            estimated_time_minutes=data.get('estimatedFillTimeSec', 120) / 60,
            # ... other fields
        )
```

#### Day 5-6: Hop and Stargate Integration
```python
# File: src/bridges/hop_api.py
class HopAPI:
    """Real Hop Protocol API integration"""
    
    async def get_quote(self, source_chain: str, target_chain: str,
                       token: str, amount_usd: float) -> BridgeQuote:
        """Get real quote from Hop API"""
        # Hop has different API structure for AMM-based bridging
        # Need to query for bonder fees and AMM slippage
        
# File: src/bridges/stargate_api.py  
class StargateAPI:
    """Real Stargate Finance API integration"""
    
    async def get_quote(self, source_chain: str, target_chain: str,
                       token: str, amount_usd: float) -> BridgeQuote:
        """Get real quote from Stargate API"""
        # Stargate uses LayerZero messaging
        # Need to account for LayerZero fees + Stargate fees
```

#### Day 7: Celer cBridge Integration
```python
# File: src/bridges/cbridge_api.py
class CelerAPI:
    """Real Celer cBridge API integration"""
    
    async def get_quote(self, source_chain: str, target_chain: str,
                       token: str, amount_usd: float) -> BridgeQuote:
        """Get real quote from Celer cBridge API"""
        try:
            params = {
                'src_chain_id': self.chain_ids[source_chain],
                'dst_chain_id': self.chain_ids[target_chain],
                'token_symbol': token,
                'amt': str(self.usd_to_wei(amount_usd, token)),
                'usr_addr': self.get_user_address(),  # Required for some quotes
                'slippage_tolerance': 3000  # 0.3% in basis points
            }
            
            async with self.session.get(
                f"{self.base_url}/v2/estimateAmt",
                params=params,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self.parse_cbridge_response(data, amount_usd)
                else:
                    raise BridgeAPIError(f"Celer API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Celer quote failed: {e}")
            return BridgeQuote(bridge_name='cbridge', success=False, error_message=str(e))
```

### Phase 2: Enhanced Error Handling (Days 8-10)
**Goal: Robust error handling and retry logic**

#### Day 8: API Error Management
```python
# File: src/bridges/bridge_error_handler.py
class BridgeErrorHandler:
    """Handle bridge API errors and retries"""
    
    def __init__(self):
        self.retry_config = {
            'max_retries': 3,
            'base_delay': 1.0,
            'max_delay': 10.0,
            'exponential_base': 2.0
        }
        
    async def execute_with_retry(self, api_call, *args, **kwargs) -> BridgeQuote:
        """Execute API call with exponential backoff retry"""
        last_exception = None
        
        for attempt in range(self.retry_config['max_retries']):
            try:
                result = await api_call(*args, **kwargs)
                if result.success:
                    return result
                else:
                    # API returned error, decide if we should retry
                    if self.should_retry_error(result.error_message):
                        last_exception = BridgeAPIError(result.error_message)
                        await self.wait_before_retry(attempt)
                        continue
                    else:
                        return result  # Don't retry, return the error
                        
            except (aiohttp.ClientTimeout, aiohttp.ClientError) as e:
                last_exception = e
                if attempt < self.retry_config['max_retries'] - 1:
                    await self.wait_before_retry(attempt)
                    continue
                else:
                    break
                    
        # All retries failed
        return BridgeQuote(
            bridge_name='unknown',
            success=False,
            error_message=f"All retries failed: {last_exception}"
        )
    
    def should_retry_error(self, error_message: str) -> bool:
        """Determine if error should trigger retry"""
        retry_indicators = [
            'timeout', 'connection', 'temporary', 'rate limit',
            'server error', '5xx', 'unavailable'
        ]
        return any(indicator in error_message.lower() for indicator in retry_indicators)
    
    async def wait_before_retry(self, attempt: int):
        """Wait with exponential backoff"""
        delay = min(
            self.retry_config['base_delay'] * (self.retry_config['exponential_base'] ** attempt),
            self.retry_config['max_delay']
        )
        await asyncio.sleep(delay)
```

#### Day 9: Rate Limiting Management
```python
# File: src/bridges/rate_limiter.py
class BridgeRateLimiter:
    """Manage rate limits across bridge APIs"""
    
    def __init__(self):
        self.rate_limits = {
            'synapse': {'requests_per_minute': 60, 'burst_limit': 10},
            'across': {'requests_per_minute': 100, 'burst_limit': 20},
            'hop': {'requests_per_minute': 30, 'burst_limit': 5},
            'stargate': {'requests_per_minute': 50, 'burst_limit': 10},
            'cbridge': {'requests_per_minute': 40, 'burst_limit': 8}
        }
        self.request_history = {}
        
    async def acquire_permit(self, bridge_name: str) -> bool:
        """Acquire permission to make API request"""
        now = datetime.now()
        
        # Clean old requests
        self.cleanup_old_requests(bridge_name, now)
        
        # Check rate limits
        if self.can_make_request(bridge_name, now):
            self.record_request(bridge_name, now)
            return True
        else:
            # Wait until we can make request
            wait_time = self.calculate_wait_time(bridge_name, now)
            await asyncio.sleep(wait_time)
            return await self.acquire_permit(bridge_name)
    
    def can_make_request(self, bridge_name: str, now: datetime) -> bool:
        """Check if we can make request without violating rate limits"""
        history = self.request_history.get(bridge_name, [])
        
        # Check minute limit
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [req for req in history if req > minute_ago]
        
        return len(recent_requests) < self.rate_limits[bridge_name]['requests_per_minute']
```

#### Day 10: Bridge Availability Monitoring
```python
# File: src/bridges/availability_monitor.py
class BridgeAvailabilityMonitor:
    """Monitor bridge availability and health"""
    
    def __init__(self):
        self.bridge_status = {}
        self.health_check_interval = 300  # 5 minutes
        
    async def start_monitoring(self):
        """Start continuous bridge health monitoring"""
        while True:
            for bridge_name in self.bridge_apis.keys():
                try:
                    health = await self.check_bridge_health(bridge_name)
                    self.bridge_status[bridge_name] = {
                        'available': health['available'],
                        'response_time': health['response_time'],
                        'last_check': datetime.now(),
                        'consecutive_failures': 0 if health['available'] else 
                            self.bridge_status.get(bridge_name, {}).get('consecutive_failures', 0) + 1
                    }
                    
                    # Alert on bridge failures
                    if not health['available']:
                        logger.warning(f"🚨 Bridge {bridge_name} is unavailable")
                        
                except Exception as e:
                    logger.error(f"Health check failed for {bridge_name}: {e}")
                    
            await asyncio.sleep(self.health_check_interval)
    
    async def check_bridge_health(self, bridge_name: str) -> Dict:
        """Check if bridge is healthy and responsive"""
        start_time = time.time()
        
        try:
            # Make a small test quote
            test_quote = await self.get_test_quote(bridge_name)
            response_time = time.time() - start_time
            
            return {
                'available': test_quote.success,
                'response_time': response_time,
                'error': test_quote.error_message if not test_quote.success else None
            }
            
        except Exception as e:
            return {
                'available': False,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    def get_available_bridges(self, source_chain: str, target_chain: str) -> List[str]:
        """Get list of currently available bridges for route"""
        available = []
        
        for bridge_name, status in self.bridge_status.items():
            if status.get('available', False):
                # Check if bridge supports this route
                if self.bridge_supports_route(bridge_name, source_chain, target_chain):
                    available.append(bridge_name)
                    
        return available
```

### Phase 3: Integration and Optimization (Days 11-14)
**Goal: Integrate real APIs with existing system**

#### Day 11-12: Update Bridge Cost Monitor
```python
# File: src/bridges/bridge_cost_monitor.py (UPDATED)
class BridgeCostMonitor:
    """Updated with real API integration"""
    
    def __init__(self, config: Dict[str, Any]):
        # Initialize real API clients
        self.api_clients = {
            'synapse': SynapseAPI(config),
            'across': AcrossAPI(config),
            'hop': HopAPI(config),
            'stargate': StargateAPI(config),
            'cbridge': CelerAPI(config)
        }
        
        # Add error handling and rate limiting
        self.error_handler = BridgeErrorHandler()
        self.rate_limiter = BridgeRateLimiter()
        self.availability_monitor = BridgeAvailabilityMonitor()
        
    async def get_real_bridge_quotes(self, source_chain: str, target_chain: str, 
                                   token: str, amount_usd: float) -> List[BridgeQuote]:
        """Get real quotes from all available bridges - UPDATED"""
        logger.info(f"📊 Getting REAL quotes: {token} {source_chain}→{target_chain} ${amount_usd}")
        
        # Get available bridges for this route
        available_bridges = self.availability_monitor.get_available_bridges(source_chain, target_chain)
        
        if not available_bridges:
            logger.warning(f"No available bridges for {source_chain}→{target_chain}")
            return []
        
        # Execute quote requests with rate limiting
        quote_tasks = []
        for bridge_name in available_bridges:
            # Acquire rate limit permit
            await self.rate_limiter.acquire_permit(bridge_name)
            
            # Create quote task with error handling
            task = self.error_handler.execute_with_retry(
                self.api_clients[bridge_name].get_quote,
                source_chain, target_chain, token, amount_usd
            )
            quote_tasks.append((bridge_name, task))
        
        # Wait for all quotes
        valid_quotes = []
        for bridge_name, task in quote_tasks:
            try:
                quote = await task
                if quote.success:
                    valid_quotes.append(quote)
                    logger.info(f"   ✅ {bridge_name}: ${quote.fee_usd:.2f} ({quote.fee_percentage:.2f}%)")
                else:
                    logger.warning(f"   ❌ {bridge_name}: {quote.error_message}")
                    
            except Exception as e:
                logger.error(f"   ❌ {bridge_name}: Unexpected error: {e}")
        
        # Sort by total cost
        valid_quotes.sort(key=lambda x: x.total_cost_usd)
        return valid_quotes
```

#### Day 13-14: Performance Optimization
```python
# File: src/bridges/quote_cache.py
class BridgeQuoteCache:
    """Cache bridge quotes to reduce API calls"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 60  # 1 minute cache
        
    def get_cache_key(self, source_chain: str, target_chain: str, 
                     token: str, amount_usd: float) -> str:
        """Generate cache key for quote"""
        # Round amount to nearest $10 for better cache hits
        rounded_amount = round(amount_usd / 10) * 10
        return f"{source_chain}_{target_chain}_{token}_{rounded_amount}"
    
    async def get_cached_quotes(self, source_chain: str, target_chain: str,
                              token: str, amount_usd: float) -> Optional[List[BridgeQuote]]:
        """Get cached quotes if available and fresh"""
        cache_key = self.get_cache_key(source_chain, target_chain, token, amount_usd)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            age = (datetime.now() - cached_data['timestamp']).total_seconds()
            
            if age < self.cache_ttl:
                logger.debug(f"Using cached bridge quotes (age: {age:.1f}s)")
                return cached_data['quotes']
            else:
                # Cache expired
                del self.cache[cache_key]
        
        return None
    
    def cache_quotes(self, source_chain: str, target_chain: str,
                    token: str, amount_usd: float, quotes: List[BridgeQuote]):
        """Cache quotes for future use"""
        cache_key = self.get_cache_key(source_chain, target_chain, token, amount_usd)
        
        self.cache[cache_key] = {
            'quotes': quotes,
            'timestamp': datetime.now()
        }
        
        # Cleanup old cache entries
        self.cleanup_expired_cache()
```

## Testing Strategy

### Unit Tests
```python
# File: tests/test_bridge_apis.py
class TestBridgeAPIs:
    """Test real bridge API integrations"""
    
    async def test_synapse_api(self):
        """Test Synapse API integration"""
        api = SynapseAPI({})
        quote = await api.get_quote('ethereum', 'arbitrum', 'ETH', 100)
        assert quote.success
        assert quote.fee_usd > 0
        assert quote.fee_percentage > 0
        
    async def test_error_handling(self):
        """Test API error handling"""
        # Test with invalid parameters
        # Test with network timeouts
        # Test with rate limiting
        
    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make rapid requests and verify rate limiting works
```

### Integration Tests
```python
# File: tests/test_bridge_integration.py
class TestBridgeIntegration:
    """Test bridge system integration"""
    
    async def test_real_quote_comparison(self):
        """Compare real quotes with previous simulated quotes"""
        # Verify real quotes are reasonable
        # Check that fee percentages are in expected ranges
        
    async def test_bridge_selection(self):
        """Test bridge selection logic"""
        # Verify cheapest bridge is selected
        # Test fallback when bridges are unavailable
```

## Success Criteria

### Phase 1 Success:
- ✅ All 5 bridge APIs return real quotes
- ✅ Quote parsing works correctly
- ✅ Error handling prevents crashes
- ✅ API responses match expected format

### Phase 2 Success:
- ✅ Retry logic handles temporary failures
- ✅ Rate limiting prevents API abuse
- ✅ Bridge availability monitoring works
- ✅ System gracefully handles bridge outages

### Phase 3 Success:
- ✅ Real quotes integrate with existing system
- ✅ Performance is acceptable (quotes in <5 seconds)
- ✅ Cache reduces redundant API calls
- ✅ Bridge selection optimizes for cost

## Risk Mitigation

### API Reliability
1. **Multiple bridge options** - If one fails, others available
2. **Retry logic** - Handle temporary failures
3. **Fallback mechanisms** - Graceful degradation
4. **Monitoring** - Alert on bridge failures

### Cost Accuracy
1. **Real-time quotes** - No more simulated data
2. **Quote validation** - Sanity checks on returned data
3. **Historical tracking** - Monitor quote accuracy over time
4. **Cross-validation** - Compare quotes across bridges

## Dependencies

### External APIs:
- Synapse Protocol API
- Across Protocol API  
- Hop Protocol API
- Stargate Finance API
- Celer cBridge API

### Internal Dependencies:
- Execution engine (for bridge transaction execution)
- Price feeds (for amount conversions)
- Risk management (for bridge selection criteria)

This bridge system implementation will provide accurate, real-time bridge cost data essential for profitable cross-chain arbitrage execution.
