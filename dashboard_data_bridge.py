#!/usr/bin/env python3
"""
🌉 DASHBOARD DATA BRIDGE
Connect your trading systems to your amazing dashboards!

This bridges the gap between your trading bots and dashboards
by creating a simple data pipeline that feeds real trading data
to your existing dashboard infrastructure.
"""

import json
import time
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard-bridge")

@dataclass
class TradeData:
 """Standardized trade data structure"""
 timestamp: str
 strategy: str
 token_pair: str
 buy_dex: str
 sell_dex: str
 profit_usd: float
 gas_spent: float
 success: bool
 execution_time: float
 chain: str
 tx_hash: Optional[str] = None

@dataclass
class OpportunityData:
 """Standardized opportunity data structure"""
 timestamp: str
 token: str
 chain: str
 buy_dex: str
 sell_dex: str
 profit_usd: float
 profit_percentage: float
 executed: bool

class DashboardDataBridge:
 """
 🌉 Bridge between trading systems and dashboards
 
 Collects data from various sources and feeds it to dashboards
 """
 
 def __init__(self):
 self.data_file = "C:/temp/mayarbi_dashboard_data.json" # Windows bridge file
 self.local_data_file = "/tmp/mayarbi_dashboard_data.json" # WSL2 file
 self.db_file = "trading_data.db"
 
 # Initialize database
 self.init_database()
 
 # Data storage
 self.session_data = {
 'session_start': datetime.now().isoformat(),
 'total_trades': 0,
 'successful_trades': 0,
 'total_profit': 0.0,
 'total_gas_spent': 0.0,
 'opportunities_found': 0,
 'opportunities_executed': 0,
 'update_count': 0
 }
 
 self.recent_trades = []
 self.recent_opportunities = []
 self.network_stats = {
 'arbitrum': {'opportunities': 0, 'executed': 0, 'profit': 0.0},
 'base': {'opportunities': 0, 'executed': 0, 'profit': 0.0},
 'optimism': {'opportunities': 0, 'executed': 0, 'profit': 0.0},
 'polygon': {'opportunities': 0, 'executed': 0, 'profit': 0.0},
 'bsc': {'opportunities': 0, 'executed': 0, 'profit': 0.0}
 }
 
 logger.info("🌉 Dashboard Data Bridge initialized")
 
 def init_database(self):
 """Initialize SQLite database for persistent storage"""
 try:
 conn = sqlite3.connect(self.db_file)
 c = conn.cursor()
 
 # Trades table
 c.execute('''CREATE TABLE IF NOT EXISTS trades (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 timestamp TEXT,
 strategy TEXT,
 token_pair TEXT,
 buy_dex TEXT,
 sell_dex TEXT,
 profit_usd REAL,
 gas_spent REAL,
 success BOOLEAN,
 execution_time REAL,
 chain TEXT,
 tx_hash TEXT
 )''')
 
 # Opportunities table
 c.execute('''CREATE TABLE IF NOT EXISTS opportunities (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 timestamp TEXT,
 token TEXT,
 chain TEXT,
 buy_dex TEXT,
 sell_dex TEXT,
 profit_usd REAL,
 profit_percentage REAL,
 executed BOOLEAN
 )''')
 
 conn.commit()
 conn.close()
 logger.info("✅ Database initialized")
 
 except Exception as e:
 logger.error(f"❌ Database initialization failed: {e}")
 
 def log_trade(self, trade: TradeData):
 """Log a completed trade"""
 try:
 # Store in database
 conn = sqlite3.connect(self.db_file)
 c = conn.cursor()
 c.execute('''INSERT INTO trades VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
 (trade.timestamp, trade.strategy, trade.token_pair, trade.buy_dex,
 trade.sell_dex, trade.profit_usd, trade.gas_spent, trade.success,
 trade.execution_time, trade.chain, trade.tx_hash))
 conn.commit()
 conn.close()
 
 # Update session data
 self.session_data['total_trades'] += 1
 if trade.success:
 self.session_data['successful_trades'] += 1
 self.session_data['total_profit'] += trade.profit_usd
 
 # Update network stats
 if trade.chain in self.network_stats:
 self.network_stats[trade.chain]['executed'] += 1
 self.network_stats[trade.chain]['profit'] += trade.profit_usd
 
 self.session_data['total_gas_spent'] += trade.gas_spent
 
 # Add to recent trades
 self.recent_trades.append(asdict(trade))
 if len(self.recent_trades) > 50:
 self.recent_trades = self.recent_trades[-50:]
 
 # Update dashboard data
 self.update_dashboard_data()
 
 logger.info(f"📊 Trade logged: {trade.token_pair} on {trade.chain} - "
 f"{'✅' if trade.success else '❌'} ${trade.profit_usd:.4f}")
 
 except Exception as e:
 logger.error(f"❌ Failed to log trade: {e}")
 
 def log_opportunity(self, opportunity: OpportunityData):
 """Log a detected opportunity"""
 try:
 # Store in database
 conn = sqlite3.connect(self.db_file)
 c = conn.cursor()
 c.execute('''INSERT INTO opportunities VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)''',
 (opportunity.timestamp, opportunity.token, opportunity.chain,
 opportunity.buy_dex, opportunity.sell_dex, opportunity.profit_usd,
 opportunity.profit_percentage, opportunity.executed))
 conn.commit()
 conn.close()
 
 # Update session data
 self.session_data['opportunities_found'] += 1
 if opportunity.executed:
 self.session_data['opportunities_executed'] += 1
 
 # Update network stats
 if opportunity.chain in self.network_stats:
 self.network_stats[opportunity.chain]['opportunities'] += 1
 
 # Add to recent opportunities
 self.recent_opportunities.append(asdict(opportunity))
 if len(self.recent_opportunities) > 100:
 self.recent_opportunities = self.recent_opportunities[-100:]
 
 # Update dashboard data
 self.update_dashboard_data()
 
 logger.info(f" Opportunity logged: {opportunity.token} on {opportunity.chain} - "
 f"${opportunity.profit_usd:.4f} ({'executed' if opportunity.executed else 'detected'})")
 
 except Exception as e:
 logger.error(f"❌ Failed to log opportunity: {e}")
 
 def update_dashboard_data(self):
 """Update dashboard data files"""
 try:
 # Calculate derived metrics
 success_rate = 0.0
 if self.session_data['total_trades'] > 0:
 success_rate = (self.session_data['successful_trades'] /
 self.session_data['total_trades']) * 100
 
 # Prepare dashboard data
 dashboard_data = {
 'update_count': self.session_data['update_count'] + 1,
 'timestamp': datetime.now().isoformat(),
 'trading_stats': {
 'session_profit': f"${self.session_data['total_profit']:.2f}",
 'total_trades': self.session_data['total_trades'],
 'success_rate': f"{success_rate:.1f}%",
 'wallet_balance': f"${765.56:.2f}", # Update with real balance
 'gas_spent': f"${self.session_data['total_gas_spent']:.4f}",
 'opportunities_found': self.session_data['opportunities_found'],
 'opportunities_executed': self.session_data['opportunities_executed']
 },
 'system_status': {
 'wsl2_bot': 'Connected and Trading',
 'last_update': datetime.now().strftime('%H:%M:%S'),
 'uptime': str(datetime.now() - datetime.fromisoformat(self.session_data['session_start']))
 },
 'network_performance': {
 'arbitrum': f"{self.network_stats['arbitrum']['opportunities']} opportunities",
 'base': f"{self.network_stats['base']['opportunities']} opportunities",
 'optimism': f"{self.network_stats['optimism']['opportunities']} opportunities"
 },
 'recent_trades': self.recent_trades[-10:],
 'recent_opportunities': self.recent_opportunities[-20:]
 }
 
 # Update session data
 self.session_data['update_count'] += 1
 
 # Write to both local and Windows files
 for file_path in [self.local_data_file, self.data_file]:
 try:
 # Ensure directory exists
 os.makedirs(os.path.dirname(file_path), exist_ok=True)
 
 with open(file_path, 'w') as f:
 json.dump(dashboard_data, f, indent=2)
 
 except Exception as e:
 logger.warning(f"⚠️ Could not write to {file_path}: {e}")
 
 logger.debug(f"📊 Dashboard data updated (#{dashboard_data['update_count']})")
 
 except Exception as e:
 logger.error(f"❌ Failed to update dashboard data: {e}")
 
 def get_session_summary(self) -> Dict[str, Any]:
 """Get current session summary"""
 success_rate = 0.0
 avg_profit = 0.0
 
 if self.session_data['total_trades'] > 0:
 success_rate = (self.session_data['successful_trades'] /
 self.session_data['total_trades']) * 100
 avg_profit = self.session_data['total_profit'] / self.session_data['total_trades']
 
 return {
 'session_start': self.session_data['session_start'],
 'total_trades': self.session_data['total_trades'],
 'successful_trades': self.session_data['successful_trades'],
 'success_rate': success_rate,
 'total_profit': self.session_data['total_profit'],
 'avg_profit_per_trade': avg_profit,
 'total_gas_spent': self.session_data['total_gas_spent'],
 'net_profit': self.session_data['total_profit'] - self.session_data['total_gas_spent'],
 'opportunities_found': self.session_data['opportunities_found'],
 'opportunities_executed': self.session_data['opportunities_executed'],
 'network_stats': self.network_stats
 }
 
 def start_background_updates(self):
 """Start background thread for periodic updates"""
 def update_loop():
 while True:
 try:
 self.update_dashboard_data()
 time.sleep(5) # Update every 5 seconds
 except Exception as e:
 logger.error(f"❌ Background update error: {e}")
 time.sleep(10)
 
 thread = threading.Thread(target=update_loop, daemon=True)
 thread.start()
 logger.info("🔄 Background updates started")

# Global bridge instance
bridge = DashboardDataBridge()

def log_trade_simple(token_pair: str, chain: str, buy_dex: str, sell_dex: str,
 profit_usd: float, gas_spent: float, success: bool,
 strategy: str = "arbitrage", execution_time: float = 0.0):
 """Simple function to log a trade from anywhere in your code"""
 trade = TradeData(
 timestamp=datetime.now().isoformat(),
 strategy=strategy,
 token_pair=token_pair,
 buy_dex=buy_dex,
 sell_dex=sell_dex,
 profit_usd=profit_usd,
 gas_spent=gas_spent,
 success=success,
 execution_time=execution_time,
 chain=chain
 )
 bridge.log_trade(trade)

def log_opportunity_simple(token: str, chain: str, buy_dex: str, sell_dex: str,
 profit_usd: float, profit_percentage: float, executed: bool = False):
 """Simple function to log an opportunity from anywhere in your code"""
 opportunity = OpportunityData(
 timestamp=datetime.now().isoformat(),
 token=token,
 chain=chain,
 buy_dex=buy_dex,
 sell_dex=sell_dex,
 profit_usd=profit_usd,
 profit_percentage=profit_percentage,
 executed=executed
 )
 bridge.log_opportunity(opportunity)

if __name__ == "__main__":
 # Start the bridge
 bridge.start_background_updates()
 
 # Example usage
 logger.info("🌉 Dashboard Data Bridge running...")
 logger.info("📊 Add these imports to your trading scripts:")
 logger.info(" from dashboard_data_bridge import log_trade_simple, log_opportunity_simple")
 logger.info("📈 Your dashboards will now show REAL DATA!")
 
 # Keep running
 try:
 while True:
 time.sleep(60)
 summary = bridge.get_session_summary()
 logger.info(f"📊 Session: {summary['total_trades']} trades, "
 f"${summary['total_profit']:.2f} profit, "
 f"{summary['success_rate']:.1f}% success rate")
 except KeyboardInterrupt:
 logger.info("🛑 Dashboard Data Bridge stopped")
