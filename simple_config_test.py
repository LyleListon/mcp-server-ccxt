#!/usr/bin/env python3
"""Simple config test"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config.trading_config import CONFIG
    print(f"✅ SUCCESS! MIN_PROFIT: ${CONFIG.MIN_PROFIT_USD}")
    print(f"✅ MAX_TRADE: ${CONFIG.MAX_TRADE_USD}")
    print(f"✅ GAS_MULTIPLIER: {CONFIG.GAS_PRICE_MULTIPLIER}x")
    print("🎉 Centralized config is working!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
