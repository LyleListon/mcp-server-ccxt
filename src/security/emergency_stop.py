"""
Emergency Stop Mechanism

Simple kill switch for the arbitrage system.
Create EMERGENCY_STOP file to halt all trading immediately.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class EmergencyStop:
    """Emergency stop mechanism for arbitrage system."""
    
    def __init__(self, stop_file_path: str = "EMERGENCY_STOP"):
        """Initialize emergency stop checker."""
        self.stop_file_path = Path(stop_file_path)
        self.last_check_result = False
    
    def is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is active."""
        try:
            # Check if emergency stop file exists
            if self.stop_file_path.exists():
                if not self.last_check_result:
                    # First time detecting stop
                    logger.critical("🚨 EMERGENCY STOP ACTIVATED! Trading halted.")
                    logger.critical(f"🚨 Stop file found: {self.stop_file_path}")
                    
                    # Read reason if provided
                    try:
                        reason = self.stop_file_path.read_text().strip()
                        if reason:
                            logger.critical(f"🚨 Reason: {reason}")
                    except:
                        pass
                
                self.last_check_result = True
                return True
            else:
                if self.last_check_result:
                    # Emergency stop was cleared
                    logger.info("✅ Emergency stop cleared. Trading can resume.")
                
                self.last_check_result = False
                return False
                
        except Exception as e:
            logger.error(f"Emergency stop check error: {e}")
            # Fail safe - if we can't check, assume stop is active
            return True
    
    def activate_emergency_stop(self, reason: str = "Manual activation"):
        """Activate emergency stop."""
        try:
            self.stop_file_path.write_text(f"Emergency stop activated: {reason}")
            logger.critical(f"🚨 EMERGENCY STOP ACTIVATED: {reason}")
        except Exception as e:
            logger.error(f"Failed to activate emergency stop: {e}")
    
    def clear_emergency_stop(self):
        """Clear emergency stop."""
        try:
            if self.stop_file_path.exists():
                self.stop_file_path.unlink()
                logger.info("✅ Emergency stop cleared")
            else:
                logger.info("ℹ️  Emergency stop was not active")
        except Exception as e:
            logger.error(f"Failed to clear emergency stop: {e}")

# Global emergency stop instance
emergency_stop = EmergencyStop()

def check_emergency_stop() -> bool:
    """Quick function to check emergency stop status."""
    return emergency_stop.is_emergency_stop_active()

def activate_emergency_stop(reason: str = "Manual activation"):
    """Quick function to activate emergency stop."""
    emergency_stop.activate_emergency_stop(reason)

def clear_emergency_stop():
    """Quick function to clear emergency stop."""
    emergency_stop.clear_emergency_stop()
