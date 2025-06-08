#!/usr/bin/env python3
"""
🚀 LIVE OPPORTUNITY SCANNER
Real-time arbitrage opportunity detection with your enhanced system
"""

import os
import sys
import asyncio
import time
from pathlib import Path
from web3 import Web3
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

class LiveOpportunityScanner:
    """Live scanner for arbitrage opportunities with enhanced DEX coverage."""
    
    def __init__(self):
        self.alchemy_key = os.getenv('ALCHEMY_API_KEY')
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        
        # Multi-chain connections
        self.connections = {
            'arbitrum': Web3(Web3.HTTPProvider(f'https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_key}')),
            'base': Web3(Web3.HTTPProvider(f'https://base-mainnet.g.alchemy.com/v2/{self.alchemy_key}')),
            'optimism': Web3(Web3.HTTPProvider(f'https://opt-mainnet.g.alchemy.com/v2/{self.alchemy_key}'))
        }

        # Add POA middleware for chains that need it
        poa_chains = ['base']  # Base uses POA consensus
        for chain in poa_chains:
            if chain in self.connections:
                try:
                    from web3.middleware import geth_poa_middleware
                    self.connections[chain].middleware_onion.inject(geth_poa_middleware, layer=0)
                except ImportError:
                    pass
        
        # Enhanced DEX configuration (your 7 DEXes)
        self.dex_configs = {
            'arbitrum': {
                'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                'camelot': '0xc873fEcbd354f5A56E00E710B90EF4201db2448d',
                'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'traderjoe': '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45'
            },
            'base': {
                'aerodrome': '0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43',
                'baseswap': '0x327Df1E6de05895d2ab08513aaDD9313Fe505d86'
            },
            'optimism': {
                'velodrome': '0xa132DAB612dB5cB9fC9Ac426A0Cc215A3423F9c9'
            }
        }
        
        # Token addresses by chain
        self.tokens = {
            'arbitrum': {
                'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
                'USDC.e': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
                'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9'
            },
            'base': {
                'WETH': '0x4200000000000000000000000000000000000006',
                'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
            },
            'optimism': {
                'WETH': '0x4200000000000000000000000000000000000006',
                'USDC': '0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85'
            }
        }
        
        # Your actual wallet balances (with USDC.e fix)
        self.wallet_balances = {
            'ETH': 0.007294,      # $21.88
            'WETH': 0.003210,     # $9.63
            'USDC': 58.93,        # $58.93
            'USDC.e': 314.38,     # $314.38 ← THE BIG ONE!
            'USDT': 2.62,         # $2.62
        }
        
        # Calculate available capital (with USDC.e fix)
        self.available_capital = (
            self.wallet_balances['USDC'] + 
            self.wallet_balances['USDC.e'] + 
            self.wallet_balances['USDT']
        )  # $375.93 total!
        
        # Router ABI (minimal)
        self.router_abi = [
            {"constant": True, "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ], "name": "getAmountsOut", "outputs": [{"name": "amounts", "type": "uint256[]"}], "type": "function"}
        ]
        
        self.scan_count = 0
        self.opportunities_found = 0
        self.viable_opportunities = 0
        
        print("🚀 LIVE OPPORTUNITY SCANNER INITIALIZED")
        print(f"💰 Available Capital: ${self.available_capital:.2f} (USDC.e fix applied!)")
        print(f"🌐 Chains: {len(self.connections)}")
        print(f"🔧 DEXes: {sum(len(dexes) for dexes in self.dex_configs.values())}")
    
    async def get_price_quote(self, chain, dex_name, token_in, token_out, amount_usd):
        """Get price quote from a specific DEX."""
        try:
            w3 = self.connections[chain]
            router_address = self.dex_configs[chain][dex_name]
            router = w3.eth.contract(address=router_address, abi=self.router_abi)
            
            token_in_addr = self.tokens[chain][token_in]
            token_out_addr = self.tokens[chain][token_out]
            
            # Convert USD to token amount
            if token_in in ['USDC', 'USDC.e', 'USDT']:
                amount_wei = int(amount_usd * 10**6)  # 6 decimals
            else:
                amount_wei = int(amount_usd * 10**18 / 3000)  # Assume $3000 ETH
            
            path = [token_in_addr, token_out_addr]
            amounts = router.functions.getAmountsOut(amount_wei, path).call()
            
            # Convert output to USD
            if token_out in ['USDC', 'USDC.e', 'USDT']:
                amount_out_usd = amounts[1] / 10**6
            else:
                amount_out_usd = amounts[1] / 10**18 * 3000
            
            return amount_out_usd
            
        except Exception as e:
            # Silent fail for cleaner output
            return None
    
    async def scan_arbitrage_opportunity(self, chain1, dex1, chain2, dex2, token_pair):
        """Scan for arbitrage opportunity between two DEXes."""
        try:
            token_in, token_out = token_pair
            test_amount = self.available_capital * 0.5  # 50% of available capital
            
            # Get quotes from both DEXes
            quote1 = await self.get_price_quote(chain1, dex1, token_in, token_out, test_amount)
            quote2 = await self.get_price_quote(chain2, dex2, token_out, token_in, test_amount)
            
            if quote1 and quote2:
                # Calculate round-trip profit
                profit = quote2 - test_amount
                profit_pct = (profit / test_amount) * 100
                
                if profit > 0.05:  # $0.05 minimum threshold (more aggressive)
                    return {
                        'chain1': chain1,
                        'dex1': dex1,
                        'chain2': chain2,
                        'dex2': dex2,
                        'token_pair': token_pair,
                        'trade_amount': test_amount,
                        'profit': profit,
                        'profit_pct': profit_pct,
                        'viable': True
                    }
            
            return None
            
        except Exception as e:
            return None
    
    async def scan_all_opportunities(self):
        """Scan all possible arbitrage opportunities."""
        opportunities = []
        
        # Expanded trading pairs for more opportunities
        trading_pairs = [
            ('USDC', 'WETH'),
            ('USDT', 'WETH'),
            ('USDC.e', 'WETH') if 'USDC.e' in self.tokens.get('arbitrum', {}) else ('USDC', 'WETH'),
            ('USDC', 'USDT'),
            ('USDC', 'ARB'),
            ('WETH', 'ARB'),
            ('USDT', 'ARB'),
            ('USDC', 'OP'),
            ('WETH', 'OP')
        ]
        
        # Scan same-chain opportunities
        for chain, dexes in self.dex_configs.items():
            dex_list = list(dexes.keys())
            for i, dex1 in enumerate(dex_list):
                for j, dex2 in enumerate(dex_list):
                    if i < j:  # Avoid duplicates
                        for pair in trading_pairs:
                            if all(token in self.tokens[chain] for token in pair):
                                opp = await self.scan_arbitrage_opportunity(chain, dex1, chain, dex2, pair)
                                if opp:
                                    opportunities.append(opp)
        
        # Scan cross-chain opportunities (simplified)
        chains = list(self.dex_configs.keys())
        for i, chain1 in enumerate(chains):
            for j, chain2 in enumerate(chains):
                if i < j:  # Avoid duplicates
                    for dex1 in self.dex_configs[chain1]:
                        for dex2 in self.dex_configs[chain2]:
                            for pair in trading_pairs:
                                if (all(token in self.tokens[chain1] for token in pair) and
                                    all(token in self.tokens[chain2] for token in pair)):
                                    opp = await self.scan_arbitrage_opportunity(chain1, dex1, chain2, dex2, pair)
                                    if opp:
                                        opportunities.append(opp)
        
        return opportunities
    
    async def run_live_scan(self):
        """Run continuous live scanning."""
        print("\n🔍 STARTING LIVE ARBITRAGE SCANNING")
        print("=" * 50)
        print("Scanning 7 DEXes across 3 chains for opportunities...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.scan_count += 1
                scan_start = time.time()
                
                print(f"🔍 Scan #{self.scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Scan for opportunities
                opportunities = await self.scan_all_opportunities()
                
                scan_time = time.time() - scan_start
                
                if opportunities:
                    self.opportunities_found += len(opportunities)
                    viable_count = len([opp for opp in opportunities if opp['viable']])
                    self.viable_opportunities += viable_count
                    
                    print(f"🎉 FOUND {len(opportunities)} OPPORTUNITIES!")
                    
                    for i, opp in enumerate(opportunities, 1):
                        chain_info = f"{opp['chain1']}" if opp['chain1'] == opp['chain2'] else f"{opp['chain1']}→{opp['chain2']}"
                        print(f"   #{i}: {opp['dex1']} → {opp['dex2']} ({chain_info})")
                        print(f"       Pair: {opp['token_pair'][0]} → {opp['token_pair'][1]}")
                        print(f"       Trade: ${opp['trade_amount']:.2f}")
                        print(f"       Profit: ${opp['profit']:.4f} ({opp['profit_pct']:.3f}%)")
                        print(f"       Status: {'✅ VIABLE' if opp['viable'] else '❌ FILTERED'}")
                else:
                    print("📊 No opportunities found this scan")
                
                print(f"⏱️  Scan time: {scan_time:.2f}s")
                print(f"📊 Total: {self.opportunities_found} found, {self.viable_opportunities} viable")
                print("-" * 50)
                
                # Wait before next scan
                await asyncio.sleep(10)  # 10 second intervals
                
        except KeyboardInterrupt:
            print(f"\n🛑 SCANNING STOPPED")
            print(f"📊 FINAL STATS:")
            print(f"   Scans completed: {self.scan_count}")
            print(f"   Opportunities found: {self.opportunities_found}")
            print(f"   Viable opportunities: {self.viable_opportunities}")
            print(f"   Success rate: {(self.viable_opportunities/max(self.opportunities_found,1))*100:.1f}%")

async def main():
    """Main function."""
    scanner = LiveOpportunityScanner()
    await scanner.run_live_scan()

if __name__ == "__main__":
    asyncio.run(main())
