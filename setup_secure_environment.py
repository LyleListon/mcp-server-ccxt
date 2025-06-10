#!/usr/bin/env python3
"""
🔐 SECURE ENVIRONMENT SETUP
Set up environment variables securely without .env files

This script helps you set up environment variables properly
without the security risks of .env files.
"""

import os
import subprocess
import getpass
from pathlib import Path

def colored_print(text, color_code):
 """Print colored text."""
 print(f"\033[{color_code}m{text}\033[0m")

def check_current_env():
 """Check what environment variables are currently set."""
 colored_print("🔍 CHECKING CURRENT ENVIRONMENT VARIABLES", "1;36")
 print("=" * 60)
 
 required_vars = [
 'ALCHEMY_API_KEY',
 'WALLET_PRIVATE_KEY',
 'PRIVATE_KEY',
 'WALLET_ADDRESS',
 'GECKO_KEY',
 'ENABLE_REAL_TRANSACTIONS',
 'ETHEREUM_NODE_URL'
 ]
 
 set_vars = []
 missing_vars = []
 
 for var in required_vars:
 value = os.getenv(var)
 if value:
 set_vars.append(var)
 if 'KEY' in var or 'PRIVATE' in var:
 colored_print(f"✅ {var}: {'*' * 20}", "1;32")
 else:
 colored_print(f"✅ {var}: {value[:20]}...", "1;32")
 else:
 missing_vars.append(var)
 colored_print(f"❌ {var}: Not set", "1;31")
 
 print(f"\n📊 SUMMARY:")
 colored_print(f" ✅ Set: {len(set_vars)}/{len(required_vars)}", "1;32")
 colored_print(f" ❌ Missing: {len(missing_vars)}/{len(required_vars)}", "1;31")
 
 return set_vars, missing_vars

def setup_bashrc_variables():
 """Set up environment variables in ~/.bashrc for persistence."""
 colored_print("\n🔧 SETTING UP PERSISTENT ENVIRONMENT VARIABLES", "1;36")
 print("=" * 60)
 
 bashrc_path = Path.home() / '.bashrc'
 
 print("This will add environment variables to your ~/.bashrc file")
 print("They will be available every time you open a terminal.")
 print()
 
 # Check if we already have a MayArbi section
 if bashrc_path.exists():
 with open(bashrc_path, 'r') as f:
 content = f.read()
 if '# MayArbi Environment Variables' in content:
 colored_print("⚠️ MayArbi variables already exist in ~/.bashrc", "1;33")
 response = input("Do you want to update them? (y/n): ")
 if response.lower() != 'y':
 return False
 
 # Collect environment variables
 env_vars = {}
 
 print("\n🔑 ENTER YOUR SECURE CREDENTIALS:")
 print("(Leave blank to skip, press Ctrl+C to cancel)")
 print()
 
 # Wallet Private Key
 if not os.getenv('WALLET_PRIVATE_KEY') and not os.getenv('PRIVATE_KEY'):
 private_key = getpass.getpass("🔐 Wallet Private Key (hidden): ")
 if private_key:
 env_vars['WALLET_PRIVATE_KEY'] = private_key
 env_vars['PRIVATE_KEY'] = private_key # Some scripts use this name
 
 # Wallet Address
 if not os.getenv('WALLET_ADDRESS'):
 wallet_address = input("📍 Wallet Address (0x...): ")
 if wallet_address:
 env_vars['WALLET_ADDRESS'] = wallet_address
 
 # Alchemy API Key
 if not os.getenv('ALCHEMY_API_KEY'):
 alchemy_key = getpass.getpass("🔑 Alchemy API Key (hidden): ")
 if alchemy_key:
 env_vars['ALCHEMY_API_KEY'] = alchemy_key
 
 # CoinGecko API Key (you already have this one)
 if not os.getenv('GECKO_KEY'):
 gecko_key = input("🦎 CoinGecko API Key (CG-w6zYkP9CY5m3Nc1ZJdboDcpC): ")
 if not gecko_key:
 gecko_key = "CG-w6zYkP9CY5m3Nc1ZJdboDcpC" # Your existing key
 env_vars['GECKO_KEY'] = gecko_key
 
 # Ethereum Node URL
 if not os.getenv('ETHEREUM_NODE_URL'):
 node_url = input("🌐 Ethereum Node URL (ws://192.168.1.18:8546): ")
 if not node_url:
 node_url = "ws://192.168.1.18:8546" # Your existing node
 env_vars['ETHEREUM_NODE_URL'] = node_url
 
 # Trading Configuration
 if not os.getenv('ENABLE_REAL_TRANSACTIONS'):
 env_vars['ENABLE_REAL_TRANSACTIONS'] = 'true'
 
 if not os.getenv('MAX_TRADE_SIZE_USD'):
 env_vars['MAX_TRADE_SIZE_USD'] = '500'
 
 if not os.getenv('MIN_PROFIT_USD'):
 env_vars['MIN_PROFIT_USD'] = '10'
 
 if not env_vars:
 colored_print("ℹ️ No new variables to add", "1;33")
 return True
 
 # Create backup
 if bashrc_path.exists():
 backup_path = bashrc_path.with_suffix('.bashrc.backup')
 subprocess.run(['cp', str(bashrc_path), str(backup_path)])
 colored_print(f"💾 Backup created: {backup_path}", "1;33")
 
 # Add variables to bashrc
 with open(bashrc_path, 'a') as f:
 f.write('\n# MayArbi Environment Variables\n')
 f.write('# Added by setup_secure_environment.py\n')
 for key, value in env_vars.items():
 f.write(f'export {key}="{value}"\n')
 f.write('\n')
 
 colored_print("✅ Environment variables added to ~/.bashrc", "1;32")
 
 # Source the bashrc
 colored_print("🔄 Reloading environment...", "1;36")
 
 # Set in current session
 for key, value in env_vars.items():
 os.environ[key] = value
 
 colored_print("✅ Environment variables loaded in current session", "1;32")
 
 return True

