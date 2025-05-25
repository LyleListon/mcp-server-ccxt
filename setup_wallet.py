#!/usr/bin/env python3
"""
Secure Wallet Setup Script

Helps you configure your wallet for real trading safely.
Guides you through the setup process with security best practices.
"""

import os
import sys
import getpass
from pathlib import Path


def print_header():
    """Print setup header."""
    print("🔐 SECURE WALLET SETUP FOR ARBITRAGE BOT")
    print("=" * 60)
    print("This script will help you configure your wallet securely.")
    print("We'll use environment variables to keep your keys safe.")
    print("=" * 60)


def check_existing_config():
    """Check if .env file already exists."""
    env_file = Path('.env')
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("Setup cancelled. Edit .env manually if needed.")
            return False
    return True


def get_wallet_type():
    """Get wallet type from user."""
    print("\n🔗 WALLET TYPE SELECTION")
    print("Choose your wallet type:")
    print("1. MetaMask (Recommended for beginners)")
    print("2. Private Key (For testing only - DANGEROUS for mainnet)")
    print("3. Hardware Wallet (Not yet implemented)")
    
    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        if choice == '1':
            return 'metamask'
        elif choice == '2':
            print("\n⚠️  WARNING: Private key mode is for testing only!")
            print("⚠️  NEVER use your main wallet private key!")
            print("⚠️  Create a separate test wallet with minimal funds!")
            confirm = input("Do you understand the risks? (y/N): ").lower()
            if confirm == 'y':
                return 'private_key'
        elif choice == '3':
            print("Hardware wallet support coming soon. Please use MetaMask for now.")
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


def get_wallet_address():
    """Get wallet address from user."""
    print("\n📍 WALLET ADDRESS")
    print("Enter your wallet address (public address - safe to store):")
    print("Example: 0x742d35Cc6634C0532925a3b8D4C9db96590c6C87")
    
    while True:
        address = input("Wallet address: ").strip()
        if address.startswith('0x') and len(address) == 42:
            return address
        else:
            print("Invalid address format. Must start with 0x and be 42 characters long.")


def get_private_key():
    """Get private key securely (for testing only)."""
    print("\n🔑 PRIVATE KEY (TESTING ONLY)")
    print("⚠️  This is for testing only - use a separate test wallet!")
    print("⚠️  Never enter your main wallet private key!")
    
    private_key = getpass.getpass("Private key (hidden input): ").strip()
    
    if not private_key:
        return None
    
    if not private_key.startswith('0x'):
        private_key = '0x' + private_key
    
    if len(private_key) != 66:
        print("Invalid private key length. Should be 64 hex characters (+ 0x prefix).")
        return None
    
    return private_key


def get_rpc_url():
    """Get Ethereum RPC URL."""
    print("\n🌐 ETHEREUM NODE CONFIGURATION")
    print("Choose your Ethereum connection:")
    print("1. Local node (http://localhost:8545)")
    print("2. Infura (requires API key)")
    print("3. Alchemy (requires API key)")
    print("4. Custom URL")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        return 'http://localhost:8545'
    elif choice == '2':
        project_id = input("Enter your Infura project ID: ").strip()
        return f'https://mainnet.infura.io/v3/{project_id}'
    elif choice == '3':
        api_key = input("Enter your Alchemy API key: ").strip()
        return f'https://eth-mainnet.alchemyapi.io/v2/{api_key}'
    elif choice == '4':
        return input("Enter custom RPC URL: ").strip()
    else:
        print("Invalid choice. Using local node.")
        return 'http://localhost:8545'


def get_security_settings():
    """Get security settings."""
    print("\n🛡️  SECURITY SETTINGS")
    
    # Max gas price
    print("Maximum gas price in gwei (safety limit):")
    print("Recommended: 50 gwei for mainnet, 20 gwei for conservative")
    max_gas = input("Max gas price (default 50): ").strip() or "50"
    
    # Max trade size
    print("\nMaximum trade size in ETH (safety limit):")
    print("Recommended: 0.1 ETH for testing, 0.01 ETH for very conservative")
    max_trade = input("Max trade size (default 0.1): ").strip() or "0.1"
    
    # Require confirmation
    print("\nRequire manual confirmation for each trade?")
    print("Recommended: true for beginners, false for automated trading")
    confirm = input("Require confirmation (y/N): ").lower()
    require_confirmation = "true" if confirm == 'y' else "false"
    
    return max_gas, max_trade, require_confirmation


