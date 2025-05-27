"""Simple file-based data storage for arbitrage patterns.

This is a temporary solution while CUDA/MCP memory server issues are resolved.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SimpleDataStorage:
    """Simple file-based storage for arbitrage data."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize storage with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "patterns").mkdir(exist_ok=True)
        (self.data_dir / "opportunities").mkdir(exist_ok=True)
        (self.data_dir / "executions").mkdir(exist_ok=True)
        (self.data_dir / "stats").mkdir(exist_ok=True)
        
        logger.info(f"Simple data storage initialized at {self.data_dir}")
    
    def store_arbitrage_pattern(self, opportunity: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Store an arbitrage pattern with execution result."""
        try:
            timestamp = datetime.now()
            pattern_id = f"pattern_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
            
            pattern_data = {
                'id': pattern_id,
                'timestamp': timestamp.isoformat(),
                'opportunity': opportunity,
                'result': result,
                'tokens': opportunity.get('tokens', []),
                'dexs': opportunity.get('dexs', []),
                'profit': result.get('profit', 0),
                'success': result.get('success', False),
                'gas_cost': result.get('gas_cost', 0)
            }
            
            # Store in patterns directory
            pattern_file = self.data_dir / "patterns" / f"{pattern_id}.json"
            with open(pattern_file, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            
            # Update daily summary
            self._update_daily_summary(pattern_data)
            
            logger.info(f"Stored arbitrage pattern: {pattern_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing arbitrage pattern: {e}")
            return False
    
    def store_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """Store a detected opportunity."""
        try:
            timestamp = datetime.now()
            opp_id = f"opp_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
            
            opp_data = {
                'id': opp_id,
                'timestamp': timestamp.isoformat(),
                **opportunity
            }
            
            # Store in opportunities directory
            opp_file = self.data_dir / "opportunities" / f"{opp_id}.json"
            with open(opp_file, 'w') as f:
                json.dump(opp_data, f, indent=2)
            
            logger.debug(f"Stored opportunity: {opp_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing opportunity: {e}")
            return False
    
    def get_recent_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent arbitrage patterns."""
        try:
            patterns_dir = self.data_dir / "patterns"
            pattern_files = sorted(patterns_dir.glob("*.json"), reverse=True)
            
            patterns = []
            for pattern_file in pattern_files[:limit]:
                with open(pattern_file, 'r') as f:
                    patterns.append(json.load(f))
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error getting recent patterns: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            patterns_count = len(list((self.data_dir / "patterns").glob("*.json")))
            opportunities_count = len(list((self.data_dir / "opportunities").glob("*.json")))
            
            # Calculate success rate from recent patterns
            recent_patterns = self.get_recent_patterns(100)
            successful = sum(1 for p in recent_patterns if p.get('result', {}).get('success', False))
            success_rate = (successful / len(recent_patterns)) * 100 if recent_patterns else 0
            
            # Calculate total profit
            total_profit = sum(p.get('result', {}).get('profit', 0) for p in recent_patterns)
            
            return {
                'total_patterns': patterns_count,
                'total_opportunities': opportunities_count,
                'recent_success_rate': success_rate,
                'recent_total_profit': total_profit,
                'data_directory': str(self.data_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def _update_daily_summary(self, pattern_data: Dict[str, Any]) -> None:
        """Update daily summary statistics."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            summary_file = self.data_dir / "stats" / f"daily_{today}.json"
            
            # Load existing summary or create new
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    summary = json.load(f)
            else:
                summary = {
                    'date': today,
                    'total_patterns': 0,
                    'successful_patterns': 0,
                    'total_profit': 0,
                    'total_gas_cost': 0,
                    'tokens_traded': set(),
                    'dexs_used': set()
                }
            
            # Update summary
            summary['total_patterns'] += 1
            if pattern_data.get('success', False):
                summary['successful_patterns'] += 1
            summary['total_profit'] += pattern_data.get('profit', 0)
            summary['total_gas_cost'] += pattern_data.get('gas_cost', 0)
            
            # Convert sets to lists for JSON serialization
            tokens = set(summary.get('tokens_traded', []))
            tokens.update(pattern_data.get('tokens', []))
            summary['tokens_traded'] = list(tokens)
            
            dexs = set(summary.get('dexs_used', []))
            dexs.update(pattern_data.get('dexs', []))
            summary['dexs_used'] = list(dexs)
            
            # Save updated summary
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating daily summary: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up data older than specified days."""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            for directory in ["patterns", "opportunities"]:
                data_path = self.data_dir / directory
                for file_path in data_path.glob("*.json"):
                    if file_path.stat().st_mtime < cutoff_date:
                        file_path.unlink()
                        logger.debug(f"Cleaned up old file: {file_path}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
