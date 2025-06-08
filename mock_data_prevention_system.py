#!/usr/bin/env python3
"""
🛡️ MOCK DATA PREVENTION SYSTEM
Prevent mock data from contaminating the system again!
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import List, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock-prevention")

class MockDataDetector(FileSystemEventHandler):
    """Detect mock data contamination in real-time."""
    
    def __init__(self):
        self.mock_patterns = [
            r"0x[a]{64}",  # Fake transaction hashes
            r"0x[1]{64}",
            r"0x[f]{64}",
            r"await asyncio\.sleep\(",  # Simulation delays
            r"ENABLE_REAL_TRANSACTIONS.*false",
            r"Would trade|Would use|Would execute",
            r"mock|simulate|fake.*transaction",
            r"return.*#.*TODO.*Mock",
        ]
        
    def on_modified(self, event):
        """Check modified files for mock data."""
        if event.is_directory or not event.src_path.endswith('.py'):
            return
            
        self.scan_file(event.src_path)
        
    def scan_file(self, file_path: str):
        """Scan a single file for mock data patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            violations = []
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern in self.mock_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append({
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
            
            if violations:
                self.alert_mock_contamination(file_path, violations)
                
        except Exception as e:
            logger.debug(f"Could not scan {file_path}: {e}")
            
    def alert_mock_contamination(self, file_path: str, violations: List[Dict]):
        """Alert about mock data contamination."""
        
        logger.error("🚨" * 20)
        logger.error("🚨 MOCK DATA CONTAMINATION DETECTED!")
        logger.error(f"🚨 File: {file_path}")
        logger.error("🚨" * 20)
        
        for violation in violations:
            logger.error(f"   Line {violation['line']}: {violation['content']}")
            
        logger.error("💰 THIS WILL BLOCK REAL PROFITS!")
        logger.error("🔧 Fix immediately or run mock_data_exterminator.py")

class ProductionModeEnforcer:
    """Enforce production mode and prevent simulation code."""
    
    def __init__(self):
        self.production_checks = [
            self.check_environment_variables,
            self.check_critical_files,
            self.check_transaction_execution,
        ]
        
    def enforce_production_mode(self) -> bool:
        """Enforce production mode across the system."""
        
        logger.info("🛡️ ENFORCING PRODUCTION MODE...")
        
        all_checks_passed = True
        
        for check in self.production_checks:
            try:
                if not check():
                    all_checks_passed = False
            except Exception as e:
                logger.error(f"Production check failed: {e}")
                all_checks_passed = False
                
        if all_checks_passed:
            logger.info("✅ PRODUCTION MODE ENFORCED")
        else:
            logger.error("❌ PRODUCTION MODE VIOLATIONS DETECTED")
            
        return all_checks_passed
        
    def check_environment_variables(self) -> bool:
        """Check critical environment variables."""
        
        logger.info("🔍 Checking environment variables...")
        
        required_vars = {
            'ENABLE_REAL_TRANSACTIONS': 'true',
            'PRIVATE_KEY': None,  # Should exist but not check value
        }
        
        violations = []
        
        for var, expected_value in required_vars.items():
            actual_value = os.getenv(var)
            
            if actual_value is None:
                violations.append(f"{var} not set")
            elif expected_value and actual_value.lower() != expected_value:
                violations.append(f"{var}={actual_value} (should be {expected_value})")
                
        if violations:
            logger.error("❌ Environment variable violations:")
            for violation in violations:
                logger.error(f"   {violation}")
            return False
            
        logger.info("✅ Environment variables OK")
        return True
        
    def check_critical_files(self) -> bool:
        """Check critical files for production readiness."""
        
        logger.info("🔍 Checking critical files...")
        
        critical_files = [
            "src/execution/real_dex_executor.py",
            "src/execution/real_arbitrage_executor.py",
        ]
        
        violations = []
        
        for file_path in critical_files:
            if not Path(file_path).exists():
                violations.append(f"Missing critical file: {file_path}")
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Check for simulation patterns
                if "SAFETY MODE ACTIVE" in content:
                    violations.append(f"{file_path}: Still in safety mode")
                    
                if "Would trade" in content:
                    violations.append(f"{file_path}: Contains simulation warnings")
                    
                if "0x" + "a" * 64 in content:
                    violations.append(f"{file_path}: Contains fake transaction hashes")
                    
            except Exception as e:
                violations.append(f"Could not check {file_path}: {e}")
                
        if violations:
            logger.error("❌ Critical file violations:")
            for violation in violations:
                logger.error(f"   {violation}")
            return False
            
        logger.info("✅ Critical files OK")
        return True
        
    def check_transaction_execution(self) -> bool:
        """Check if transaction execution is properly configured."""
        
        logger.info("🔍 Checking transaction execution configuration...")
        
        # This would integrate with your actual transaction execution
        # For now, just check environment
        
        enable_real_tx = os.getenv('ENABLE_REAL_TRANSACTIONS', 'false').lower()
        
        if enable_real_tx != 'true':
            logger.error("❌ Real transactions not enabled")
            return False
            
        logger.info("✅ Transaction execution OK")
        return True

def start_mock_data_monitoring():
    """Start real-time mock data monitoring."""
    
    logger.info("🛡️ Starting mock data prevention system...")
    
    # Setup file monitoring
    event_handler = MockDataDetector()
    observer = Observer()
    
    # Monitor key directories
    monitor_paths = ['src/', 'contracts/', '.']
    
    for path in monitor_paths:
        if Path(path).exists():
            observer.schedule(event_handler, path, recursive=True)
            logger.info(f"📁 Monitoring {path} for mock data contamination")
    
    observer.start()
    
    # Setup production mode enforcement
    enforcer = ProductionModeEnforcer()
    
    try:
        logger.info("🚀 Mock data prevention system active!")
        logger.info("🛡️ Will alert on any mock data contamination")
        
        while True:
            # Periodic production mode checks
            time.sleep(300)  # Check every 5 minutes
            enforcer.enforce_production_mode()
            
    except KeyboardInterrupt:
        logger.info("🛑 Stopping mock data prevention system")
        observer.stop()
        
    observer.join()

def main():
    """Run the mock data prevention system."""
    
    print("🛡️" * 20)
    print("🛡️ MOCK DATA PREVENTION SYSTEM")
    print("🛡️" * 20)
    
    # Initial production mode check
    enforcer = ProductionModeEnforcer()
    if enforcer.enforce_production_mode():
        print("✅ System is in production mode")
        print("🛡️ Starting real-time monitoring...")
        start_mock_data_monitoring()
    else:
        print("❌ System not ready for production")
        print("🔧 Fix violations before starting monitoring")

if __name__ == "__main__":
    main()
