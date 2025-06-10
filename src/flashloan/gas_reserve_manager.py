#!/usr/bin/env python3
"""
GAS RESERVE MANAGER
Maintains optimal gas reserves across all chains for flashloan execution
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from web3 import Web3
from decimal import Decimal

logger = logging.getLogger(__name__)

class GasReserveManager:
    """Manages gas reserves across multiple chains for flashloan operations."""
    
    def __init__(self, web3_connections: Dict[str, Web3], wallet_account, smart_wallet_manager):
        self.web3_connections = web3_connections
        self.wallet_account = wallet_account
        self.smart_wallet_manager = smart_wallet_manager
        
        # Optimal gas reserves per chain (in ETH)
        self.target_gas_reserves = {
            'arbitrum': 0.02,    # $64 at $3200/ETH - cheap gas
            'base': 0.015,       # $48 at $3200/ETH - very cheap gas  
            'optimism': 0.015,   # $48 at $3200/ETH - cheap gas
            'ethereum': 0.05     # $160 at $3200/ETH - expensive gas
        }
        
        # Minimum gas reserves (emergency level)
        self.minimum_gas_reserves = {
            'arbitrum': 0.005,   # $16 - absolute minimum
            'base': 0.003,       # $10 - absolute minimum
            'optimism': 0.003,   # $10 - absolute minimum  
            'ethereum': 0.015    # $48 - absolute minimum
        }
        
        # Maximum gas reserves (don't over-allocate)
        self.maximum_gas_reserves = {
            'arbitrum': 0.05,    # $160 - don't tie up too much
            'base': 0.03,        # $96 - don't tie up too much
            'optimism': 0.03,    # $96 - don't tie up too much
            'ethereum': 0.1      # $320 - expensive but necessary
        }
        
        # Gas cost estimates per flashloan (in ETH)
        self.flashloan_gas_costs = {
            'arbitrum': 0.001,   # ~$3.20 per flashloan
            'base': 0.0005,      # ~$1.60 per flashloan
            'optimism': 0.0005,  # ~$1.60 per flashloan
            'ethereum': 0.015    # ~$48 per flashloan (expensive!)
        }
    
    async def check_gas_reserves(self) -> Dict[str, Any]:
        """Check current gas reserves across all chains."""
        reserves_status = {}
        total_gas_value_usd = 0
        
        for chain, w3 in self.web3_connections.items():
            try:
                # Get current ETH balance
                balance_wei = w3.eth.get_balance(self.wallet_account.address)
                balance_eth = float(w3.from_wei(balance_wei, 'ether'))
                balance_usd = balance_eth * 3200  # ETH price estimate
                
                target_eth = self.target_gas_reserves.get(chain, 0.02)
                minimum_eth = self.minimum_gas_reserves.get(chain, 0.005)
                maximum_eth = self.maximum_gas_reserves.get(chain, 0.05)
                
                # Determine status
                if balance_eth >= target_eth:
                    status = 'optimal'
                elif balance_eth >= minimum_eth:
                    status = 'low'
                else:
                    status = 'critical'
                
                # Calculate how many flashloans possible
                gas_cost_per_flashloan = self.flashloan_gas_costs.get(chain, 0.001)
                possible_flashloans = int(balance_eth / gas_cost_per_flashloan) if gas_cost_per_flashloan > 0 else 0
                
                reserves_status[chain] = {
                    'current_eth': balance_eth,
                    'current_usd': balance_usd,
                    'target_eth': target_eth,
                    'minimum_eth': minimum_eth,
                    'maximum_eth': maximum_eth,
                    'status': status,
                    'possible_flashloans': possible_flashloans,
                    'needs_refill': balance_eth < target_eth,
                    'shortage_eth': max(0, target_eth - balance_eth),
                    'excess_eth': max(0, balance_eth - maximum_eth)
                }
                
                total_gas_value_usd += balance_usd
                
            except Exception as e:
                logger.error(f"Error checking gas reserves for {chain}: {e}")
                reserves_status[chain] = {'error': str(e)}
        
        return {
            'reserves_by_chain': reserves_status,
            'total_gas_value_usd': total_gas_value_usd,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    async def rebalance_gas_reserves(self) -> Dict[str, Any]:
        """Automatically rebalance gas reserves across chains."""
        logger.info("🔄 Starting gas reserve rebalancing...")
        
        reserves_status = await self.check_gas_reserves()
        rebalance_actions = []
        
        for chain, status in reserves_status['reserves_by_chain'].items():
            if 'error' in status:
                continue
                
            if status['needs_refill'] and status['shortage_eth'] > 0.001:  # Only refill if shortage > 0.001 ETH
                # Need to add gas to this chain
                shortage_eth = status['shortage_eth']
                shortage_usd = shortage_eth * 3200
                
                logger.info(f"🔄 {chain.upper()}: Need {shortage_eth:.6f} ETH (${shortage_usd:.2f}) for gas")
                
                # Use smart wallet manager to convert tokens to ETH
                if self.smart_wallet_manager:
                    conversion_result = await self.smart_wallet_manager.ensure_sufficient_eth_for_trade(
                        required_eth_amount=shortage_eth,
                        chain=chain
                    )
                    
                    if conversion_result['success']:
                        rebalance_actions.append({
                            'chain': chain,
                            'action': 'refilled',
                            'amount_eth': shortage_eth,
                            'amount_usd': shortage_usd,
                            'method': 'token_conversion'
                        })
                        logger.info(f"✅ {chain.upper()}: Gas reserve refilled")
                    else:
                        rebalance_actions.append({
                            'chain': chain,
                            'action': 'failed',
                            'error': conversion_result.get('error', 'Unknown error')
                        })
                        logger.error(f"❌ {chain.upper()}: Gas refill failed")
            
            elif status['excess_eth'] > 0.005:  # If excess > 0.005 ETH, consider rebalancing
                # Too much gas on this chain - could move to other chains
                excess_eth = status['excess_eth']
                excess_usd = excess_eth * 3200
                
                logger.info(f"💰 {chain.upper()}: Excess gas {excess_eth:.6f} ETH (${excess_usd:.2f}) - could rebalance")
                # TODO: Implement cross-chain gas rebalancing
        
        return {
            'rebalance_actions': rebalance_actions,
            'total_actions': len(rebalance_actions),
            'success': len([a for a in rebalance_actions if a.get('action') == 'refilled'])
        }
    
    async def can_execute_flashloan(self, chain: str, estimated_gas_cost: float = None) -> Dict[str, Any]:
        """Check if we have sufficient gas reserves to execute a flashloan."""
        if chain not in self.web3_connections:
            return {'can_execute': False, 'error': f'Chain {chain} not supported'}
        
        try:
            w3 = self.web3_connections[chain]
            balance_wei = w3.eth.get_balance(self.wallet_account.address)
            balance_eth = float(w3.from_wei(balance_wei, 'ether'))
            
            # Use provided gas cost or default estimate
            required_gas = estimated_gas_cost or self.flashloan_gas_costs.get(chain, 0.001)
            minimum_reserve = self.minimum_gas_reserves.get(chain, 0.005)
            
            # Need enough for the flashloan + maintain minimum reserve
            total_needed = required_gas + minimum_reserve
            
            can_execute = balance_eth >= total_needed
            
            return {
                'can_execute': can_execute,
                'current_balance_eth': balance_eth,
                'required_gas_eth': required_gas,
                'minimum_reserve_eth': minimum_reserve,
                'total_needed_eth': total_needed,
                'shortage_eth': max(0, total_needed - balance_eth) if not can_execute else 0
            }
            
        except Exception as e:
            return {'can_execute': False, 'error': str(e)}
    
    async def get_gas_reserve_summary(self) -> Dict[str, Any]:
        """Get a summary of gas reserves for monitoring."""
        reserves_status = await self.check_gas_reserves()
        
        summary = {
            'total_chains': len(self.web3_connections),
            'chains_optimal': 0,
            'chains_low': 0,
            'chains_critical': 0,
            'total_gas_value_usd': reserves_status['total_gas_value_usd'],
            'total_possible_flashloans': 0,
            'needs_attention': []
        }
        
        for chain, status in reserves_status['reserves_by_chain'].items():
            if 'error' in status:
                continue
                
            if status['status'] == 'optimal':
                summary['chains_optimal'] += 1
            elif status['status'] == 'low':
                summary['chains_low'] += 1
                summary['needs_attention'].append(f"{chain}: Low gas reserves")
            elif status['status'] == 'critical':
                summary['chains_critical'] += 1
                summary['needs_attention'].append(f"{chain}: CRITICAL gas reserves")
            
            summary['total_possible_flashloans'] += status.get('possible_flashloans', 0)
        
        return summary
