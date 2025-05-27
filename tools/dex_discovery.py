#!/usr/bin/env python3
"""
DEX Discovery Tool
Finds smaller DEXs on Ethereum with working APIs and good arbitrage potential.
"""

import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DEXDiscovery:
    """Discover smaller DEXs with arbitrage potential."""

    def __init__(self):
        """Initialize DEX discovery."""
        self.session = None

        # Known smaller Ethereum DEXs to test
        self.potential_dexs = {
            'curve': {
                'name': 'Curve Finance',
                'type': 'stableswap',
                'api_url': 'https://api.curve.fi/api/getPools/ethereum/main',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/curvefi/curve',
                'focus': 'stablecoins',
                'expected_pairs': 20
            },
            'balancer': {
                'name': 'Balancer',
                'type': 'weighted_pools',
                'api_url': 'https://api.balancer.fi/pools',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/balancer-labs/balancer-v2',
                'focus': 'multi-token pools',
                'expected_pairs': 50
            },
            'bancor': {
                'name': 'Bancor',
                'type': 'single_sided',
                'api_url': 'https://api.bancor.network/0.1/currencies',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/bancorprotocol/bancor3',
                'focus': 'single-sided liquidity',
                'expected_pairs': 30
            },
            'kyber': {
                'name': 'KyberSwap',
                'type': 'concentrated_liquidity',
                'api_url': 'https://aggregator-api.kyberswap.com/ethereum/api/v1/routes',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/kybernetwork/kyberswap-exchange-ethereum',
                'focus': 'concentrated liquidity',
                'expected_pairs': 40
            },
            'shibaswap': {
                'name': 'ShibaSwap',
                'type': 'uniswap_v2_fork',
                'api_url': None,  # No direct API
                'subgraph': 'https://api.thegraph.com/subgraphs/name/shibaswap/exchange',
                'focus': 'meme tokens',
                'expected_pairs': 15
            },
            'dodo': {
                'name': 'DODO',
                'type': 'pmm',
                'api_url': 'https://api.dodoex.io/route-service/developer/get_dodo_route',
                'subgraph': 'https://api.thegraph.com/subgraphs/name/dodoex/dodoex-v2',
                'focus': 'proactive market making',
                'expected_pairs': 25
            },
            'fraxswap': {
                'name': 'FraxSwap',
                'type': 'twamm',
                'api_url': None,
                'subgraph': 'https://api.thegraph.com/subgraphs/name/frax-finance/fraxswap',
                'focus': 'FRAX ecosystem',
                'expected_pairs': 10
            }
        }

    def discover_working_dexs(self) -> List[Dict[str, Any]]:
        """Discover which DEXs are working and have good arbitrage potential."""
        working_dexs = []

        logger.info("🔍 Starting DEX discovery...")

        for dex_id, dex_info in self.potential_dexs.items():
            logger.info(f"\n📊 Testing {dex_info['name']} ({dex_id})...")

            result = self._test_dex(dex_id, dex_info)
            if result['working']:
                working_dexs.append(result)
                logger.info(f"✅ {dex_info['name']}: {result['pairs_found']} pairs, {result['status']}")
            else:
                logger.warning(f"❌ {dex_info['name']}: {result['error']}")

        # Sort by arbitrage potential
        working_dexs.sort(key=lambda x: x['arbitrage_score'], reverse=True)

        logger.info(f"\n🎯 Discovery complete! Found {len(working_dexs)} working DEXs")
        return working_dexs

    def _test_dex(self, dex_id: str, dex_info: Dict[str, Any]) -> Dict[str, Any]:
        """Test if a DEX is working and has arbitrage potential."""
        result = {
            'dex_id': dex_id,
            'name': dex_info['name'],
            'type': dex_info['type'],
            'focus': dex_info['focus'],
            'working': False,
            'pairs_found': 0,
            'arbitrage_score': 0,
            'api_working': False,
            'subgraph_working': False,
            'error': None,
            'status': 'unknown'
        }

        try:
            # Test API if available
            if dex_info.get('api_url'):
                api_result = self._test_api(dex_info['api_url'], dex_id)
                result['api_working'] = api_result['working']
                if api_result['working']:
                    result['pairs_found'] += api_result.get('pairs', 0)

            # Test subgraph
            if dex_info.get('subgraph'):
                subgraph_result = self._test_subgraph(dex_info['subgraph'], dex_id)
                result['subgraph_working'] = subgraph_result['working']
                if subgraph_result['working']:
                    result['pairs_found'] += subgraph_result.get('pairs', 0)

            # Determine if DEX is working
            result['working'] = result['api_working'] or result['subgraph_working']

            if result['working']:
                result['arbitrage_score'] = self._calculate_arbitrage_score(result, dex_info)
                result['status'] = self._get_status(result)
            else:
                result['error'] = 'No working endpoints'

        except Exception as e:
            result['error'] = str(e)

        return result

    def _test_api(self, api_url: str, dex_id: str) -> Dict[str, Any]:
        """Test if DEX API is working."""
        try:
            if dex_id == 'curve':
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    pools = data.get('data', {}).get('poolData', [])
                    return {'working': True, 'pairs': len(pools)}

            elif dex_id == 'balancer':
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    pools = data.get('pools', [])
                    return {'working': True, 'pairs': len(pools)}

            elif dex_id == 'bancor':
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    currencies = data.get('data', [])
                    return {'working': True, 'pairs': len(currencies)}

            elif dex_id == 'kyber':
                # Test with a simple route query
                params = {
                    'tokenIn': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC
                    'tokenOut': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
                    'amountIn': '1000000'  # 1 USDC
                }
                response = requests.get(api_url, params=params, timeout=10)
                if response.status_code == 200:
                    return {'working': True, 'pairs': 40}  # Estimate

            elif dex_id == 'dodo':
                # Test DODO route API
                params = {
                    'fromTokenAddress': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  # USDC
                    'toTokenAddress': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
                    'fromAmount': '1000000',
                    'slippage': '1',
                    'userAddr': '0x0000000000000000000000000000000000000000'
                }
                response = requests.get(api_url, params=params, timeout=10)
                if response.status_code == 200:
                    return {'working': True, 'pairs': 25}  # Estimate

            return {'working': False, 'error': 'API test failed'}

        except Exception as e:
            return {'working': False, 'error': str(e)}

    def _test_subgraph(self, subgraph_url: str, dex_id: str) -> Dict[str, Any]:
        """Test if DEX subgraph is working."""
        try:
            # Generic query for most DEXs
            query = """
            {
                pairs(first: 5) {
                    id
                    token0 { symbol }
                    token1 { symbol }
                }
            }
            """

            # Balancer uses pools instead of pairs
            if dex_id == 'balancer':
                query = """
                {
                    pools(first: 5) {
                        id
                        tokens { symbol }
                    }
                }
                """

            response = requests.post(
                subgraph_url,
                json={'query': query},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    pairs_key = 'pools' if dex_id == 'balancer' else 'pairs'
                    pairs = data['data'].get(pairs_key, [])
                    return {'working': True, 'pairs': len(pairs) * 10}  # Estimate total

            return {'working': False, 'error': 'Subgraph query failed'}

        except Exception as e:
            return {'working': False, 'error': str(e)}

    def _calculate_arbitrage_score(self, result: Dict[str, Any], dex_info: Dict[str, Any]) -> float:
        """Calculate arbitrage potential score."""
        score = 0.0

        # Base score from number of pairs
        pairs_score = min(result['pairs_found'] / 50, 1.0) * 30
        score += pairs_score

        # Bonus for DEX type (some are better for arbitrage)
        type_bonuses = {
            'stableswap': 25,      # Curve - great for stablecoin arb
            'pmm': 20,             # DODO - proactive market making
            'concentrated_liquidity': 15,  # Kyber - concentrated liquidity
            'weighted_pools': 10,   # Balancer - multi-token pools
            'uniswap_v2_fork': 5,  # ShibaSwap - basic AMM
            'single_sided': 5,     # Bancor - single-sided
            'twamm': 5             # FraxSwap - time-weighted
        }
        score += type_bonuses.get(dex_info['type'], 0)

        # Bonus for having both API and subgraph
        if result['api_working'] and result['subgraph_working']:
            score += 15
        elif result['api_working'] or result['subgraph_working']:
            score += 5

        # Focus area bonuses
        focus_bonuses = {
            'stablecoins': 20,     # High arbitrage potential
            'meme tokens': 15,     # Volatile, good for arb
            'concentrated liquidity': 10,
            'FRAX ecosystem': 5
        }
        score += focus_bonuses.get(dex_info['focus'], 0)

        return min(score, 100)  # Cap at 100

    def _get_status(self, result: Dict[str, Any]) -> str:
        """Get status description."""
        if result['arbitrage_score'] >= 70:
            return 'EXCELLENT - High arbitrage potential'
        elif result['arbitrage_score'] >= 50:
            return 'GOOD - Moderate arbitrage potential'
        elif result['arbitrage_score'] >= 30:
            return 'FAIR - Some arbitrage potential'
        else:
            return 'LOW - Limited arbitrage potential'


def main():
    """Run DEX discovery."""
    discovery = DEXDiscovery()
    working_dexs = discovery.discover_working_dexs()

    print("\n" + "="*80)
    print("🎯 DEX DISCOVERY RESULTS")
    print("="*80)

    if working_dexs:
        for i, dex in enumerate(working_dexs, 1):
            print(f"\n{i}. {dex['name']} ({dex['dex_id']})")
            print(f"   Type: {dex['type']}")
            print(f"   Focus: {dex['focus']}")
            print(f"   Pairs: {dex['pairs_found']}")
            print(f"   Score: {dex['arbitrage_score']:.1f}/100")
            print(f"   Status: {dex['status']}")
            print(f"   API: {'✅' if dex['api_working'] else '❌'}")
            print(f"   Subgraph: {'✅' if dex['subgraph_working'] else '❌'}")

        print(f"\n🏆 Top recommendation: {working_dexs[0]['name']} (Score: {working_dexs[0]['arbitrage_score']:.1f})")

        # Save results
        with open('dex_discovery_results.json', 'w') as f:
            json.dump(working_dexs, f, indent=2)
        print(f"\n💾 Results saved to dex_discovery_results.json")
    else:
        print("\n❌ No working DEXs found")


if __name__ == "__main__":
    main()
