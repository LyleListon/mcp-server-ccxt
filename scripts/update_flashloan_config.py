#!/usr/bin/env python3
"""
🔧 UPDATE FLASHLOAN CONFIGURATION
Updates the arbitrage system to use the new fixed flashloan contract
"""

import os
import json
import sys

def update_flashloan_executor():
    """Update the flashloan executor configuration"""
    print("🔧 Updating flashloan executor configuration...")
    
    # Load deployment info
    if not os.path.exists('deployment_info.json'):
        print("❌ deployment_info.json not found. Deploy contract first.")
        return False
    
    with open('deployment_info.json', 'r') as f:
        deployment_info = json.load(f)
    
    new_contract_address = deployment_info['contract_address']
    print(f"📍 New contract address: {new_contract_address}")
    
    # Update flashloan executor file
    executor_file = 'src/execution/flashloan_arbitrage_executor.py'
    
    if os.path.exists(executor_file):
        with open(executor_file, 'r') as f:
            content = f.read()
        
        # Replace old contract address with new one
        old_address = "0x7E6BD347cd7C671d57F843879f4654fA3Ca0665A"  # Current failing contract
        
        if old_address in content:
            updated_content = content.replace(old_address, new_contract_address)
            
            with open(executor_file, 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Updated {executor_file}")
            print(f"🔄 Changed {old_address} → {new_contract_address}")
        else:
            print(f"⚠️  Old contract address not found in {executor_file}")
            print("Manual update may be required")
    else:
        print(f"❌ {executor_file} not found")
        return False
    
    return True

def update_config_files():
    """Update configuration files"""
    print("🔧 Updating configuration files...")
    
    # Load deployment info
    with open('deployment_info.json', 'r') as f:
        deployment_info = json.load(f)
    
    new_contract_address = deployment_info['contract_address']
    
    # Update main config
    config_files = [
        'config/arbitrage_config.json',
        'config/flashloan_config.json',
        'src/config/config.py'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            if config_file.endswith('.json'):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Update contract address
                config['flashloan_contract_address'] = new_contract_address
                config['flashloan_version'] = 'FixedFlashloanArbitrage_v2'
                
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print(f"✅ Updated {config_file}")
            
            elif config_file.endswith('.py'):
                with open(config_file, 'r') as f:
                    content = f.read()
                
                # Replace contract address in Python config
                old_address = "0x7E6BD347cd7C671d57F843879f4654fA3Ca0665A"
                if old_address in content:
                    updated_content = content.replace(old_address, new_contract_address)
                    
                    with open(config_file, 'w') as f:
                        f.write(updated_content)
                    
                    print(f"✅ Updated {config_file}")
        else:
            print(f"⚠️  {config_file} not found")

def create_backup():
    """Create backup of old configuration"""
    print("💾 Creating backup of old configuration...")
    
    import shutil
    import time
    
    timestamp = int(time.time())
    backup_dir = f"backup/config_backup_{timestamp}"
    
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'src/execution/flashloan_arbitrage_executor.py',
        'config/arbitrage_config.json',
        'config/flashloan_config.json'
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_dir)
            print(f"📁 Backed up {file_path}")
    
    print(f"✅ Backup created in {backup_dir}")

def verify_update():
    """Verify the configuration update"""
    print("🔍 Verifying configuration update...")
    
    # Load deployment info
    with open('deployment_info.json', 'r') as f:
        deployment_info = json.load(f)
    
    expected_address = deployment_info['contract_address']
    
    # Check flashloan executor
    executor_file = 'src/execution/flashloan_arbitrage_executor.py'
    if os.path.exists(executor_file):
        with open(executor_file, 'r') as f:
            content = f.read()
        
        if expected_address in content:
            print("✅ Flashloan executor updated correctly")
        else:
            print("❌ Flashloan executor not updated")
            return False
    
    # Check config files
    config_file = 'config/arbitrage_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if config.get('flashloan_contract_address') == expected_address:
            print("✅ Configuration files updated correctly")
        else:
            print("❌ Configuration files not updated")
            return False
    
    print("✅ All configurations verified!")
    return True

def main():
    """Main update process"""
    print("🔧 FLASHLOAN CONFIGURATION UPDATE")
    print("=================================")
    
    try:
        # Create backup first
        create_backup()
        
        # Update flashloan executor
        if not update_flashloan_executor():
            print("❌ Failed to update flashloan executor")
            return False
        
        # Update config files
        update_config_files()
        
        # Verify updates
        if verify_update():
            print("\n🎉 CONFIGURATION UPDATE COMPLETE!")
            print("✅ All files updated successfully")
            print("🔄 System ready to use new contract")
            print("⚡ Restart arbitrage system to apply changes")
            return True
        else:
            print("❌ Configuration verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Update error: {e}")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