def get_trading_settings():
    """Get trading settings."""
    print("\n💰 TRADING SETTINGS")
    
    # Trading enabled
    print("Enable real trading?")
    print("⚠️  Start with 'false' to test in simulation mode!")
    trading = input("Enable real trading (y/N): ").lower()
    trading_enabled = "true" if trading == 'y' else "false"
    
    # Profit threshold
    print("\nMinimum profit threshold (percentage):")
    print("Recommended: 0.05 for micro-arbitrage, 0.1 for conservative")
    profit = input("Min profit threshold (default 0.05): ").strip() or "0.05"
    
    # Scan interval
    print("\nScan interval in seconds:")
    print("Recommended: 5 for active trading, 10 for conservative")
    interval = input("Scan interval (default 5): ").strip() or "5"
    
    return trading_enabled, profit, interval


def create_env_file(config):
    """Create .env file with configuration."""
    env_content = f"""# 🔐 SECURE WALLET CONFIGURATION
# Generated by setup_wallet.py
# NEVER commit this file to git!

# Wallet Configuration
WALLET_TYPE={config['wallet_type']}
WALLET_ADDRESS={config['wallet_address']}
"""

    if config.get('private_key'):
        env_content += f"PRIVATE_KEY={config['private_key']}\n"

    env_content += f"""
# Ethereum Node
ETHEREUM_RPC_URL={config['rpc_url']}

# Security Settings
MAX_GAS_PRICE_GWEI={config['max_gas']}
MAX_TRADE_SIZE_ETH={config['max_trade']}
REQUIRE_CONFIRMATION={config['require_confirmation']}

# Trading Settings
TRADING_ENABLED={config['trading_enabled']}
MIN_PROFIT_THRESHOLD={config['profit_threshold']}
SCAN_INTERVAL={config['scan_interval']}

# Optional API Keys (uncomment and fill in if you have them)
# ONEINCH_API_KEY=your_1inch_api_key_here
# DISCORD_WEBHOOK_URL=your_discord_webhook_url
"""

    with open('.env', 'w') as f:
        f.write(env_content)
    
    # Set secure permissions
    os.chmod('.env', 0o600)  # Read/write for owner only


def main():
    """Main setup function."""
    print_header()
    
    if not check_existing_config():
        return
    
    config = {}
    
    # Get wallet configuration
    config['wallet_type'] = get_wallet_type()
    config['wallet_address'] = get_wallet_address()
    
    if config['wallet_type'] == 'private_key':
        config['private_key'] = get_private_key()
        if not config['private_key']:
            print("Private key required for private_key wallet type.")
            return
    
    # Get network configuration
    config['rpc_url'] = get_rpc_url()
    
    # Get security settings
    config['max_gas'], config['max_trade'], config['require_confirmation'] = get_security_settings()
    
    # Get trading settings
    config['trading_enabled'], config['profit_threshold'], config['scan_interval'] = get_trading_settings()
    
    # Create .env file
    print("\n📝 CREATING CONFIGURATION FILE")
    create_env_file(config)
    
    print("\n✅ WALLET SETUP COMPLETE!")
    print("=" * 40)
    print("Configuration saved to .env file")
    print("File permissions set to 600 (owner read/write only)")
    print("\n🚀 NEXT STEPS:")
    print("1. Review your .env file")
    print("2. Test with small amounts first")
    print("3. Run: python src/real_arbitrage_bot.py")
    print("4. Monitor logs carefully")
    print("\n⚠️  SECURITY REMINDERS:")
    print("• Never share your .env file")
    print("• Never commit .env to git")
    print("• Start with small amounts")
    print("• Monitor all transactions")
    print("• Keep backups of your wallet")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\nSetup failed: {e}")
        sys.exit(1)
