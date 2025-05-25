"""
Mock aiohttp module for testing DEX integration without external dependencies.
This allows us to test the arbitrage logic while we resolve dependency issues.
"""

import asyncio
import json
from typing import Dict, Any, Optional


class MockResponse:
    """Mock HTTP response."""

    def __init__(self, status: int, data: Dict[str, Any]):
        self.status = status
        self._data = data

    async def json(self) -> Dict[str, Any]:
        """Return JSON data."""
        return self._data

    async def text(self) -> str:
        """Return text data."""
        return json.dumps(self._data)


class MockContextManager:
    """Mock async context manager for HTTP requests."""

    def __init__(self, coro):
        self.coro = coro

    async def __aenter__(self):
        return await self.coro

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockSession:
    """Mock HTTP session."""

    def __init__(self):
        self.closed = False

    def post(self, url: str, **kwargs):
        """Mock POST request with async context manager support."""
        return MockContextManager(self._post_impl(url, **kwargs))

    def get(self, url: str, **kwargs):
        """Mock GET request with async context manager support."""
        return MockContextManager(self._get_impl(url, **kwargs))

    async def _post_impl(self, url: str, **kwargs) -> MockResponse:
        """Mock POST implementation."""
        # Simulate different responses based on URL
        if 'uniswap' in url.lower():
            return await self._mock_uniswap_response(kwargs)
        elif 'sushiswap' in url.lower():
            return await self._mock_sushiswap_response(kwargs)
        else:
            return MockResponse(200, {"data": {}})

    async def _get_impl(self, url: str, **kwargs) -> MockResponse:
        """Mock GET implementation."""
        return MockResponse(200, {"data": {}})

    async def _mock_uniswap_response(self, kwargs: Dict[str, Any]) -> MockResponse:
        """Mock Uniswap subgraph response."""
        query = kwargs.get('json', {}).get('query', '')

        if 'pools' in query:
            # Mock pool data
            mock_pools = [
                {
                    'id': '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640',
                    'token0': {
                        'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
                        'symbol': 'USDC',
                        'name': 'USD Coin',
                        'decimals': '6'
                    },
                    'token1': {
                        'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                        'symbol': 'WETH',
                        'name': 'Wrapped Ether',
                        'decimals': '18'
                    },
                    'feeTier': '500',
                    'liquidity': '1234567890',
                    'sqrtPrice': '1234567890123456789012345',
                    'tick': '123456',
                    'totalValueLockedUSD': '50000000',
                    'volumeUSD': '10000000'
                },
                {
                    'id': '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',
                    'token0': {
                        'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
                        'symbol': 'USDC',
                        'name': 'USD Coin',
                        'decimals': '6'
                    },
                    'token1': {
                        'id': '0xdac17f958d2ee523a2206206994597c13d831ec7',
                        'symbol': 'USDT',
                        'name': 'Tether USD',
                        'decimals': '6'
                    },
                    'feeTier': '100',
                    'liquidity': '987654321',
                    'sqrtPrice': '1000000000000000000000000',
                    'tick': '0',
                    'totalValueLockedUSD': '25000000',
                    'volumeUSD': '5000000'
                }
            ]

            return MockResponse(200, {"data": {"pools": mock_pools}})

        return MockResponse(200, {"data": {}})

    async def _mock_sushiswap_response(self, kwargs: Dict[str, Any]) -> MockResponse:
        """Mock SushiSwap subgraph response."""
        query = kwargs.get('json', {}).get('query', '')

        if 'pairs' in query:
            # Mock pair data with realistic arbitrage opportunities
            mock_pairs = [
                {
                    'id': '0x397ff1542f962076d0bfe58ea045ffa2d347aca0',
                    'token0': {
                        'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
                        'symbol': 'USDC',
                        'name': 'USD Coin',
                        'decimals': '6'
                    },
                    'token1': {
                        'id': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',
                        'symbol': 'WETH',
                        'name': 'Wrapped Ether',
                        'decimals': '18'
                    },
                    'reserve0': '2000000000000',  # 2M USDC
                    'reserve1': '1000000000000000000000',  # 1000 WETH
                    'reserveUSD': '4000000',
                    'volumeUSD': '500000',
                    'token0Price': '0.0005',  # 1 USDC = 0.0005 WETH (WETH = $2000)
                    'token1Price': '2000'     # 1 WETH = 2000 USDC
                },
                {
                    'id': '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8',
                    'token0': {
                        'id': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
                        'symbol': 'USDC',
                        'name': 'USD Coin',
                        'decimals': '6'
                    },
                    'token1': {
                        'id': '0xdac17f958d2ee523a2206206994597c13d831ec7',
                        'symbol': 'USDT',
                        'name': 'Tether USD',
                        'decimals': '6'
                    },
                    'reserve0': '5000000000000',  # 5M USDC
                    'reserve1': '5005000000000',  # 5.005M USDT (slight price difference!)
                    'reserveUSD': '10000000',
                    'volumeUSD': '2000000',
                    'token0Price': '1.001',  # 1 USDC = 1.001 USDT (0.1% arbitrage opportunity!)
                    'token1Price': '0.999'   # 1 USDT = 0.999 USDC
                }
            ]

            return MockResponse(200, {"data": {"pairs": mock_pairs}})

        return MockResponse(200, {"data": {}})

    async def close(self):
        """Close session."""
        self.closed = True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def ClientSession(*args, **kwargs) -> MockSession:
    """Create mock client session."""
    return MockSession()


# Mock the aiohttp module structure
class MockAiohttp:
    ClientSession = ClientSession


# Export the mock
import sys
sys.modules['aiohttp'] = MockAiohttp()
