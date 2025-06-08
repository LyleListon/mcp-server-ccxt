#!/usr/bin/env python3
"""
🏪 REAL DEX TRADING EXECUTOR
Execute real trades on DEXs for cross-chain arbitrage
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import os
from web3 import Web3
from eth_account import Account
import json

logger = logging.getLogger(__name__)

@dataclass
class TradeResult:
    """Result of a DEX trade execution."""
    success: bool
    tx_hash: Optional[str] = None
    amount_in: float = 0.0
    amount_out: float = 0.0
    gas_used: int = 0
    gas_price: int = 0
    slippage_pct: float = 0.0
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None

class RealDEXTradingExecutor:
    """Execute real trades on DEXs."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize real DEX trading executor."""
        self.config = config
        
        # Web3 connections
        self.web3_connections = {}
        self.chain_configs = {
            'arbitrum': {
                'rpc_url': f"https://arb-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
                'chain_id': 42161,
                'native_token': 'ETH',
                'weth_address': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
            },
            'base': {
                'rpc_url': f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
                'chain_id': 8453,
                'native_token': 'ETH',
                'weth_address': '0x4200000000000000000000000000000000000006'
            },
            'optimism': {
                'rpc_url': f"https://opt-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}",
                'chain_id': 10,
                'native_token': 'ETH',
                'weth_address': '0x4200000000000000000000000000000000000006'
            },
            'polygon': {
                'rpc_url': os.getenv('ALCHEMY_POLY_KEY'),
                'chain_id': 137,
                'native_token': 'MATIC',
                'weth_address': '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619'
            },
            'bsc': {
                'rpc_url': os.getenv('BSC_RPC_KEY'),
                'chain_id': 56,
                'native_token': 'BNB',
                'weth_address': '0x2170Ed0880ac9A755fd29B2688956BD959F933F8'
            },
            'scroll': {
                'rpc_url': os.getenv('SCROLL_RPC_KEY'),
                'chain_id': 534352,
                'native_token': 'ETH',
                'weth_address': '0x5300000000000000000000000000000000000004'
            },
            'mantle': {
                'rpc_url': os.getenv('MANTLE_RPC_KEY'),
                'chain_id': 5000,
                'native_token': 'MNT',
                'weth_address': '0xdEAddEaDdeadDEadDEADDEAddEADDEAddead1111'
            },
            'blast': {
                'rpc_url': os.getenv('BLAST_RPC_KEY'),
                'chain_id': 81457,
                'native_token': 'ETH',
                'weth_address': '0x4300000000000000000000000000000000000004'
            }
        }
        
        # DEX configurations with real contract addresses
        self.dex_configs = {
            'arbitrum': {
                'sushiswap': {
                    'router': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',
                    'factory': '0xc35DADB65012eC5796536bD9864eD8773aBc74C4',
                    'type': 'uniswap_v2'
                },
                'camelot': {
                    'router': '0xc873fEcbd354f5A56E00E710B90EF4201db2448d',
                    'factory': '0x6EcCab422D763aC031210895C81787E87B91425',
                    'type': 'uniswap_v2'
                },
                'uniswap_v3': {
                    'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                    'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
                    'type': 'uniswap_v3'
                },
                'traderjoe': {
                    'router': '0xb4315e873dBcf96Ffd0acd8EA43f689D8c20fB30',
                    'factory': '0x740b1c1de25031C31FF4fC9A62f554A55cdC1baD',
                    'type': 'uniswap_v2'
                },
                'solidly': {
                    'router': '0x4c7ffd05eadd3716bd42f0161c69dc808f889ef8',
                    'factory': '0x777de5fe8117caaa7b44f396fcbf26b32e15906a',
                    'type': 'uniswap_v2'
                },
                'ramses': {
                    'router': '0xAAA87963EFeB6f7E0a2711F397663105Acb1805e',
                    'factory': '0xAAA20D08e59F6561f242b08513D36266C5A29415',
                    'type': 'uniswap_v2'
                }
            },
            'base': {
                'aerodrome': {
                    'router': '0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43',
                    'factory': '0x420DD381b31aEf6683db6B902084cB0FFECe40Da',
                    'type': 'uniswap_v2'
                },
                'baseswap': {
                    'router': '0x327Df1E6de05895d2ab08513aaDD9313Fe505d86',
                    'factory': '0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB',
                    'type': 'uniswap_v2'
                },
                'swapfish': {
                    'router': '0x1231DEB6f5749EF6cE6943a275A1D3E7486F4EaE',
                    'factory': '0x71539D09D3890195dDa87A6198B98B75211b72F3',
                    'type': 'uniswap_v2'
                },
                'dackieswap': {
                    'router': '0x1A0A18AC4BECDDbd6389559687d1A73d8927E416',
                    'factory': '0x43eC799eAdd63848443E2347C49f5f52e8Fe0F6f',
                    'type': 'uniswap_v2'
                },
                'meshswap': {
                    'router': '0x10f4A785F458Bc144e3706575924889954946639',
                    'factory': '0x9d3591719038752db0c8bEEe2040FfcC3B2c6B9c',
                    'type': 'uniswap_v2'
                }
            },
            'optimism': {
                'velodrome': {
                    'router': '0xa132DAB612dB5cB9fC9Ac426A0Cc215A3423F9c9',
                    'factory': '0x25CbdDb98b35ab1FF77413456B31EC81A6B6B746',
                    'type': 'uniswap_v2'
                },
                'ramses': {
                    'router': '0xAAA87963EFeB6f7E0a2711F397663105Acb1805e',
                    'factory': '0xAAA20D08e59F6561f242b08513D36266C5A29415',
                    'type': 'uniswap_v2'
                },
                'kyberswap': {
                    'router': '0x6131B5fae19EA4f9D964eAc0408E4408b66337b5',
                    'factory': '0x5F1dddbf348aC2fbe22a163e30F99F9ECE3DD50a',
                    'type': 'uniswap_v2'
                }
            }
        }
        
        # Token configurations with all major tokens
        self.token_configs = {
            'arbitrum': {
                'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
                'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                'USDC.e': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
                'ETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',  # Same as WETH
                'LINK': '0xf97f4df75117a78c1A5a0DBb814Af92458539FB4',
                'UNI': '0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0',
                'ARB': '0x912CE59144191C1204E64559FE8253a0e49E6548',
                'CRV': '0x11cDb42B0EB46D95f990BeDD4695A6e3fA034978',
                'AVAX': '0x565609fAF65B92F7be02468acF86f8979423e514',
                'MATIC': '0x561877b6b3DD7651313794e5F2894B2F18bE0766',
                'FTM': '0xd42785D323e608B9E99fa542bd8b1000D4c2Df37',
                'OP': '0x4200000000000000000000000000000000000042',
                'WBTC': '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f'
            },
            'base': {
                'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
                'WETH': '0x4200000000000000000000000000000000000006',
                'ETH': '0x4200000000000000000000000000000000000006',  # Same as WETH
                'LINK': '0x88Fb150BDc53A65fe94Dea0c9BA0a6dAf8C6e196',
                'UNI': '0x3e7eF8f50246f725885102E8238CBba33F276747',
                'CRV': '0x8Ee73c484A26e0A5df2Ee2a4960B789967dd0415',
                'AVAX': '0x4158734D47Fc9692176B5085E0F52ee0Da5d47F1',
                'MATIC': '0x7c6b91D9Be155A6Db01f749217d76fF02A7227F2',
                'FTM': '0x4621b7A9c75199271F773Ebd9A499dbd165c3191',
                'BNB': '0xd07379a755A8f11B57610154861D694b2A0f615a',
                'OP': '0x4200000000000000000000000000000000000042',
                'WBTC': '0x1C7a460413dD4e964f96D8dFC56E7223cE88CD85',
                'USDT': '0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2'
            },
            'optimism': {
                'USDC': '0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85',
                'USDT': '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58',
                'WETH': '0x4200000000000000000000000000000000000006',
                'ETH': '0x4200000000000000000000000000000000000006',  # Same as WETH
                'LINK': '0x350a791Bfc2C21F9Ed5d10980Dad2e2638ffa7f6',
                'UNI': '0x6fd9d7AD17242c41f7131d257212c54A0e816691',
                'CRV': '0xaddb6a0412de1ba0f936dcaeb8aaa24578dcf3b2',
                'AVAX': '0x565609fAF65B92F7be02468acF86f8979423e514',
                'MATIC': '0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85',
                'FTM': '0x2513486f18eeE1498D7b6281f668B955181Dd0D9',
                'OP': '0x4200000000000000000000000000000000000042',
                'WBTC': '0x68f180fcCe6836688e9084f035309E29Bf0A2095'
            }
        }
        
        # Trading settings
        self.max_slippage_pct = config.get('max_slippage_pct', 2.0)  # 2% max slippage
        self.gas_price_multiplier = config.get('gas_price_multiplier', 1.1)  # 10% above market
        self.trade_timeout_seconds = config.get('trade_timeout_seconds', 60)  # 1 minute timeout
        
        # Load wallet
        self.wallet_address = None
        self.private_key = None
        
        logger.info("🏪 Real DEX trading executor initialized")
        logger.info(f"   🎯 Max slippage: {self.max_slippage_pct}%")
        logger.info(f"   ⛽ Gas multiplier: {self.gas_price_multiplier}x")
    
    async def initialize(self, private_key: str) -> bool:
        """Initialize Web3 connections and wallet."""
        try:
            logger.info("🔧 Initializing real DEX trading connections...")
            
            # Load wallet
            self.private_key = private_key
            account = Account.from_key(private_key)
            self.wallet_address = account.address
            
            logger.info(f"   🔑 Wallet: {self.wallet_address}")
            
            # Initialize Web3 connections
            for chain, config in self.chain_configs.items():
                try:
                    self.web3_connections[chain] = Web3(Web3.HTTPProvider(config['rpc_url']))
                    
                    # Test connection
                    latest_block = self.web3_connections[chain].eth.get_block('latest')
                    logger.info(f"   ✅ {chain.title()}: Block {latest_block['number']}")
                    
                except Exception as e:
                    logger.error(f"   ❌ {chain.title()}: {e}")
                    return False
            
            logger.info("✅ Real DEX trading executor ready!")
            return True
            
        except Exception as e:
            logger.error(f"DEX trading initialization failed: {e}")
            return False
    
    async def execute_buy_order(self, chain: str, token: str, amount_usd: float, 
                               dex: str, expected_price: float) -> TradeResult:
        """Execute a real buy order on a DEX."""
        start_time = datetime.now()
        
        logger.info(f"🛒 EXECUTING REAL BUY ORDER")
        logger.info(f"   Chain: {chain}")
        logger.info(f"   Token: {token}")
        logger.info(f"   Amount: ${amount_usd:.2f}")
        logger.info(f"   DEX: {dex}")
        logger.info(f"   Expected price: ${expected_price:.6f}")
        
        try:
            # Get Web3 connection
            w3 = self.web3_connections[chain]

            # Check wallet balance first
            wallet_balance_eth = w3.eth.get_balance(self.wallet_address)
            wallet_balance_eth_formatted = wallet_balance_eth / 1e18

            # Estimate gas cost
            estimated_gas_cost = 300000 * w3.eth.gas_price * self.gas_price_multiplier
            estimated_gas_cost_eth = estimated_gas_cost / 1e18

            logger.info(f"   💰 ETH balance: {wallet_balance_eth_formatted:.6f} ETH")
            logger.info(f"   ⛽ Estimated gas: {estimated_gas_cost_eth:.6f} ETH")

            # Check if we have enough ETH for gas (but allow USDC.e trades)
            if wallet_balance_eth < estimated_gas_cost:
                return TradeResult(
                    success=False,
                    error_message=f"Insufficient ETH for gas on {chain}: have {wallet_balance_eth_formatted:.6f} ETH, need {estimated_gas_cost_eth:.6f} ETH for gas"
                )

            # For USDC.e trades, check USDC.e balance instead of ETH
            if token == 'USDC.e':
                usdc_e_address = self.token_configs[chain].get('USDC.e')
                if usdc_e_address:
                    # ERC20 ABI for balanceOf
                    erc20_abi = [
                        {
                            "constant": True,
                            "inputs": [{"name": "_owner", "type": "address"}],
                            "name": "balanceOf",
                            "outputs": [{"name": "balance", "type": "uint256"}],
                            "type": "function"
                        }
                    ]

                    usdc_contract = w3.eth.contract(
                        address=w3.to_checksum_address(usdc_e_address),
                        abi=erc20_abi
                    )

                    usdc_balance = usdc_contract.functions.balanceOf(self.wallet_address).call()
                    usdc_balance_formatted = usdc_balance / 1e6  # USDC has 6 decimals

                    logger.info(f"   💰 USDC.e balance: {usdc_balance_formatted:.2f} USDC.e")

                    required_usdc = amount_usd  # For USDC.e, amount_usd is the USDC amount needed

                    if usdc_balance_formatted < required_usdc:
                        return TradeResult(
                            success=False,
                            error_message=f"Insufficient USDC.e on {chain}: have {usdc_balance_formatted:.2f} USDC.e, need {required_usdc:.2f} USDC.e"
                        )

            # Get token addresses
            token_address = self.token_configs[chain].get(token)
            weth_address = self.chain_configs[chain]['weth_address']

            if not token_address:
                return TradeResult(
                    success=False,
                    error_message=f"Token {token} not configured for {chain}"
                )

            # Ensure proper checksums
            token_address = w3.to_checksum_address(token_address)
            weth_address = w3.to_checksum_address(weth_address)
            
            # Get DEX configuration
            dex_config = self.dex_configs[chain].get(dex)
            if not dex_config:
                # Try to use a fallback DEX for the chain
                fallback_dex = self._get_fallback_dex(chain)
                if fallback_dex:
                    logger.warning(f"   ⚠️  DEX {dex} not configured, using fallback: {fallback_dex}")
                    dex_config = self.dex_configs[chain][fallback_dex]
                else:
                    return TradeResult(
                        success=False,
                        error_message=f"DEX {dex} not configured for {chain} and no fallback available"
                    )
            
            # Calculate amounts
            eth_amount = amount_usd / 3500  # Approximate ETH price
            token_amount_expected = amount_usd / expected_price
            
            # Calculate minimum amount out (with slippage protection)
            min_amount_out = int(token_amount_expected * (1 - self.max_slippage_pct / 100) * 1e18)
            amount_in = int(eth_amount * 1e18)
            
            logger.info(f"   💰 ETH in: {eth_amount:.6f} ETH")
            logger.info(f"   🎯 Expected out: {token_amount_expected:.6f} {token}")
            logger.info(f"   🛡️  Min out: {min_amount_out / 1e18:.6f} {token}")
            
            # Build transaction
            if dex_config['type'] == 'uniswap_v2':
                tx_data = await self._build_uniswap_v2_buy_tx(
                    w3, dex_config, weth_address, token_address, 
                    amount_in, min_amount_out
                )
            else:
                return TradeResult(
                    success=False,
                    error_message=f"DEX type {dex_config['type']} not implemented"
                )
            
            if not tx_data:
                return TradeResult(
                    success=False,
                    error_message="Failed to build transaction"
                )
            
            # Execute transaction
            tx_hash = await self._send_transaction(w3, tx_data)
            
            if tx_hash:
                # Wait for confirmation
                receipt = await self._wait_for_confirmation(w3, tx_hash)
                
                if receipt and receipt['status'] == 1:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"   ✅ BUY ORDER SUCCESS!")
                    logger.info(f"   📝 TX: {tx_hash}")
                    logger.info(f"   ⏰ Time: {execution_time:.1f}s")
                    
                    return TradeResult(
                        success=True,
                        tx_hash=tx_hash,
                        amount_in=eth_amount,
                        amount_out=token_amount_expected,  # TODO: Get actual from logs
                        gas_used=receipt['gasUsed'],
                        gas_price=receipt['effectiveGasPrice'],
                        execution_time_seconds=execution_time
                    )
                else:
                    return TradeResult(
                        success=False,
                        tx_hash=tx_hash,
                        error_message="Transaction failed"
                    )
            else:
                return TradeResult(
                    success=False,
                    error_message="Failed to send transaction"
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"   ❌ BUY ORDER FAILED: {e}")
            
            return TradeResult(
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )
    
    async def execute_sell_order(self, chain: str, token: str, amount: float, 
                                dex: str, expected_price: float) -> TradeResult:
        """Execute a real sell order on a DEX."""
        start_time = datetime.now()
        
        logger.info(f"💰 EXECUTING REAL SELL ORDER")
        logger.info(f"   Chain: {chain}")
        logger.info(f"   Token: {token}")
        logger.info(f"   Amount: {amount:.6f} {token}")
        logger.info(f"   DEX: {dex}")
        logger.info(f"   Expected price: ${expected_price:.6f}")
        
        try:
            # Get Web3 connection
            w3 = self.web3_connections[chain]
            
            # Get token addresses
            token_address = self.token_configs[chain].get(token)
            weth_address = self.chain_configs[chain]['weth_address']

            if not token_address:
                return TradeResult(
                    success=False,
                    error_message=f"Token {token} not configured for {chain}"
                )

            # Ensure proper checksums
            token_address = w3.to_checksum_address(token_address)
            weth_address = w3.to_checksum_address(weth_address)
            
            # Get DEX configuration
            dex_config = self.dex_configs[chain].get(dex)
            if not dex_config:
                # Try to use a fallback DEX for the chain
                fallback_dex = self._get_fallback_dex(chain)
                if fallback_dex:
                    logger.warning(f"   ⚠️  DEX {dex} not configured, using fallback: {fallback_dex}")
                    dex_config = self.dex_configs[chain][fallback_dex]
                else:
                    return TradeResult(
                        success=False,
                        error_message=f"DEX {dex} not configured for {chain} and no fallback available"
                    )
            
            # Calculate amounts
            expected_eth_out = amount * expected_price / 3500  # Approximate
            min_eth_out = int(expected_eth_out * (1 - self.max_slippage_pct / 100) * 1e18)
            amount_in = int(amount * 1e18)
            
            logger.info(f"   🎯 Expected ETH out: {expected_eth_out:.6f} ETH")
            logger.info(f"   🛡️  Min ETH out: {min_eth_out / 1e18:.6f} ETH")
            
            # Build transaction
            if dex_config['type'] == 'uniswap_v2':
                tx_data = await self._build_uniswap_v2_sell_tx(
                    w3, dex_config, token_address, weth_address,
                    amount_in, min_eth_out
                )
            else:
                return TradeResult(
                    success=False,
                    error_message=f"DEX type {dex_config['type']} not implemented"
                )
            
            if not tx_data:
                return TradeResult(
                    success=False,
                    error_message="Failed to build transaction"
                )
            
            # Execute transaction
            tx_hash = await self._send_transaction(w3, tx_data)
            
            if tx_hash:
                # Wait for confirmation
                receipt = await self._wait_for_confirmation(w3, tx_hash)
                
                if receipt and receipt['status'] == 1:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"   ✅ SELL ORDER SUCCESS!")
                    logger.info(f"   📝 TX: {tx_hash}")
                    logger.info(f"   ⏰ Time: {execution_time:.1f}s")
                    
                    return TradeResult(
                        success=True,
                        tx_hash=tx_hash,
                        amount_in=amount,
                        amount_out=expected_eth_out,  # TODO: Get actual from logs
                        gas_used=receipt['gasUsed'],
                        gas_price=receipt['effectiveGasPrice'],
                        execution_time_seconds=execution_time
                    )
                else:
                    return TradeResult(
                        success=False,
                        tx_hash=tx_hash,
                        error_message="Transaction failed"
                    )
            else:
                return TradeResult(
                    success=False,
                    error_message="Failed to send transaction"
                )
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"   ❌ SELL ORDER FAILED: {e}")
            
            return TradeResult(
                success=False,
                execution_time_seconds=execution_time,
                error_message=str(e)
            )

    async def _build_uniswap_v2_buy_tx(self, w3: Web3, dex_config: Dict,
                                      weth_address: str, token_address: str,
                                      amount_in: int, min_amount_out: int) -> Optional[Dict]:
        """Build Uniswap V2 style buy transaction."""
        try:
            # Uniswap V2 Router ABI (simplified)
            router_abi = [
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                        {"internalType": "address[]", "name": "path", "type": "address[]"},
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                    ],
                    "name": "swapExactETHForTokens",
                    "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                    "stateMutability": "payable",
                    "type": "function"
                }
            ]

            # Create contract instance (ensure proper checksum)
            router_address = w3.to_checksum_address(dex_config['router'])
            router_contract = w3.eth.contract(
                address=router_address,
                abi=router_abi
            )

            # Build transaction
            deadline = w3.eth.get_block('latest')['timestamp'] + 300  # 5 minutes
            path = [weth_address, token_address]

            tx_data = router_contract.functions.swapExactETHForTokens(
                min_amount_out,
                path,
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'value': amount_in,
                'gas': 300000,  # Increased gas limit for DEX swaps
                'gasPrice': int(w3.eth.gas_price * self.gas_price_multiplier),
                'nonce': w3.eth.get_transaction_count(self.wallet_address)
            })

            return tx_data

        except Exception as e:
            logger.error(f"Failed to build buy transaction: {e}")
            return None

    async def _build_uniswap_v2_sell_tx(self, w3: Web3, dex_config: Dict,
                                       token_address: str, weth_address: str,
                                       amount_in: int, min_amount_out: int) -> Optional[Dict]:
        """Build Uniswap V2 style sell transaction."""
        try:
            # Uniswap V2 Router ABI (simplified)
            router_abi = [
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                        {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                        {"internalType": "address[]", "name": "path", "type": "address[]"},
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                    ],
                    "name": "swapExactTokensForETH",
                    "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            # Create contract instance (ensure proper checksum)
            router_address = w3.to_checksum_address(dex_config['router'])
            router_contract = w3.eth.contract(
                address=router_address,
                abi=router_abi
            )

            # Build transaction
            deadline = w3.eth.get_block('latest')['timestamp'] + 300  # 5 minutes
            path = [token_address, weth_address]

            tx_data = router_contract.functions.swapExactTokensForETH(
                amount_in,
                min_amount_out,
                path,
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 300000,  # Increased gas limit for DEX swaps
                'gasPrice': int(w3.eth.gas_price * self.gas_price_multiplier),
                'nonce': w3.eth.get_transaction_count(self.wallet_address)
            })

            return tx_data

        except Exception as e:
            logger.error(f"Failed to build sell transaction: {e}")
            return None

    async def _send_transaction(self, w3: Web3, tx_data: Dict) -> Optional[str]:
        """Send transaction to blockchain."""
        try:
            logger.info(f"   📡 Signing transaction...")

            # Sign transaction
            signed_tx = w3.eth.account.sign_transaction(tx_data, self.private_key)

            logger.info(f"   📡 Sending transaction to blockchain...")

            # Send transaction (fix: use raw_transaction instead of rawTransaction)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            logger.info(f"   ✅ Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            logger.error(f"Transaction data: {tx_data}")
            return None

    async def _wait_for_confirmation(self, w3: Web3, tx_hash: str, timeout: int = 60) -> Optional[Dict]:
        """Wait for transaction confirmation."""
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            return receipt

        except Exception as e:
            logger.error(f"Transaction confirmation failed: {e}")
            return None

    def _get_fallback_dex(self, chain: str) -> Optional[str]:
        """Get a fallback DEX for the chain if the requested one isn't configured."""
        fallback_dexes = {
            'arbitrum': 'sushiswap',  # Most reliable on Arbitrum
            'base': 'aerodrome',      # Most reliable on Base
            'optimism': 'velodrome'   # Most reliable on Optimism
        }

        fallback = fallback_dexes.get(chain)
        if fallback and fallback in self.dex_configs.get(chain, {}):
            return fallback

        # If fallback not available, try any available DEX
        available_dexes = list(self.dex_configs.get(chain, {}).keys())
        return available_dexes[0] if available_dexes else None
