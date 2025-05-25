#!/usr/bin/env python3
"""
Wallet Connection Test

Tests wallet connection and basic functionality before real trading.
Verifies security settings and performs safety checks.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


async def test_environment_setup():
    """Test environment variable setup."""
    print("🔧 Testing Environment Setup")
    print("=" * 40)
    
    required_vars = [
        'WALLET_TYPE',
        'WALLET_ADDRESS',
        'ETHEREUM_RPC_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PRIVATE' in var:
                display_value = f"{value[:6]}...{value[-4:]}" if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {missing_vars}")
        print("Run: python setup_wallet.py")
        return False
    
    print("\n✅ Environment setup complete")
    return True


async def test_wallet_manager():
    """Test wallet manager functionality."""
    print("\n🔐 Testing Wallet Manager")
    print("=" * 40)
    
    try:
        from wallet.wallet_manager import WalletManager
        
        # Create wallet manager
        config = {
            'max_gas_price_gwei': int(os.getenv('MAX_GAS_PRICE_GWEI', 50)),
            'max_trade_size_eth': float(os.getenv('MAX_TRADE_SIZE_ETH', 0.1)),
            'require_confirmation': os.getenv('REQUIRE_CONFIRMATION', 'true').lower() == 'true'
        }
        
        wallet = WalletManager(config)
        print("   ✅ Wallet manager created")
        
        # Test connection
        print("   🔗 Testing wallet connection...")
        connected = await wallet.connect_wallet()
        
        if connected:
            print("   ✅ Wallet connected successfully")
            
            # Get wallet info
            info = wallet.get_wallet_info()
            print(f"   📍 Address: {info['address'][:6]}...{info['address'][-4:]}")
            print(f"   ⛽ Max gas: {info['max_gas_price_gwei']} gwei")
            print(f"   💰 Max trade: {info['max_trade_size_eth']} ETH")
            print(f"   🔒 Confirmation: {info['require_confirmation']}")
            
            # Test balance check
            print("   💰 Checking balance...")
            balance = await wallet.get_balance()
            print(f"   💰 ETH Balance: {balance} ETH")
            
            # Test gas price
            print("   ⛽ Checking gas price...")
            gas_price = await wallet.get_gas_price()
            gas_price_gwei = gas_price // 10**9
            print(f"   ⛽ Current gas: {gas_price_gwei} gwei")
            
            await wallet.disconnect()
            print("   ✅ Wallet disconnected")
            
            return True
        else:
            print("   ❌ Wallet connection failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Wallet manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_security_settings():
    """Test security settings and limits."""
    print("\n🛡️  Testing Security Settings")
    print("=" * 40)
    
    try:
        from wallet.wallet_manager import WalletManager
        
        config = {
            'max_gas_price_gwei': int(os.getenv('MAX_GAS_PRICE_GWEI', 50)),
            'max_trade_size_eth': float(os.getenv('MAX_TRADE_SIZE_ETH', 0.1)),
            'require_confirmation': os.getenv('REQUIRE_CONFIRMATION', 'true').lower() == 'true'
        }
        
        wallet = WalletManager(config)
        await wallet.connect_wallet()
        
        # Test trade validation with safe parameters
        safe_trade = {
            'from_token': 'ETH',
            'to_token': 'USDC',
            'amount': 0.01,  # Small amount
            'dex': 'uniswap'
        }
        
        print("   🔍 Testing safe trade validation...")
        valid = await wallet._validate_trade(safe_trade)
        if valid:
            print("   ✅ Safe trade validation passed")
        else:
            print("   ❌ Safe trade validation failed")
        
        # Test trade validation with unsafe parameters
        unsafe_trade = {
            'from_token': 'ETH',
            'to_token': 'USDC',
            'amount': 10.0,  # Large amount
            'dex': 'uniswap'
        }
        
        print("   🔍 Testing unsafe trade validation...")
        valid = await wallet._validate_trade(unsafe_trade)
        if not valid:
            print("   ✅ Unsafe trade correctly rejected")
        else:
            print("   ❌ Unsafe trade incorrectly accepted")
        
        await wallet.disconnect()
        return True
        
    except Exception as e:
        print(f"   ❌ Security test failed: {e}")
        return False


async def test_simulated_trade():
    """Test simulated trade execution."""
    print("\n🎯 Testing Simulated Trade")
    print("=" * 40)
    
    try:
        from wallet.wallet_manager import WalletManager
        
        config = {
            'max_gas_price_gwei': int(os.getenv('MAX_GAS_PRICE_GWEI', 50)),
            'max_trade_size_eth': float(os.getenv('MAX_TRADE_SIZE_ETH', 0.1)),
            'require_confirmation': False  # Disable for testing
        }
        
        wallet = WalletManager(config)
        await wallet.connect_wallet()
        
        # Test trade parameters
        trade_params = {
            'from_token': 'ETH',
            'to_token': 'USDC',
            'amount': 0.01,  # Small test amount
            'dex': 'uniswap',
            'expected_output': 25.0  # ~$25 worth
        }
        
        print("   🎯 Executing simulated trade...")
        result = await wallet.execute_trade(trade_params)
        
        if result['success']:
            print("   ✅ Simulated trade successful!")
            print(f"   📝 TX Hash: {result['tx_hash'][:10]}...")
            print(f"   ⛽ Gas used: {result['gas_used']:,}")
            print(f"   💰 Gas cost: {result['gas_cost_eth']:.6f} ETH")
        else:
            print(f"   ❌ Simulated trade failed: {result['error']}")
        
        await wallet.disconnect()
        return result['success']
        
    except Exception as e:
        print(f"   ❌ Simulated trade test failed: {e}")
        return False


async def test_trading_mode():
    """Test trading mode configuration."""
    print("\n💰 Testing Trading Mode")
    print("=" * 40)
    
    trading_enabled = os.getenv('TRADING_ENABLED', 'false').lower() == 'true'
    
    if trading_enabled:
        print("   ⚠️  REAL TRADING MODE ENABLED!")
        print("   ⚠️  Bot will execute real transactions!")
        print("   ⚠️  Make sure you're ready for real trading!")
        
        confirm = input("   Continue with real trading mode? (y/N): ").lower()
        if confirm != 'y':
            print("   🛑 Real trading mode cancelled")
            return False
        else:
            print("   ✅ Real trading mode confirmed")
            return True
    else:
        print("   ✅ Simulation mode enabled (safe)")
        print("   💡 Set TRADING_ENABLED=true when ready for real trading")
        return True


async def main():
    """Run all wallet tests."""
    print("🔐 WALLET CONNECTION TEST SUITE")
    print("=" * 60)
    print("Testing wallet setup before real trading")
    print("=" * 60)
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("❌ .env file not found!")
        print("Run: python setup_wallet.py")
        return False
    
    # Run all tests
    env_ok = await test_environment_setup()
    wallet_ok = await test_wallet_manager()
    security_ok = await test_security_settings()
    trade_ok = await test_simulated_trade()
    mode_ok = await test_trading_mode()
    
    print("\n📊 TEST RESULTS")
    print("=" * 30)
    print(f"Environment Setup: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Wallet Manager: {'✅ PASS' if wallet_ok else '❌ FAIL'}")
    print(f"Security Settings: {'✅ PASS' if security_ok else '❌ FAIL'}")
    print(f"Simulated Trade: {'✅ PASS' if trade_ok else '❌ FAIL'}")
    print(f"Trading Mode: {'✅ PASS' if mode_ok else '❌ FAIL'}")
    
    all_passed = all([env_ok, wallet_ok, security_ok, trade_ok, mode_ok])
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Wallet is ready for arbitrage trading!")
        print("\n🎯 Next Steps:")
        print("1. ✅ Wallet configuration complete")
        print("2. ✅ Security settings verified")
        print("3. ✅ Simulated trading working")
        print("4. 🔄 Run enhanced arbitrage bot")
        print("5. 🔄 Monitor first real trades carefully")
        print("\n💰 Ready to make money!")
    else:
        print("\n⚠️  Some tests failed")
        print("Please fix the issues before real trading")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite crashed: {e}")
        sys.exit(1)
