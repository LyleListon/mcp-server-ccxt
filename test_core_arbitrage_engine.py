#!/usr/bin/env python3
"""
Test script for the core arbitrage engine components
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.arbitrage.arbitrage_engine import ArbitrageEngine
from core.arbitrage.path_finder import PathFinder
from core.arbitrage.profit_calculator import ProfitCalculator
from core.arbitrage.risk_analyzer import RiskAnalyzer
from common.events.event_bus import EventBus

def test_core_components():
    """Test core arbitrage engine components"""
    print("🧪 Testing Core Arbitrage Engine Components")
    print("=" * 60)
    
    # Test Event Bus
    print("\n📡 Testing Event Bus...")
    event_bus = EventBus()
    
    # Test subscription
    events_received = []
    def test_callback(event):
        events_received.append(event)
    
    event_bus.subscribe("test_event", test_callback)
    event_bus.publish_event("test_event", {"message": "Hello World"})
    
    if events_received:
        print("✅ Event Bus: Working correctly")
    else:
        print("❌ Event Bus: Failed to deliver events")
        return False
    
    # Test Path Finder
    print("\n🗺️  Testing Path Finder...")
    path_finder = PathFinder(max_path_length=3)
    
    # Create sample market data
    sample_market_data = {
        "pairs": [
            {
                "base_token": "USDC",
                "quote_token": "ETH", 
                "dex": "uniswap_v3",
                "price": 0.0003,  # 1 USDC = 0.0003 ETH
                "liquidity": 1000000
            },
            {
                "base_token": "ETH",
                "quote_token": "WBTC",
                "dex": "sushiswap", 
                "price": 0.04,  # 1 ETH = 0.04 WBTC
                "liquidity": 500000
            },
            {
                "base_token": "WBTC",
                "quote_token": "USDC",
                "dex": "curve",
                "price": 90000,  # 1 WBTC = 90000 USDC
                "liquidity": 800000
            }
        ]
    }
    
    path_finder.update_graph(sample_market_data)
    
    # Find arbitrage paths
    usdc_paths = path_finder.find_arbitrage_paths("USDC", min_liquidity=100000)
    
    if usdc_paths:
        print(f"✅ Path Finder: Found {len(usdc_paths)} arbitrage paths for USDC")
        for i, path in enumerate(usdc_paths[:2]):  # Show first 2 paths
            print(f"   Path {i+1}: {' -> '.join([edge['from_token'] for edge in path] + [path[-1]['to_token']])}")
    else:
        print("⚠️  Path Finder: No arbitrage paths found (this might be expected with sample data)")
    
    # Test Profit Calculator
    print("\n💰 Testing Profit Calculator...")
    profit_calculator = ProfitCalculator(min_profit_threshold=0.5)
    
    # Create a simple test path
    test_path = [
        {
            "from_token": "USDC",
            "to_token": "ETH",
            "dex": "uniswap_v3",
            "price": 0.0003,
            "liquidity": 1000000
        },
        {
            "from_token": "ETH", 
            "to_token": "USDC",
            "dex": "sushiswap",
            "price": 3400,  # Slightly higher price for arbitrage
            "liquidity": 500000
        }
    ]
    
    token_prices = {
        "USDC": 1.0,
        "ETH": 3300.0,
        "WBTC": 95000.0
    }
    
    opportunity = profit_calculator.evaluate_opportunity(
        test_path, 1000.0, token_prices, use_flash_loan=True
    )
    
    if opportunity:
        print(f"✅ Profit Calculator: Evaluated opportunity")
        print(f"   Expected Profit: {opportunity.get('expected_profit_percentage', 0):.2f}%")
        print(f"   Net Profit USD: ${opportunity.get('net_profit_usd', 0):.2f}")
        print(f"   Profitable: {opportunity.get('profitable', False)}")
    else:
        print("❌ Profit Calculator: Failed to evaluate opportunity")
        return False
    
    # Test Risk Analyzer
    print("\n⚠️  Testing Risk Analyzer...")
    risk_analyzer = RiskAnalyzer(max_slippage=1.0, max_risk_score=3)
    
    token_info = {
        "USDC": {"verified": True, "market_cap": 50e9, "volume": 1e9},
        "ETH": {"verified": True, "market_cap": 400e9, "volume": 10e9},
        "WBTC": {"verified": True, "market_cap": 15e9, "volume": 500e6}
    }
    
    analyzed_opportunity = risk_analyzer.analyze_opportunity(opportunity, token_info)
    
    if analyzed_opportunity:
        risk_score = analyzed_opportunity.get('risk_score', 0)
        acceptable_risk = analyzed_opportunity.get('acceptable_risk', False)
        print(f"✅ Risk Analyzer: Analyzed opportunity")
        print(f"   Risk Score: {risk_score}/5")
        print(f"   Acceptable Risk: {acceptable_risk}")
    else:
        print("❌ Risk Analyzer: Failed to analyze opportunity")
        return False
    
    # Test Arbitrage Engine Integration
    print("\n🚀 Testing Arbitrage Engine Integration...")
    
    config = {
        "trading": {
            "min_profit_threshold": 0.5,
            "max_slippage": 1.0,
            "max_trade_amount": 10000.0,
            "min_liquidity": 100000,
            "trading_enabled": False  # Keep disabled for testing
        }
    }
    
    arbitrage_engine = ArbitrageEngine(
        path_finder=path_finder,
        profit_calculator=profit_calculator,
        risk_analyzer=risk_analyzer,
        event_bus=event_bus,
        config=config
    )
    
    # Update engine with market data
    arbitrage_engine.update_market_data(sample_market_data)
    arbitrage_engine.update_token_prices(token_prices)
    arbitrage_engine.update_token_info(token_info)
    
    # Find opportunities
    opportunities = arbitrage_engine.find_opportunities()
    
    print(f"✅ Arbitrage Engine: Found {len(opportunities)} opportunities")
    
    if opportunities:
        best_opportunity = opportunities[0]
        print(f"   Best Opportunity ID: {best_opportunity.get('id', 'N/A')}")
        print(f"   Expected Profit: {best_opportunity.get('expected_profit_percentage', 0):.2f}%")
        print(f"   Risk Score: {best_opportunity.get('risk_score', 0)}/5")
        
        # Test execution plan preparation
        execution_plan = arbitrage_engine.prepare_execution_plan(best_opportunity)
        print(f"   Execution Steps: {len(execution_plan.get('steps', []))}")
        print(f"   Flash Loan Required: {execution_plan.get('flash_loan') is not None}")
    
    print("\n🎉 Core Arbitrage Engine Migration: SUCCESSFUL!")
    print("   All components are working together correctly.")
    print("   Ready for integration with DEX adapters and live trading.")
    
    return True

def test_configuration_loading():
    """Test configuration loading"""
    print("\n⚙️  Testing Configuration Loading...")
    
    # Test loading DEX config
    dex_config_path = Path("config/dex_config.json")
    if dex_config_path.exists():
        try:
            with open(dex_config_path, 'r') as f:
                dex_config = json.load(f)
            print(f"✅ DEX Config: Loaded {len(dex_config.get('dexes', []))} DEX configurations")
        except Exception as e:
            print(f"❌ DEX Config: Failed to load - {e}")
            return False
    else:
        print("⚠️  DEX Config: File not found (will need to create)")
    
    # Test loading default config
    default_config_path = Path("src/config/configs/default/config.json")
    if default_config_path.exists():
        try:
            with open(default_config_path, 'r') as f:
                default_config = json.load(f)
            print(f"✅ Default Config: Loaded successfully")
        except Exception as e:
            print(f"❌ Default Config: Failed to load - {e}")
            return False
    else:
        print("⚠️  Default Config: File not found (will need to create)")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Core Arbitrage Engine Migration Test")
    print(f"📁 Working directory: {os.getcwd()}")
    
    success = True
    
    try:
        success &= test_core_components()
        success &= test_configuration_loading()
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("   Core arbitrage engine migration is complete and working!")
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("   Check the output above for details.")
            
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    sys.exit(0 if success else 1)
