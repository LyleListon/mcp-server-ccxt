"""
REAL TRANSACTION PROFIT CALCULATOR
Parses actual transaction logs to calculate REAL profits - NO MORE FAKE ESTIMATES!
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal, getcontext
from web3 import Web3
import json

# Set high precision for calculations
getcontext().prec = 50

logger = logging.getLogger(__name__)

class TransactionProfitCalculator:
    """Calculate REAL profits from actual transaction logs."""
    
    def __init__(self):
        # ERC20 Transfer event signature
        self.transfer_topic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
        
        # Common token decimals
        self.token_decimals = {
            'WETH': 18,
            'ETH': 18,
            'USDC': 6,
            'USDC.e': 6,
            'USDbC': 6,
            'USDT': 6,
            'DAI': 18
        }
        
        # Token addresses by chain
        self.token_addresses = {
            'arbitrum': {
                '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1': 'WETH',
                '0xaf88d065e77c8cC2239327C5EDb3A432268e5831': 'USDC',
                '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8': 'USDC.e',
                '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9': 'USDT'
            },
            'base': {
                '0x4200000000000000000000000000000000000006': 'WETH',
                '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913': 'USDC',
                '0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA': 'USDbC'
            },
            'optimism': {
                '0x4200000000000000000000000000000000000006': 'WETH',
                '0x7F5c764cBc14f9669B88837ca1490cCa17c31607': 'USDC',
                '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58': 'USDT'
            }
        }
        
        # Current token prices (should be fetched from real API)
        self.token_prices_usd = {
            'ETH': 3800.0,
            'WETH': 3800.0,
            'USDC': 1.0,
            'USDC.e': 1.0,
            'USDbC': 1.0,
            'USDT': 1.0,
            'DAI': 1.0
        }

    async def calculate_real_profit(self, web3: Web3, tx_hash: str, wallet_address: str, 
                                  chain: str = 'arbitrum') -> Dict[str, Any]:
        """Calculate REAL profit from actual transaction logs."""
        try:
            logger.info(f"🔍 CALCULATING REAL PROFIT FROM TRANSACTION: {tx_hash}")
            
            # Get transaction receipt
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if not receipt:
                return {'success': False, 'error': 'Transaction receipt not found'}
            
            # Get transaction details
            tx = web3.eth.get_transaction(tx_hash)
            if not tx:
                return {'success': False, 'error': 'Transaction not found'}
            
            # Calculate gas costs
            gas_used = receipt.gasUsed
            gas_price = tx.gasPrice
            gas_cost_wei = gas_used * gas_price
            gas_cost_eth = web3.from_wei(gas_cost_wei, 'ether')
            gas_cost_usd = float(gas_cost_eth) * self.token_prices_usd['ETH']
            
            logger.info(f"   ⛽ REAL GAS COST: {gas_cost_eth:.6f} ETH (${gas_cost_usd:.2f})")
            
            # Parse token transfers
            token_flows = await self._parse_token_transfers(web3, receipt, wallet_address, chain)
            
            # Calculate net profit
            profit_analysis = await self._calculate_net_profit(token_flows, gas_cost_usd)
            
            # Combine results
            result = {
                'success': True,
                'transaction_hash': tx_hash,
                'gas_cost_eth': float(gas_cost_eth),
                'gas_cost_usd': gas_cost_usd,
                'token_flows': token_flows,
                'profit_analysis': profit_analysis,
                'net_profit_usd': profit_analysis['net_profit_usd'],
                'calculation_method': 'real_transaction_logs'
            }
            
            logger.info(f"💰 REAL PROFIT CALCULATED: ${profit_analysis['net_profit_usd']:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Real profit calculation error: {e}")
            return {'success': False, 'error': str(e)}

    async def _parse_token_transfers(self, web3: Web3, receipt, wallet_address: str, 
                                   chain: str) -> Dict[str, Dict]:
        """Parse ERC20 transfer events to track token flows."""
        try:
            logger.info(f"   🔍 Parsing token transfers for wallet: {wallet_address}")
            
            token_flows = {}
            wallet_address = wallet_address.lower()
            
            # Parse all logs for Transfer events
            for log in receipt.logs:
                try:
                    # Check if this is a Transfer event
                    if len(log.topics) >= 3 and log.topics[0].hex() == self.transfer_topic:
                        # Decode transfer event
                        from_address = '0x' + log.topics[1].hex()[26:]  # Remove padding
                        to_address = '0x' + log.topics[2].hex()[26:]    # Remove padding
                        amount_hex = log.data.hex()
                        amount = int(amount_hex, 16) if amount_hex else 0
                        
                        token_address = log.address.lower()
                        
                        # Get token symbol
                        token_symbol = self.token_addresses.get(chain, {}).get(token_address, 'UNKNOWN')
                        if token_symbol == 'UNKNOWN':
                            continue  # Skip unknown tokens
                        
                        # Convert amount to human readable
                        decimals = self.token_decimals.get(token_symbol, 18)
                        amount_tokens = amount / (10 ** decimals)
                        
                        # Calculate USD value
                        token_price = self.token_prices_usd.get(token_symbol, 0.0)
                        amount_usd = amount_tokens * token_price
                        
                        # Track flows for our wallet
                        if from_address.lower() == wallet_address:
                            # Outgoing transfer (we sent tokens)
                            if token_symbol not in token_flows:
                                token_flows[token_symbol] = {'in': 0, 'out': 0, 'net': 0}
                            token_flows[token_symbol]['out'] += amount_tokens
                            logger.info(f"      📤 OUT: {amount_tokens:.6f} {token_symbol} (${amount_usd:.2f})")
                            
                        elif to_address.lower() == wallet_address:
                            # Incoming transfer (we received tokens)
                            if token_symbol not in token_flows:
                                token_flows[token_symbol] = {'in': 0, 'out': 0, 'net': 0}
                            token_flows[token_symbol]['in'] += amount_tokens
                            logger.info(f"      📥 IN:  {amount_tokens:.6f} {token_symbol} (${amount_usd:.2f})")
                            
                except Exception as e:
                    logger.warning(f"⚠️  Error parsing log: {e}")
                    continue
            
            # Calculate net flows
            for token_symbol in token_flows:
                flow = token_flows[token_symbol]
                flow['net'] = flow['in'] - flow['out']
                
                token_price = self.token_prices_usd.get(token_symbol, 0.0)
                flow['net_usd'] = flow['net'] * token_price
                
                logger.info(f"   💰 NET {token_symbol}: {flow['net']:+.6f} (${flow['net_usd']:+.2f})")
            
            return token_flows
            
        except Exception as e:
            logger.error(f"❌ Token transfer parsing error: {e}")
            return {}

    async def _calculate_net_profit(self, token_flows: Dict, gas_cost_usd: float) -> Dict[str, Any]:
        """Calculate net profit from token flows."""
        try:
            logger.info(f"   🧮 CALCULATING NET PROFIT...")
            
            total_token_profit_usd = 0.0
            profit_breakdown = {}
            
            # Sum up all token gains/losses
            for token_symbol, flow in token_flows.items():
                net_usd = flow.get('net_usd', 0.0)
                total_token_profit_usd += net_usd
                profit_breakdown[token_symbol] = net_usd
                
                if net_usd != 0:
                    logger.info(f"      💰 {token_symbol}: ${net_usd:+.2f}")
            
            # Calculate final net profit (token gains - gas costs)
            net_profit_usd = total_token_profit_usd - gas_cost_usd
            
            logger.info(f"   📊 PROFIT BREAKDOWN:")
            logger.info(f"      💰 Token gains: ${total_token_profit_usd:+.2f}")
            logger.info(f"      ⛽ Gas costs: ${gas_cost_usd:.2f}")
            logger.info(f"      🎯 NET PROFIT: ${net_profit_usd:+.2f}")
            
            return {
                'token_profit_usd': total_token_profit_usd,
                'gas_cost_usd': gas_cost_usd,
                'net_profit_usd': net_profit_usd,
                'profit_breakdown': profit_breakdown,
                'is_profitable': net_profit_usd > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Net profit calculation error: {e}")
            return {
                'token_profit_usd': 0.0,
                'gas_cost_usd': gas_cost_usd,
                'net_profit_usd': -gas_cost_usd,
                'profit_breakdown': {},
                'is_profitable': False,
                'error': str(e)
            }

    def update_token_prices(self, prices: Dict[str, float]):
        """Update token prices for accurate USD calculations."""
        self.token_prices_usd.update(prices)
        logger.info(f"💰 Updated token prices: {prices}")

    async def get_wallet_balance_change(self, web3: Web3, wallet_address: str, 
                                      before_block: int, after_block: int) -> Dict[str, float]:
        """Get wallet balance changes between blocks (alternative method)."""
        try:
            logger.info(f"📊 Checking balance changes from block {before_block} to {after_block}")
            
            # Get ETH balance change
            balance_before = web3.eth.get_balance(wallet_address, before_block)
            balance_after = web3.eth.get_balance(wallet_address, after_block)
            
            eth_change = web3.from_wei(balance_after - balance_before, 'ether')
            eth_change_usd = float(eth_change) * self.token_prices_usd['ETH']
            
            logger.info(f"   💰 ETH balance change: {eth_change:+.6f} ETH (${eth_change_usd:+.2f})")
            
            return {
                'eth_change': float(eth_change),
                'eth_change_usd': eth_change_usd
            }
            
        except Exception as e:
            logger.error(f"❌ Balance change calculation error: {e}")
            return {'eth_change': 0.0, 'eth_change_usd': 0.0}
