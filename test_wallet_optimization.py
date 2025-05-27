#!/usr/bin/env python3
"""
Wallet Optimization Test
Tests smart wallet management for your $675 USDC wallet.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from wallet.smart_wallet_manager import SmartWalletManager

async def test_wallet_optimization():
    """Test wallet optimization for your current $675 USDC setup."""
    print("💰 Smart Wallet Optimization Test")
    print("=" * 60)
    print("🎯 Optimizing your $675 USDC wallet for maximum arbitrage")
    print("🔄 Automatic token swapping and rebalancing")
    print("⚡ Dynamic optimization for opportunities")
    print("=" * 60)
    
    # Load config
    with open('config/capital_efficient_config.json', 'r') as f:
        config = json.load(f)
    
    # Initialize wallet manager
    print("\n🔌 Initializing Smart Wallet Manager...")
    
    wallet_manager = SmartWalletManager(config)
    
    # Your wallet address (simulated)
    wallet_address = "0x1234567890123456789012345678901234567890"
    
    print("✅ Smart Wallet Manager Ready!")
    
    # Analyze current wallet composition
    print(f"\n📊 Analyzing Your Current Wallet ($675)...")
    
    wallet_status = await wallet_manager.get_wallet_status(wallet_address)
    
    if 'error' in wallet_status:
        print(f"❌ Error: {wallet_status['error']}")
        return False
    
    print(f"   Total Value: ${wallet_status['total_value_usd']:,.2f}")
    print(f"   Current Composition:")
    
    for token, analysis in wallet_status['composition_analysis'].items():
        status_icon = "✅" if analysis['status'] == 'optimal' else "⚠️"
        print(f"      {status_icon} {token}: ${analysis['current_usd']:.2f} ({analysis['current_percentage']:.1f}%)")
        print(f"         Target: {analysis['target_percentage']:.1f}%, Difference: {analysis['difference']:+.1f}%")
    
    # Show rebalancing recommendation
    if wallet_status['rebalance_needed']:
        print(f"\n🔄 Rebalancing Needed!")
        
        rebalance_plan = await wallet_manager.generate_rebalancing_plan(wallet_address)
        
        if 'error' not in rebalance_plan:
            print(f"   Estimated Cost: ${rebalance_plan['estimated_gas_cost']:.2f} gas")
            print(f"   Estimated Time: {rebalance_plan['estimated_time_minutes']} minutes")
            print(f"   Swap Plan:")
            
            for swap in rebalance_plan['swap_plan']:
                action_icon = "🟢" if swap['action'] == 'buy' else "🔴"
                print(f"      {action_icon} {swap['action'].upper()} ${swap['amount_usd']:.0f} {swap['token']}")
            
            print(f"\n   Target Composition After Rebalancing:")
            for token, target_balance in rebalance_plan['target_balances'].items():
                target_pct = (target_balance / wallet_status['total_value_usd']) * 100
                print(f"      {token}: ${target_balance:.2f} ({target_pct:.1f}%)")
    else:
        print(f"\n✅ Wallet composition is optimal!")
    
    # Test opportunity-specific optimization
    print(f"\n🎯 Testing Opportunity-Specific Optimization...")
    
    test_opportunities = [
        {
            'name': 'ETH Cross-Chain Arbitrage',
            'token': 'ETH',
            'estimated_trade_size': 300,
            'profit_percentage': 0.8
        },
        {
            'name': 'USDT Stablecoin Arbitrage',
            'token': 'USDT',
            'estimated_trade_size': 500,
            'profit_percentage': 0.4
        },
        {
            'name': 'Large USDC Arbitrage',
            'token': 'USDC',
            'estimated_trade_size': 800,
            'profit_percentage': 0.6
        }
    ]
    
    for opportunity in test_opportunities:
        print(f"\n   🧪 {opportunity['name']}")
        print(f"      Token: {opportunity['token']}, Size: ${opportunity['estimated_trade_size']}")
        
        optimization = await wallet_manager.optimize_for_opportunity(opportunity, wallet_address)
        
        if optimization.get('optimization_needed'):
            if 'error' in optimization:
                print(f"      ❌ {optimization['error']}")
            else:
                swap_plan = optimization['swap_plan']
                print(f"      🔄 Optimization needed:")
                print(f"         Swap ${swap_plan['amount_usd']:.0f} {swap_plan['from_token']} → {swap_plan['to_token']}")
                print(f"         Cost: ${swap_plan['estimated_gas_cost']:.2f}, Time: {swap_plan['estimated_time_minutes']} min")
        else:
            print(f"      ✅ {optimization['message']}")
    
    # Show wallet recommendations
    print(f"\n💡 Wallet Optimization Recommendations:")
    
    for rec in wallet_status['recommendations']:
        print(f"   📋 {rec['type'].title()}: {rec['message']}")
        if 'suggested_composition' in rec:
            print(f"      Suggested composition:")
            for token, pct in rec['suggested_composition'].items():
                amount = wallet_status['total_value_usd'] * pct
                print(f"         {token}: ${amount:.0f} ({pct*100:.0f}%)")
    
    # Simulate rebalancing execution
    print(f"\n🚀 Simulating Wallet Rebalancing...")
    
    if wallet_status['rebalance_needed']:
        print("   Executing rebalancing plan...")
        
        # Simulate private key (don't use real one in test!)
        fake_private_key = "0x" + "0" * 64
        
        rebalance_result = await wallet_manager.execute_rebalancing(wallet_address, fake_private_key)
        
        if rebalance_result.get('success'):
            print(f"   ✅ Rebalancing successful!")
            print(f"      Swaps executed: {rebalance_result['swaps_executed']}")
            print(f"      Total gas cost: ${rebalance_result['total_gas_cost']:.2f}")
            
            # Show new composition
            new_composition = rebalance_result['new_composition']
            print(f"      New composition:")
            for token, analysis in new_composition['composition_analysis'].items():
                print(f"         {token}: ${analysis['current_usd']:.2f} ({analysis['current_percentage']:.1f}%)")
        else:
            print(f"   ❌ Rebalancing failed: {rebalance_result.get('error')}")
    else:
        print("   No rebalancing needed - wallet is optimal!")
    
    # Calculate arbitrage readiness score
    print(f"\n📊 Arbitrage Readiness Analysis:")
    
    readiness_score = 0
    max_score = 100
    
    # Token diversity (40 points)
    token_count = len([b for b in wallet_status['current_balances'].values() if b > 10])
    diversity_score = min(40, token_count * 10)
    readiness_score += diversity_score
    print(f"   Token Diversity: {diversity_score}/40 ({token_count} tokens with >$10)")
    
    # Composition balance (30 points)
    composition_score = 30
    for token, analysis in wallet_status['composition_analysis'].items():
        if analysis['difference'] > 15:  # >15% off target
            composition_score -= 5
    composition_score = max(0, composition_score)
    readiness_score += composition_score
    print(f"   Composition Balance: {composition_score}/30")
    
    # Liquidity (20 points)
    eth_balance = wallet_status['current_balances'].get('ETH', 0)
    liquidity_score = min(20, (eth_balance / 100) * 20)  # 20 points for $100+ ETH
    readiness_score += liquidity_score
    print(f"   ETH Liquidity: {liquidity_score:.0f}/20 (${eth_balance:.0f} ETH)")
    
    # Stable base (10 points)
    stable_balance = (wallet_status['current_balances'].get('USDC', 0) + 
                     wallet_status['current_balances'].get('USDT', 0) + 
                     wallet_status['current_balances'].get('DAI', 0))
    stable_score = min(10, (stable_balance / 300) * 10)  # 10 points for $300+ stables
    readiness_score += stable_score
    print(f"   Stable Base: {stable_score:.0f}/10 (${stable_balance:.0f} stables)")
    
    print(f"\n🎯 Overall Arbitrage Readiness: {readiness_score:.0f}/100")
    
    if readiness_score >= 80:
        print(f"   🚀 EXCELLENT - Ready for aggressive arbitrage!")
    elif readiness_score >= 60:
        print(f"   ✅ GOOD - Ready for moderate arbitrage")
    elif readiness_score >= 40:
        print(f"   ⚠️  FAIR - Consider rebalancing first")
    else:
        print(f"   ❌ POOR - Rebalancing strongly recommended")
    
    # Specific recommendations for your $675 wallet
    print(f"\n🎯 Specific Recommendations for Your $675 Wallet:")
    
    current_usdc = wallet_status['current_balances'].get('USDC', 0)
    current_eth = wallet_status['current_balances'].get('ETH', 0)
    
    print(f"   Current: ${current_usdc:.0f} USDC, ${current_eth:.0f} ETH")
    print(f"   Recommended immediate actions:")
    
    if current_usdc > 500:
        eth_to_buy = 675 * 0.3 - current_eth  # Target 30% ETH
        print(f"   1. 🔄 Swap ${eth_to_buy:.0f} USDC → ETH (for cross-chain opportunities)")
    
    if wallet_status['current_balances'].get('USDT', 0) < 50:
        print(f"   2. 🔄 Swap $100 USDC → USDT (for stablecoin arbitrage)")
    
    print(f"   3. ⚡ Start with $200-400 trade sizes")
    print(f"   4. 📈 Scale up as profits accumulate")
    print(f"   5. 🔄 Rebalance weekly or after major profits")
    
    print(f"\n🎉 Wallet Optimization Test Complete!")
    print(f"   Your $675 is ready for arbitrage with minor optimization!")
    
    return True

async def main():
    """Main test function."""
    try:
        success = await test_wallet_optimization()
        return success
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
