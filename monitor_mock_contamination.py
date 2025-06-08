#!/usr/bin/env python3
'''
🔍 CONTINUOUS MOCK DATA MONITORING
Run this to continuously monitor for mock data contamination.
'''

import time
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-monitor")

def check_for_contamination():
    '''Check for mock data contamination.'''
    try:
        result = subprocess.run(['python', 'verify_real_execution.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ System clean - no mock contamination")
            return True
        else:
            logger.error("❌ MOCK CONTAMINATION DETECTED!")
            logger.error(result.stdout)
            return False
            
    except Exception as e:
        logger.error(f"Monitor check failed: {e}")
        return False

def main():
    '''Run continuous monitoring.'''
    logger.info("🛡️ Starting continuous mock data monitoring...")
    logger.info("🔍 Checking every 5 minutes for contamination")
    
    while True:
        try:
            if not check_for_contamination():
                logger.error("🚨 IMMEDIATE ACTION REQUIRED!")
                logger.error("🔧 Run: python fix_mock_data_contamination.py")
                
            time.sleep(300)  # Check every 5 minutes
            
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped")
            break

if __name__ == "__main__":
    main()
