#!/usr/bin/env python3
"""
Debug Contract Execution Issues
Analyzes why smart contract swaps are reverting.
"""

import os
import asyncio
from web3 import Web3
from eth_account import Account
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class ContractExecutionDebugger:
    """Debug smart contract execution issues."""
    
    def __init__(self):
        # Get environment variables
        self.private_key = os.getenv('WALLET_PRIVATE_KEY')
        self.alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
        
        if not self.private_key or not self.alchemy_api_key:
            raise ValueError("Missing WALLET_PRIVATE_KEY or ALCHEMY_API_KEY environment variables")
        
        # Setup Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(f"https://arb-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"))
        self.account = Account.from_key(self.private_key)
        
        # Token addresses on Arbitrum
        self.tokens = {
            'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
            'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
            'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
            'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'
        }
        
        # SushiSwap router on Arbitrum
        self.sushi_router = '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
        
        # ERC20 ABI (minimal)
        self.erc20_abi = [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
        ]
        
        # Router ABI (minimal)
        self.router_abi = [
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"}, {"internalType": "address[]", "name": "path", "type": "address[]"}, {"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "swapExactTokensForETH", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "amountOutMin", "type": "uint256"}, {"internalType": "address[]", "name": "path", "type": "address[]"}, {"internalType": "address", "name": "to", "type": "address"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "swapExactETHForTokens", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "payable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "address[]", "name": "path", "type": "address[]"}], "name": "getAmountsOut", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}], "stateMutability": "view", "type": "function"}
        ]
    
    async def debug_wallet_state(self):
        """Check current wallet state and balances."""
        logger.info("🔍 DEBUGGING WALLET STATE")
        logger.info("=" * 40)
        
        # Check ETH balance
        eth_balance = self.w3.eth.get_balance(self.account.address)
        eth_balance_ether = self.w3.from_wei(eth_balance, 'ether')
        logger.info(f"💰 ETH Balance: {eth_balance_ether:.6f} ETH")
        
        # Check token balances
        for token_name, token_address in self.tokens.items():
            try:
                contract = self.w3.eth.contract(address=token_address, abi=self.erc20_abi)
                balance = contract.functions.balanceOf(self.account.address).call()
                decimals = contract.functions.decimals().call()
                balance_formatted = balance / (10 ** decimals)
                logger.info(f"💰 {token_name} Balance: {balance_formatted:.6f} {token_name}")
                
                # Check allowance for SushiSwap
                allowance = contract.functions.allowance(self.account.address, self.sushi_router).call()
                allowance_formatted = allowance / (10 ** decimals)
                logger.info(f"✅ {token_name} Allowance: {allowance_formatted:.6f} {token_name}")
                
            except Exception as e:
                logger.error(f"❌ Error checking {token_name}: {e}")
    
    async def test_simple_swap(self, amount_eth=0.001):
        """Test a simple ETH → WETH swap to diagnose issues."""
        logger.info(f"\n🧪 TESTING SIMPLE SWAP: {amount_eth} ETH → WETH")
        logger.info("=" * 50)
        
        try:
            # Get router contract
            router = self.w3.eth.contract(address=self.sushi_router, abi=self.router_abi)
            
            # Setup swap parameters
            amount_wei = self.w3.to_wei(amount_eth, 'ether')
            path = [self.tokens['WETH']]  # ETH → WETH path (just WETH for ETH swaps)
            deadline = int(self.w3.eth.get_block('latest')['timestamp']) + 300  # 5 minutes
            
            # Calculate minimum output (95% of input for ETH → WETH)
            min_amount_out = int(amount_wei * 0.95)
            
            logger.info(f"📊 Swap Parameters:")
            logger.info(f"   Amount In: {amount_wei} wei ({amount_eth} ETH)")
            logger.info(f"   Min Amount Out: {min_amount_out} wei")
            logger.info(f"   Path: ETH → WETH")
            logger.info(f"   Deadline: {deadline}")
            logger.info(f"   To: {self.account.address}")
            
            # Try to get quote first
            try:
                amounts_out = router.functions.getAmountsOut(amount_wei, path).call()
                expected_out = amounts_out[-1]
                logger.info(f"📈 Expected Output: {expected_out} wei ({self.w3.from_wei(expected_out, 'ether'):.6f} WETH)")
            except Exception as quote_error:
                logger.error(f"❌ Quote failed: {quote_error}")
                return False
            
            # Build transaction
            try:
                swap_tx = router.functions.swapExactETHForTokens(
                    min_amount_out,
                    path,
                    self.account.address,
                    deadline
                ).build_transaction({
                    'from': self.account.address,
                    'value': amount_wei,
                    'gas': 300000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.account.address)
                })
                
                logger.info(f"✅ Transaction built successfully")
                logger.info(f"📊 Gas: {swap_tx['gas']}")
                logger.info(f"⛽ Gas Price: {self.w3.from_wei(swap_tx['gasPrice'], 'gwei'):.1f} gwei")
                
                # Estimate gas to check for revert
                try:
                    estimated_gas = self.w3.eth.estimate_gas(swap_tx)
                    logger.info(f"✅ Gas estimation successful: {estimated_gas}")
                except Exception as gas_error:
                    logger.error(f"❌ Gas estimation failed: {gas_error}")
                    logger.error("   This indicates the transaction would revert!")
                    return False
                
                # Ask user if they want to execute
                logger.info(f"\n🚀 Ready to execute swap. Proceed? (y/n)")
                # For automated testing, we'll skip actual execution
                logger.info("   (Skipping execution for safety - transaction appears valid)")
                return True
                
            except Exception as build_error:
                logger.error(f"❌ Transaction build failed: {build_error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test swap failed: {e}")
            return False
    
    async def analyze_failed_transaction(self, tx_hash):
        """Analyze a specific failed transaction."""
        logger.info(f"\n🔍 ANALYZING FAILED TRANSACTION: {tx_hash}")
        logger.info("=" * 60)
        
        try:
            # Get transaction details
            tx = self.w3.eth.get_transaction(tx_hash)
            logger.info(f"📊 Transaction Details:")
            logger.info(f"   From: {tx['from']}")
            logger.info(f"   To: {tx['to']}")
            logger.info(f"   Value: {self.w3.from_wei(tx['value'], 'ether')} ETH")
            logger.info(f"   Gas: {tx['gas']}")
            logger.info(f"   Gas Price: {self.w3.from_wei(tx['gasPrice'], 'gwei')} gwei")
            
            # Get receipt
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            logger.info(f"📋 Receipt:")
            logger.info(f"   Status: {'SUCCESS' if receipt['status'] == 1 else 'FAILED'}")
            logger.info(f"   Gas Used: {receipt['gasUsed']}")
            logger.info(f"   Block: {receipt['blockNumber']}")
            
            if receipt['status'] == 0:
                logger.info("❌ Transaction failed - analyzing revert reason...")
                
                # Try to get revert reason
                try:
                    self.w3.eth.call(tx, receipt['blockNumber'])
                except Exception as revert_error:
                    logger.error(f"💥 Revert Reason: {revert_error}")
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")

async def main():
    """Main debugging function."""
    try:
        debugger = ContractExecutionDebugger()
        
        # Check wallet state
        await debugger.debug_wallet_state()
        
        # Test simple swap
        await debugger.test_simple_swap()
        
        # Analyze the specific failed transaction
        failed_tx = "1f376839205e80af85c55e9b863ae27f6ddca68f99cbf264056f566fc3525f91"
        await debugger.analyze_failed_transaction(failed_tx)
        
        logger.info("\n✅ DEBUGGING COMPLETE!")
        
    except Exception as e:
        logger.error(f"❌ Debugging failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
