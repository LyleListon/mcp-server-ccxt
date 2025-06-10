#!/usr/bin/env python3
"""
 MOCK DATA EXTERMINATOR
Hunt down and DESTROY every last piece of mock data contamination!

This is your FINAL BOSS BATTLE against mock data!
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EXTERMINATOR")

class MockDataExterminator:
 """The ultimate mock data hunter and destroyer."""
 
 def __init__(self):
 self.contaminated_files = []
 self.violations_found = 0
 
 # 🚨 DEADLY MOCK DATA PATTERNS
 self.deadly_patterns = [
 # Fake transaction hashes
 (r"0x[a]{64}", "FAKE_TX_HASH_AAAA"),
 (r"0x[1]{64}", "FAKE_TX_HASH_1111"),
 (r"0x[f]{64}", "FAKE_TX_HASH_FFFF"),
 
 # Mock/simulation code
 (r"create_mock_opportunity", "MOCK_OPPORTUNITY_CREATOR"),
 (r"_create_mock_opportunities", "MOCK_OPPORTUNITY_BATCH"),
 (r"_get_mock_price", "MOCK_PRICE_GENERATOR"),
 (r"mock.*True", "MOCK_FLAG_TRUE"),
 (r"'mock':\s*True", "MOCK_PROPERTY_TRUE"),
 
 # Simulation delays and fake execution
 (r"await asyncio\.sleep\(0\.[0-9]+\)", "SIMULATION_DELAY"),
 (r"# Simulate.*", "SIMULATION_COMMENT"),
 (r"Would trade|Would execute|Would use", "SIMULATION_MESSAGE"),
 
 # Safety mode contamination
 (r"SAFETY MODE", "SAFETY_MODE_ACTIVE"),
 (r"ENABLE_REAL_TRANSACTIONS.*false", "REAL_TX_DISABLED"),
 
 # Mock imports and classes
 (r"from mock_", "MOCK_IMPORT"),
 (r"import.*mock", "MOCK_MODULE_IMPORT"),
 (r"class Mock", "MOCK_CLASS_DEFINITION"),
 
 # Hardcoded fake values
 (r"profit.*=.*random\.", "RANDOM_PROFIT"),
 (r"price.*=.*random\.", "RANDOM_PRICE"),
 (r"slippage_estimate.*=.*0\.1", "HARDCODED_SLIPPAGE"),
 (r"gas_estimate.*=.*[0-9]+", "HARDCODED_GAS"),
 
 # Testing/development contamination
 (r"# For now, simulate", "SIMULATION_TODO"),
 (r"# TODO.*mock", "MOCK_TODO"),
 (r"# Replace with real", "REAL_IMPLEMENTATION_TODO"),
 ]
 
 # CRITICAL FILES THAT MUST BE CLEAN
 self.critical_files = [
 "src/execution/real_arbitrage_executor.py",
 "src/flashloan/balancer_flashloan.py",
 "src/core/master_arbitrage_system.py",
 "src/real_arbitrage_bot.py"
 ]
 
 # 📁 DIRECTORIES TO SCAN
 self.scan_directories = [
 "src/",
 ".",
 ]
 
 # 🚫 FILES TO IGNORE (known test/mock files)
 self.ignore_files = [
 "mock_data_prevention_system.py",
 "MOCK_PREVENTION_RULES.md",
 "MOCK_DATA_EXTERMINATOR.py",
 "speed_optimized_arbitrage.py", # Test file
 "opportunity_lifespan_monitor.py", # Test file
 "batch_enhanced_arbitrage.py", # Test file
 ]
 
 def scan_file(self, file_path: str) -> List[Dict[str, str]]:
 """Scan a single file for mock data contamination."""
 violations = []
 
 try:
 with open(file_path, 'r', encoding='utf-8') as f:
 content = f.read()
 lines = content.split('\n')
 
 for line_num, line in enumerate(lines, 1):
 for pattern, violation_type in self.deadly_patterns:
 if re.search(pattern, line, re.IGNORECASE):
 violations.append({
 'file': file_path,
 'line': line_num,
 'content': line.strip(),
 'violation_type': violation_type,
 'pattern': pattern
 })
 
 except Exception as e:
 logger.error(f"❌ Could not scan {file_path}: {e}")
 
 return violations
 
 def scan_all_files(self) -> List[Dict[str, str]]:
 """Scan all Python files for contamination."""
 logger.info("🔍 STARTING COMPREHENSIVE MOCK DATA SCAN...")
 logger.info("=" * 60)
 
 all_violations = []
 files_scanned = 0
 
 for directory in self.scan_directories:
 if not os.path.exists(directory):
 continue
 
 for root, dirs, files in os.walk(directory):
 # Skip hidden directories and __pycache__
 dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
 
 for file in files:
 if file.endswith('.py'):
 file_path = os.path.join(root, file)
 
 # Skip ignored files
 if any(ignore in file_path for ignore in self.ignore_files):
 continue
 
 violations = self.scan_file(file_path)
 if violations:
 all_violations.extend(violations)
 if file_path not in self.contaminated_files:
 self.contaminated_files.append(file_path)
 
 files_scanned += 1
 
 self.violations_found = len(all_violations)
 logger.info(f"📊 SCAN COMPLETE: {files_scanned} files scanned, {self.violations_found} violations found")
 
 return all_violations
 
 def report_violations(self, violations: List[Dict[str, str]]):
 """Generate detailed violation report."""
 if not violations:
 logger.info(" NO MOCK DATA CONTAMINATION FOUND! SYSTEM IS CLEAN!")
 return
 
 logger.error("🚨 MOCK DATA CONTAMINATION DETECTED!")
 logger.error("=" * 60)
 
 # Group by file
 by_file = {}
 for violation in violations:
 file_path = violation['file']
 if file_path not in by_file:
 by_file[file_path] = []
 by_file[file_path].append(violation)
 
 # Report by file
 for file_path, file_violations in by_file.items():
 logger.error(f"\n📁 FILE: {file_path}")
 logger.error(f" 🚨 {len(file_violations)} violations found:")
 
 for violation in file_violations:
 logger.error(f" Line {violation['line']:3d}: {violation['violation_type']}")
 logger.error(f" Code: {violation['content'][:80]}...")
 
 # Summary by violation type
 logger.error(f"\n📊 VIOLATION SUMMARY:")
 violation_counts = {}
 for violation in violations:
 vtype = violation['violation_type']
 violation_counts[vtype] = violation_counts.get(vtype, 0) + 1
 
 for vtype, count in sorted(violation_counts.items()):
 logger.error(f" {vtype}: {count} occurrences")
 
 def check_critical_files(self) -> bool:
 """Check if critical trading files are contaminated."""
 logger.info("\n CHECKING CRITICAL TRADING FILES...")
 
 critical_contaminated = []
 
 for file_path in self.critical_files:
 if os.path.exists(file_path):
 violations = self.scan_file(file_path)
 if violations:
 critical_contaminated.append((file_path, len(violations)))
 logger.error(f"❌ CRITICAL FILE CONTAMINATED: {file_path} ({len(violations)} violations)")
 else:
 logger.info(f"✅ CRITICAL FILE CLEAN: {file_path}")
 else:
 logger.warning(f"⚠️ CRITICAL FILE MISSING: {file_path}")
 
 if critical_contaminated:
 logger.error("🚨 CRITICAL SYSTEM CONTAMINATION DETECTED!")
 logger.error(" These files MUST be cleaned before trading:")
 for file_path, count in critical_contaminated:
 logger.error(f" - {file_path} ({count} violations)")
 return False
 else:
 logger.info("✅ ALL CRITICAL FILES ARE CLEAN!")
 return True
 
 def generate_cleanup_script(self, violations: List[Dict[str, str]]):
 """Generate a script to help clean up violations."""
 if not violations:
 return
 
 logger.info("\n🔧 GENERATING CLEANUP RECOMMENDATIONS...")
 
 cleanup_actions = []
 
 for violation in violations:
 file_path = violation['file']
 line_num = violation['line']
 vtype = violation['violation_type']
 content = violation['content']
 
 if vtype == "MOCK_OPPORTUNITY_CREATOR":
 cleanup_actions.append(f"# {file_path}:{line_num} - Remove mock opportunity creation")
 elif vtype == "SIMULATION_DELAY":
 cleanup_actions.append(f"# {file_path}:{line_num} - Remove simulation delay")
 elif vtype == "FAKE_TX_HASH":
 cleanup_actions.append(f"# {file_path}:{line_num} - Replace with real transaction hash")
 elif vtype == "RANDOM_PROFIT":
 cleanup_actions.append(f"# {file_path}:{line_num} - Replace with real profit calculation")
 
 if cleanup_actions:
 logger.info("📝 CLEANUP ACTIONS NEEDED:")
 for action in cleanup_actions[:10]: # Show first 10
 logger.info(f" {action}")
 if len(cleanup_actions) > 10:
 logger.info(f" ... and {len(cleanup_actions) - 10} more")
 
 def exterminate(self) -> bool:
 """Run the complete extermination process."""
 logger.info(" MOCK DATA EXTERMINATOR ACTIVATED!")
 logger.info(" TARGET: ALL MOCK DATA CONTAMINATION")
 logger.info(" MISSION: SEARCH AND DESTROY")
 logger.info("=" * 60)
 
 # Scan all files
 violations = self.scan_all_files()
 
 # Report findings
 self.report_violations(violations)
 
 # Check critical files
 critical_clean = self.check_critical_files()
 
 # Generate cleanup recommendations
 self.generate_cleanup_script(violations)
 
 # Final verdict
 logger.info("\n" + "=" * 60)
 if violations:
 logger.error("🚨 SYSTEM CONTAMINATED - MOCK DATA FOUND!")
 logger.error(f" 📊 {len(violations)} violations in {len(self.contaminated_files)} files")
 logger.error(" 🔧 Clean up required before production trading")
 return False
 else:
 logger.info(" SYSTEM CLEAN - NO MOCK DATA DETECTED!")
 logger.info(" ✅ Safe for production trading")
 return True

def main():
 """Run the mock data exterminator."""
 exterminator = MockDataExterminator()
 is_clean = exterminator.exterminate()
 
 if not is_clean:
 logger.error("\n🚨 ACTION REQUIRED:")
 logger.error(" 1. Review violations above")
 logger.error(" 2. Remove or replace mock data")
 logger.error(" 3. Run exterminator again")
 logger.error(" 4. Only trade when system is 100% clean")
 exit(1)
 else:
 logger.info("\n SYSTEM READY FOR PRODUCTION TRADING!")
 exit(0)

if __name__ == "__main__":
 main()
