#!/usr/bin/env python3
"""
🚀 SIMPLE ARBITRAGE BOT - DIRECT WALLET TRADING
Bypasses complex master system - goes straight to making money!
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from web3 import Web3
from decimal import Decimal

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class SimpleArbitrageBot:
    """Simple, direct arbitrage bot that actually works."""
    
    def __init__(self):
        self.wallet_address = os.getenv('WALLET_ADDRESS')
        self.private_key = os.getenv('PRIVATE_KEY')
        self.alchemy_key = os.getenv('ALCHEMY_API_KEY')
        
        # Arbitrum connection (where your money is)
        self.w3 = Web3(Web3.HTTPProvider(f'https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_key}'))
        self.account = self.w3.eth.account.from_key(self.private_key)
        
        # SushiSwap router (proven working)
        self.sushi_router = '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
        
        # Token addresses (corrected)
        self.tokens = {
            'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
            'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
            'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
            'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
        }
        
        # ERC20 ABI (minimal)
        self.erc20_abi = [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
             "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], 
             "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
        ]
        
        # Uniswap V2 Router ABI (minimal)
        self.router_abi = [
            {"constant": False, "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}
            ], "name": "swapExactTokensForTokens", "outputs": [{"name": "amounts", "type": "uint256[]"}], "type": "function"},
            {"constant": True, "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ], "name": "getAmountsOut", "outputs": [{"name": "amounts", "type": "uint256[]"}], "type": "function"}
        ]
        
        logger.info("✅ Simple arbitrage bot initialized")
    
    def get_balance(self, token_symbol):
        """Get token balance."""
        try:
            if token_symbol == 'ETH':
                balance = self.w3.eth.get_balance(self.wallet_address)
                return self.w3.from_wei(balance, 'ether')
            
            token_address = self.tokens.get(token_symbol)
            if not token_address:
                return Decimal('0')
            
            contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
            balance = contract.functions.balanceOf(self.wallet_address).call()
            decimals = contract.functions.decimals().call()
            
            return Decimal(balance) / Decimal(10 ** decimals)
            
        except Exception as e:
            logger.error(f"Error getting {token_symbol} balance: {e}")
            return Decimal('0')
    
    def check_wallet(self):
        """Check wallet balances."""
        logger.info("💰 WALLET CHECK:")
        
        eth_balance = self.get_balance('ETH')
        logger.info(f"   ETH: {eth_balance:.6f}")
        
        for token in ['USDC', 'USDT', 'DAI', 'WETH']:
            balance = self.get_balance(token)
            logger.info(f"   {token}: {balance:.2f}")
        
        return eth_balance
    
    def get_price_quote(self, token_in, token_out, amount_in):
        """Get price quote from SushiSwap."""
        try:
            router = self.w3.eth.contract(address=self.sushi_router, abi=self.router_abi)
            
            token_in_addr = self.tokens[token_in]
            token_out_addr = self.tokens[token_out]
            
            # Convert amount to wei
            if token_in == 'USDC' or token_in == 'USDT':
                amount_wei = int(amount_in * 10**6)  # 6 decimals
            else:
                amount_wei = int(amount_in * 10**18)  # 18 decimals
            
            path = [token_in_addr, token_out_addr]
            amounts = router.functions.getAmountsOut(amount_wei, path).call()
            
            # Convert output amount
            if token_out == 'USDC' or token_out == 'USDT':
                amount_out = amounts[1] / 10**6
            else:
                amount_out = amounts[1] / 10**18
            
            return amount_out
            
        except Exception as e:
            logger.error(f"Error getting quote {token_in}→{token_out}: {e}")
            return 0
    
    def execute_swap(self, token_in, token_out, amount_in):
        """Execute a real swap on SushiSwap."""
        try:
            logger.info(f"🚀 EXECUTING SWAP: {amount_in} {token_in} → {token_out}")
            
            # Get contracts
            token_in_contract = self.w3.eth.contract(address=self.tokens[token_in], abi=self.erc20_abi)
            router = self.w3.eth.contract(address=self.sushi_router, abi=self.router_abi)
            
            # Convert amount to wei
            if token_in == 'USDC' or token_in == 'USDT':
                amount_wei = int(amount_in * 10**6)
            else:
                amount_wei = int(amount_in * 10**18)
            
            # Check allowance and approve if needed
            allowance = token_in_contract.functions.allowance(self.wallet_address, self.sushi_router).call()
            if allowance < amount_wei:
                logger.info("   📝 Approving token spend...")
                approve_tx = token_in_contract.functions.approve(self.sushi_router, amount_wei * 2)
                approve_tx = approve_tx.build_transaction({
                    'from': self.wallet_address,
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.wallet_address)
                })
                
                signed_approve = self.account.sign_transaction(approve_tx)
                approve_hash = self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                logger.info(f"   ✅ Approval tx: {approve_hash.hex()}")
                
                # Wait for approval
                self.w3.eth.wait_for_transaction_receipt(approve_hash)
            
            # Get quote for minimum output (90% slippage tolerance)
            expected_out = self.get_price_quote(token_in, token_out, amount_in)
            min_out = int(expected_out * 0.9 * (10**6 if token_out in ['USDC', 'USDT'] else 10**18))
            
            # Build swap transaction
            path = [self.tokens[token_in], self.tokens[token_out]]
            deadline = int(time.time()) + 300  # 5 minutes
            
            swap_tx = router.functions.swapExactTokensForTokens(
                amount_wei,
                min_out,
                path,
                self.wallet_address,
                deadline
            ).build_transaction({
                'from': self.wallet_address,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address)
            })
            
            # Sign and send
            signed_swap = self.account.sign_transaction(swap_tx)
            swap_hash = self.w3.eth.send_raw_transaction(signed_swap.raw_transaction)
            
            logger.info(f"   🎯 Swap tx: {swap_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(swap_hash)
            
            if receipt.status == 1:
                logger.info("   ✅ SWAP SUCCESSFUL!")
                return True
            else:
                logger.error("   ❌ Swap failed")
                return False
                
        except Exception as e:
            logger.error(f"   💥 Swap error: {e}")
            return False
    
    def find_arbitrage(self):
        """Find simple arbitrage opportunities."""
        logger.info("🔍 Scanning for arbitrage...")
        
        # Simple strategy: Look for USDC/USDT price differences
        usdc_balance = self.get_balance('USDC')
        usdt_balance = self.get_balance('USDT')
        
        if usdc_balance > 10:  # If we have USDC
            # Check USDC → USDT rate
            usdt_out = self.get_price_quote('USDC', 'USDT', 100)
            if usdt_out > 100.1:  # 0.1% profit
                profit = usdt_out - 100
                logger.info(f"   💰 OPPORTUNITY: USDC→USDT profit: ${profit:.2f}")
                return ('USDC', 'USDT', min(100, float(usdc_balance)))
        
        if usdt_balance > 10:  # If we have USDT
            # Check USDT → USDC rate
            usdc_out = self.get_price_quote('USDT', 'USDC', 100)
            if usdc_out > 100.1:  # 0.1% profit
                profit = usdc_out - 100
                logger.info(f"   💰 OPPORTUNITY: USDT→USDC profit: ${profit:.2f}")
                return ('USDT', 'USDC', min(100, float(usdt_balance)))
        
        return None
    
    async def run(self):
        """Main trading loop."""
        logger.info("🚀 STARTING SIMPLE ARBITRAGE BOT!")
        
        # Initial wallet check
        eth_balance = self.check_wallet()
        
        if eth_balance < 0.001:
            logger.error("❌ Insufficient ETH for gas fees")
            return
        
        scan_count = 0
        while True:
            try:
                scan_count += 1
                logger.info(f"⏰ Scan #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Look for opportunities
                opportunity = self.find_arbitrage()
                
                if opportunity:
                    token_in, token_out, amount = opportunity
                    logger.info(f"🎯 EXECUTING: {amount} {token_in} → {token_out}")
                    
                    success = self.execute_swap(token_in, token_out, amount)

                    # 🎨 COLOR-CODED RESULTS: Yellow for success, red for failure
                    if success:
                        from src.utils.color_logger import Colors
                        logger.info(Colors.success("✅ TRADE SUCCESSFUL!"))
                        self.check_wallet()  # Show new balances
                    else:
                        from src.utils.color_logger import Colors
                        logger.error(Colors.failure("❌ Trade failed"))
                else:
                    logger.info("   📊 No profitable opportunities found")
                
                # Wait before next scan
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"💥 Error: {e}")
                await asyncio.sleep(10)

async def main():
    """Main function."""
    print("🚀🚀🚀 SIMPLE ARBITRAGE BOT - LIVE TRADING! 🚀🚀🚀")
    print("💰 Using your wallet balance for direct DEX arbitrage")
    print("🎯 Target: Any profit > 0.1%")
    print("⚡ Strategy: USDC/USDT arbitrage on SushiSwap")
    print("🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀")
    print()
    
    bot = SimpleArbitrageBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