def verify_setup():
 """Verify the environment setup is working."""
 colored_print("\n✅ VERIFYING SETUP", "1;36")
 print("=" * 60)
 
 # Check critical variables
 critical_vars = ['WALLET_PRIVATE_KEY', 'ALCHEMY_API_KEY', 'ENABLE_REAL_TRANSACTIONS']
 
 all_good = True
 for var in critical_vars:
 value = os.getenv(var)
 if value:
 if 'KEY' in var:
 colored_print(f"✅ {var}: Set (hidden)", "1;32")
 else:
 colored_print(f"✅ {var}: {value}", "1;32")
 else:
 colored_print(f"❌ {var}: Missing", "1;31")
 all_good = False
 
 if all_good:
 colored_print("\n SETUP COMPLETE! Your environment is ready for trading!", "1;32")
 print("\n📋 NEXT STEPS:")
 print(" 1. Open a new terminal (or run: source ~/.bashrc)")
 print(" 2. Run your trading system")
 print(" 3. Environment variables will persist across reboots")
 print("\n🔐 SECURITY NOTES:")
 print(" ✅ No .env files created")
 print(" ✅ Variables stored in ~/.bashrc (secure)")
 print(" ✅ Private keys never displayed")
 print(" ✅ Safe from accidental Git commits")
 else:
 colored_print("\n⚠️ SETUP INCOMPLETE", "1;33")
 print("Some required variables are still missing.")
 print("Run this script again to complete setup.")
 
 return all_good

def show_usage_examples():
 """Show examples of how to use the environment variables."""
 colored_print("\n📚 USAGE EXAMPLES", "1;36")
 print("=" * 60)
 
 print("Your trading scripts will automatically use these variables:")
 print()
 print("🐍 Python code:")
 print(" import os")
 print(" api_key = os.getenv('ALCHEMY_API_KEY')")
 print(" private_key = os.getenv('WALLET_PRIVATE_KEY')")
 print()
 print("🔧 Manual export (if needed):")
 print(" export ENABLE_REAL_TRANSACTIONS=true")
 print(" export MAX_TRADE_SIZE_USD=500")
 print()
 print("🔍 Check variables:")
 print(" echo $ALCHEMY_API_KEY")
 print(" env | grep WALLET")

def main():
 """Main setup function."""
 colored_print("🔐 MAYARBI SECURE ENVIRONMENT SETUP", "1;35")
 colored_print("=" * 60, "1;35")
 print("This script helps you set up environment variables securely")
 print("without the risks of .env files being committed to Git.")
 print()
 
 # Check current environment
 set_vars, missing_vars = check_current_env()
 
 if not missing_vars:
 colored_print("\n ALL ENVIRONMENT VARIABLES ARE ALREADY SET!", "1;32")
 verify_setup()
 show_usage_examples()
 return
 
 print(f"\n⚠️ Found {len(missing_vars)} missing variables")
 response = input("Do you want to set them up now? (y/n): ")
 
 if response.lower() == 'y':
 if setup_bashrc_variables():
 verify_setup()
 show_usage_examples()
 else:
 colored_print("ℹ️ Setup cancelled", "1;33")
 print("Run this script again when you're ready to set up your environment.")

if __name__ == "__main__":
 try:
 main()
 except KeyboardInterrupt:
 colored_print("\n\n🛑 Setup cancelled by user", "1;33")
 except Exception as e:
 colored_print(f"\n❌ Setup failed: {e}", "1;31")
 print("Please check the error and try again.")
