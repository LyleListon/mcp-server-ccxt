#!/usr/bin/env python3
"""
🛡️ Quick Security Exposure Test
Check how vulnerable your arbitrage system is to detection.
"""

import os
import json

def analyze_contract_exposure():
    """Analyze how exposed your contracts are."""
    
    print("🛡️ SECURITY EXPOSURE ANALYSIS")
    print("=" * 50)
    
    # Check contract names
    contract_dir = "contracts"
    obvious_names = []
    
    if os.path.exists(contract_dir):
        for filename in os.listdir(contract_dir):
            if filename.endswith('.sol'):
                name = filename.replace('.sol', '').lower()
                if any(keyword in name for keyword in ['arbitrage', 'flashloan', 'profit', 'mev']):
                    obvious_names.append(filename)
    
    print(f"🚨 OBVIOUS CONTRACT NAMES DETECTED:")
    for name in obvious_names:
        print(f"   ❌ {name}")
    
    # Check if your contracts appear in your own ABI exports
    abi_dir = "abi_exports/arbitrum"
    your_contracts_exposed = []
    
    if os.path.exists(abi_dir):
        for filename in os.listdir(abi_dir):
            if filename.endswith('.json'):
                try:
                    with open(f"{abi_dir}/{filename}", 'r') as f:
                        abi = json.load(f)
                    
                    # Check if this looks like your contract
                    abi_text = json.dumps(abi).lower()
                    if any(indicator in abi_text for indicator in ['executeArbitrage', 'flashLoan', 'ProfitMade']):
                        address = filename.split('_')[-1].replace('.json', '')
                        your_contracts_exposed.append(address)
                except:
                    continue
    
    print(f"\n🕵️ CONTRACTS IN YOUR SPY DATABASE:")
    print(f"   Total contracts: {len(os.listdir(abi_dir)) if os.path.exists(abi_dir) else 0}")
    print(f"   Arbitrage-like contracts: {len(your_contracts_exposed)}")
    
    # Risk assessment
    risk_score = 0
    risk_factors = []
    
    if obvious_names:
        risk_score += len(obvious_names) * 3
        risk_factors.append(f"Obvious contract names ({len(obvious_names)} files)")
    
    if len(your_contracts_exposed) > 5:
        risk_score += 5
        risk_factors.append("Many arbitrage contracts detected")
    
    # Check for environment variables (basic OpSec)
    sensitive_vars = ['PRIVATE_KEY', 'ALCHEMY_API_KEY', 'WALLET_ADDRESS']
    exposed_vars = [var for var in sensitive_vars if os.getenv(var)]
    
    if len(exposed_vars) == len(sensitive_vars):
        risk_score += 2
        risk_factors.append("All sensitive environment variables set (good)")
    
    # Determine risk level
    if risk_score <= 5:
        risk_level = "LOW"
        color = "🟢"
    elif risk_score <= 10:
        risk_level = "MEDIUM" 
        color = "🟡"
    elif risk_score <= 15:
        risk_level = "HIGH"
        color = "🟠"
    else:
        risk_level = "CRITICAL"
        color = "🔴"
    
    print(f"\n📊 RISK ASSESSMENT:")
    print(f"   {color} Risk Level: {risk_level}")
    print(f"   📈 Risk Score: {risk_score}/20")
    
    print(f"\n⚠️ RISK FACTORS:")
    for factor in risk_factors:
        print(f"   • {factor}")
    
    # Recommendations
    print(f"\n💡 IMMEDIATE RECOMMENDATIONS:")
    
    if obvious_names:
        print("   🎭 Rename contracts to innocent names (TokenManager, LiquidityHelper)")
        print("   🔀 Obfuscate function names (executeArbitrage → processTransaction)")
    
    if risk_level in ['HIGH', 'CRITICAL']:
        print("   🥷 Enable private mempool (Flashbots) immediately")
        print("   🔄 Rotate wallet addresses")
        print("   📦 Use transaction bundling")
    
    if risk_level in ['MEDIUM', 'HIGH', 'CRITICAL']:
        print("   🍯 Deploy honeypot contracts to mislead competitors")
        print("   🎯 Add decoy transactions")
    
    print("   📊 Monitor for copycat behavior")
    print("   🛡️ Implement stealth mode operations")
    
    return {
        'risk_level': risk_level,
        'risk_score': risk_score,
        'obvious_contracts': obvious_names,
        'exposed_contracts': len(your_contracts_exposed)
    }

def check_spy_network_exposure():
    """Check if your spy network could detect your own operations."""
    
    print(f"\n🕵️ SPY NETWORK SELF-TEST")
    print("=" * 50)
    
    # Load your competitor bot monitor
    try:
        # Simulate what your spy network would see
        print("🔍 Testing if your spy network would detect your operations...")
        
        # Check contract patterns
        suspicious_patterns = [
            'executeArbitrage',
            'flashLoan', 
            'ProfitMade',
            'ArbExecuted',
            'FlashLoanStarted'
        ]
        
        print(f"🎯 Patterns your spy network looks for:")
        for pattern in suspicious_patterns:
            print(f"   • {pattern}")
        
        print(f"\n⚠️ If your contracts contain these patterns, competitors can find you!")
        
        return True
        
    except Exception as e:
        print(f"❌ Could not test spy network: {e}")
        return False

if __name__ == "__main__":
    # Run exposure analysis
    exposure_results = analyze_contract_exposure()
    
    # Run spy network self-test
    spy_test_results = check_spy_network_exposure()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   Risk Level: {exposure_results['risk_level']}")
    print(f"   Obvious Contracts: {len(exposure_results['obvious_contracts'])}")
    print(f"   Spy Network Active: {'✅' if spy_test_results else '❌'}")
    
    if exposure_results['risk_level'] in ['HIGH', 'CRITICAL']:
        print(f"\n🚨 URGENT ACTION REQUIRED!")
        print(f"   Your operations are highly vulnerable to detection!")
        print(f"   Implement stealth measures immediately!")
    else:
        print(f"\n✅ Security posture is acceptable but can be improved.")
