#!/usr/bin/env python3
"""
🌉 DASHBOARD BRIDGE
WSL2 → Windows Dashboard Communication Bridge
Sends real-time arbitrage data to Windows dashboard
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import requests
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class TradingStats:
    """Trading statistics for dashboard"""
    session_profit: float = 0.0
    total_trades: int = 0
    success_rate: float = 0.0
    wallet_balance: float = 0.0
    
@dataclass
class SystemStatus:
    """System status for dashboard"""
    dashboard_active: bool = True
    wsl2_bot_status: str = "Connecting"
    networks: list = None
    last_update: str = ""
    
@dataclass
class NetworkPerformance:
    """Network performance metrics"""
    arbitrum_opportunities: int = 0
    base_opportunities: int = 0
    optimism_opportunities: int = 0
    updates: int = 0

class DashboardBridge:
    """Bridge between WSL2 arbitrage bot and Windows dashboard"""
    
    def __init__(self, dashboard_url: str = "http://localhost:9999"):
        self.dashboard_url = dashboard_url
        self.session = None
        self.connected = False
        self.stats = TradingStats(wallet_balance=763.00)  # Current wallet balance
        self.system_status = SystemStatus(networks=["Arbitrum", "Base", "Optimism"])
        self.network_performance = NetworkPerformance()
        self.update_count = 0
        
    async def initialize(self) -> bool:
        """Initialize the dashboard bridge"""
        try:
            # Create aiohttp session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            )
            
            # Test connection to Windows dashboard
            await self._test_connection()
            
            logger.info("🌉 Dashboard bridge initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Dashboard bridge initialization failed: {e}")
            return False
    
    async def _test_connection(self) -> bool:
        """Test connection to Windows dashboard"""
        try:
            async with self.session.get(f"{self.dashboard_url}/api/data") as response:
                if response.status == 200:
                    self.connected = True
                    logger.info("✅ Connected to Windows dashboard")
                    return True
                else:
                    logger.warning(f"⚠️ Dashboard responded with status {response.status}")
                    return False
                    
        except Exception as e:
            logger.warning(f"⚠️ Dashboard connection test failed: {e}")
            self.connected = False
            return False
    
    async def send_trading_update(self, 
                                profit: float = None,
                                trade_executed: bool = False,
                                trade_success: bool = False,
                                wallet_balance: float = None) -> bool:
        """Send trading update to dashboard"""
        
        try:
            # Update stats
            if profit is not None:
                self.stats.session_profit += profit
                
            if trade_executed:
                self.stats.total_trades += 1
                if trade_success:
                    # Recalculate success rate
                    success_count = int(self.stats.success_rate * (self.stats.total_trades - 1) / 100)
                    success_count += 1
                    self.stats.success_rate = (success_count / self.stats.total_trades) * 100
                else:
                    # Recalculate success rate for failure
                    success_count = int(self.stats.success_rate * (self.stats.total_trades - 1) / 100)
                    self.stats.success_rate = (success_count / self.stats.total_trades) * 100
                    
            if wallet_balance is not None:
                self.stats.wallet_balance = wallet_balance
            
            # Send update
            return await self._send_update()
            
        except Exception as e:
            logger.error(f"❌ Failed to send trading update: {e}")
            return False
    
    async def send_opportunity_update(self, 
                                    network: str,
                                    opportunities_found: int = 1) -> bool:
        """Send opportunity detection update"""
        
        try:
            # Update network performance
            network_lower = network.lower()
            if network_lower == "arbitrum":
                self.network_performance.arbitrum_opportunities += opportunities_found
            elif network_lower == "base":
                self.network_performance.base_opportunities += opportunities_found
            elif network_lower == "optimism":
                self.network_performance.optimism_opportunities += opportunities_found
            
            self.network_performance.updates += 1
            
            # Send update
            return await self._send_update()
            
        except Exception as e:
            logger.error(f"❌ Failed to send opportunity update: {e}")
            return False
    
    async def send_system_status(self, 
                               bot_status: str = None,
                               networks: list = None) -> bool:
        """Send system status update"""
        
        try:
            if bot_status:
                self.system_status.wsl2_bot_status = bot_status
                
            if networks:
                self.system_status.networks = networks
                
            self.system_status.last_update = datetime.now().strftime("%I:%M:%S %p")
            
            # Send update
            return await self._send_update()
            
        except Exception as e:
            logger.error(f"❌ Failed to send system status: {e}")
            return False
    
    async def _send_update(self) -> bool:
        """Send complete update to dashboard"""

        try:
            self.update_count += 1

            # Prepare dashboard data
            dashboard_data = {
                "trading_stats": {
                    "session_profit": self.stats.session_profit,
                    "total_trades": self.stats.total_trades,
                    "success_rate": f"{self.stats.success_rate:.0f}%",
                    "wallet_balance": f"${self.stats.wallet_balance:.2f}"
                },
                "system_status": {
                    "dashboard": "✅ Active",
                    "wsl2_bot": f"⚡ {self.system_status.wsl2_bot_status}",
                    "networks": ", ".join(self.system_status.networks),
                    "last_update": self.system_status.last_update
                },
                "network_performance": {
                    "arbitrum": f"{self.network_performance.arbitrum_opportunities} opportunities",
                    "base": f"{self.network_performance.base_opportunities} opportunities",
                    "optimism": f"{self.network_performance.optimism_opportunities} opportunities",
                    "updates": self.network_performance.updates
                },
                "timestamp": datetime.now().isoformat(),
                "update_count": self.update_count
            }

            # Try HTTP first (if dashboard is accessible)
            if self.connected:
                try:
                    async with self.session.post(
                        f"{self.dashboard_url}/api/update",
                        json=dashboard_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:

                        if response.status == 200:
                            logger.debug(f"📊 Dashboard update sent via HTTP (#{self.update_count})")
                            return True
                except:
                    self.connected = False

            # Fallback: Write to shared file (WSL2 → Windows bridge)
            try:
                # Write to /mnt/c/temp/ which Windows can read
                import os
                os.makedirs("/mnt/c/temp", exist_ok=True)

                with open("/mnt/c/temp/mayarbi_dashboard_data.json", "w") as f:
                    import json
                    json.dump(dashboard_data, f, indent=2)

                logger.debug(f"📊 Dashboard data written to file (#{self.update_count})")
                return True

            except Exception as file_error:
                logger.error(f"❌ Failed to write dashboard file: {file_error}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to send dashboard update: {e}")
            return False
    
    async def send_heartbeat(self) -> bool:
        """Send heartbeat to keep connection alive"""
        return await self.send_system_status(bot_status="Running")
    
    async def close(self):
        """Close the dashboard bridge"""
        if self.session:
            await self.session.close()
        logger.info("🌉 Dashboard bridge closed")

# Global bridge instance
dashboard_bridge = None

async def get_dashboard_bridge() -> DashboardBridge:
    """Get or create dashboard bridge instance"""
    global dashboard_bridge
    
    if dashboard_bridge is None:
        dashboard_bridge = DashboardBridge()
        await dashboard_bridge.initialize()
    
    return dashboard_bridge

async def send_trading_data(profit: float = None, 
                          trade_executed: bool = False,
                          trade_success: bool = False,
                          wallet_balance: float = None):
    """Convenience function to send trading data"""
    bridge = await get_dashboard_bridge()
    await bridge.send_trading_update(profit, trade_executed, trade_success, wallet_balance)

async def send_opportunity_data(network: str, opportunities: int = 1):
    """Convenience function to send opportunity data"""
    bridge = await get_dashboard_bridge()
    await bridge.send_opportunity_update(network, opportunities)

async def send_status_data(bot_status: str = None, networks: list = None):
    """Convenience function to send status data"""
    bridge = await get_dashboard_bridge()
    await bridge.send_system_status(bot_status, networks)
