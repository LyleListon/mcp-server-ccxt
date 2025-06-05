#!/usr/bin/env python3
"""
Configuration Migration Script
=============================

This script identifies all the scattered configuration values
and shows exactly what needs to be updated to use the new
centralized TradingConfig.

Run this to see the migration plan before making changes.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


class ConfigMigrationAnalyzer:
    """Analyzes codebase for scattered configuration values."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.scattered_configs = []
        
    def find_scattered_configs(self) -> List[Dict]:
        """Find all scattered configuration values."""
        
        # Patterns to search for
        patterns = {
            'min_profit': [
                r'min_profit[_\w]*\s*[=:]\s*([0-9.]+)',
                r'MIN_PROFIT[_\w]*\s*[=:]\s*([0-9.]+)',
                r'profit[_\w]*threshold\s*[=:]\s*([0-9.]+)'
            ],
            'max_trade': [
                r'max_trade[_\w]*\s*[=:]\s*([0-9.]+)',
                r'MAX_TRADE[_\w]*\s*[=:]\s*([0-9.]+)',
                r'trade[_\w]*size[_\w]*\s*[=:]\s*([0-9.]+)'
            ],
            'gas_price': [
                r'gas[_\w]*price[_\w]*\s*[=:]\s*([0-9.]+)',
                r'GAS[_\w]*PRICE[_\w]*\s*[=:]\s*([0-9.]+)',
                r'gas[_\w]*multiplier\s*[=:]\s*([0-9.]+)'
            ],
            'slippage': [
                r'slippage[_\w]*\s*[=:]\s*([0-9.]+)',
                r'SLIPPAGE[_\w]*\s*[=:]\s*([0-9.]+)',
                r'max_slippage\s*[=:]\s*([0-9.]+)'
            ],
            'scan_interval': [
                r'scan[_\w]*interval\s*[=:]\s*([0-9.]+)',
                r'SCAN[_\w]*INTERVAL\s*[=:]\s*([0-9.]+)'
            ]
        }
        
        # Search through Python files
        python_files = list(self.project_root.rglob("*.py"))
        json_files = list(self.project_root.rglob("*.json"))
        
        all_files = python_files + json_files
        
        results = []
        
        for file_path in all_files:
            if 'venv' in str(file_path) or '__pycache__' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for config_type, pattern_list in patterns.items():
                    for pattern in pattern_list:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            results.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'type': config_type,
                                'pattern': match.group(0),
                                'value': match.group(1),
                                'context': self._get_line_context(content, match.start())
                            })
                            
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                
        return results
    
    def _get_line_context(self, content: str, position: int) -> str:
        """Get the line containing the match."""
        lines = content.split('\n')
        line_num = content[:position].count('\n')
        if line_num < len(lines):
            return lines[line_num].strip()
        return ""
    
    def generate_migration_plan(self) -> str:
        """Generate a migration plan."""
        configs = self.find_scattered_configs()
        
        plan = """
🔧 CONFIGURATION MIGRATION PLAN
===============================

Found {} scattered configuration values that need to be centralized.

""".format(len(configs))
        
        # Group by file
        by_file = {}
        for config in configs:
            file_path = config['file']
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(config)
        
        for file_path, file_configs in by_file.items():
            plan += f"\n📁 {file_path}\n"
            plan += "=" * (len(file_path) + 3) + "\n"
            
            for config in file_configs:
                plan += f"  Line {config['line']:3d}: {config['type']:<15} = {config['value']:<8} | {config['context'][:60]}...\n"
            
            plan += "\n  🔄 REPLACE WITH:\n"
            plan += "     from src.config.trading_config import CONFIG\n"
            
            # Suggest replacements
            replacements = {
                'min_profit': 'CONFIG.MIN_PROFIT_USD',
                'max_trade': 'CONFIG.MAX_TRADE_USD', 
                'gas_price': 'CONFIG.GAS_PRICE_MULTIPLIER',
                'slippage': 'CONFIG.MAX_SLIPPAGE_PERCENTAGE',
                'scan_interval': 'CONFIG.SCAN_INTERVAL_SECONDS'
            }
            
            for config in file_configs:
                if config['type'] in replacements:
                    plan += f"     {config['pattern']} → {replacements[config['type']]}\n"
            
            plan += "\n"
        
        # Summary
        plan += """
🎯 MIGRATION BENEFITS:
=====================
✅ Single source of truth - change one value, updates everywhere
✅ No more configuration mismatches between files  
✅ Easy A/B testing - change CONFIG.MIN_PROFIT_USD and test
✅ Environment variable overrides for production
✅ Type safety and validation
✅ Clean, professional codebase

🚀 NEXT STEPS:
=============
1. Review this migration plan
2. Update files one by one (start with most critical)
3. Test each change to ensure it works
4. Remove old configuration files once migrated
5. Implement $1 minimum profit filter using CONFIG.MIN_PROFIT_USD

"""
        return plan


def main():
    """Run the migration analysis."""
    project_root = os.getcwd()
    analyzer = ConfigMigrationAnalyzer(project_root)
    
    print("🔍 Analyzing codebase for scattered configuration values...")
    plan = analyzer.generate_migration_plan()
    
    print(plan)
    
    # Save plan to file
    with open('config_migration_plan.txt', 'w') as f:
        f.write(plan)
    
    print("📝 Migration plan saved to: config_migration_plan.txt")
    print("\n🎯 Ready to start migration? Let's clean up this configuration mess!")


if __name__ == "__main__":
    main()
