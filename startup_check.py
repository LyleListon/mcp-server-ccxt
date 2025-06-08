#!/usr/bin/env python3
'''
🚀 ARBITRAGE SYSTEM STARTUP CHECK
Run this before starting the arbitrage system to ensure no mock contamination.
'''

import os
import sys
import subprocess

def startup_check():
    '''Perform startup contamination check.'''
    
    print("🚀" * 20)
    print("🚀 ARBITRAGE SYSTEM STARTUP CHECK")
    print("🚀" * 20)
    
    # Check 1: Environment variables
    enable_real_tx = os.getenv('ENABLE_REAL_TRANSACTIONS', 'false')
    if enable_real_tx.lower() != 'true':
        print("❌ ENABLE_REAL_TRANSACTIONS not set to true")
        print("🔧 Run: export ENABLE_REAL_TRANSACTIONS=true")
        return False
    
    # Check 2: Run verification
    try:
        result = subprocess.run(['python', 'verify_real_execution.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ STARTUP CHECK PASSED!")
            print("🚀 System ready for real execution")
            print("💰 No mock data blocking profits")
            return True
        else:
            print("❌ STARTUP CHECK FAILED!")
            print(result.stdout)
            print("🔧 Fix contamination before starting arbitrage")
            return False
            
    except Exception as e:
        print(f"❌ Startup check error: {e}")
        return False

if __name__ == "__main__":
    if startup_check():
        print("\n🎯 READY TO START ARBITRAGE SYSTEM!")
        sys.exit(0)
    else:
        print("\n🚨 DO NOT START - FIX ISSUES FIRST!")
        sys.exit(1)
