"""Interface definitions for arbitrage bot components."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class OpportunityDetector(ABC):
    """Interface for arbitrage opportunity detectors."""
    
    @abstractmethod
    async def detect_opportunities(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect arbitrage opportunities.
        
        Args:
            market_data: Current market data
            
        Returns:
            List of detected opportunities
        """
        pass


class MarketDataProvider(ABC):
    """Interface for market data providers."""
    
    @abstractmethod
    async def get_market_data(self) -> Dict[str, Any]:
        """Get current market data.
        
        Returns:
            Market data dictionary
        """
        pass
    
    @abstractmethod
    async def subscribe_to_updates(self, callback) -> None:
        """Subscribe to market data updates.
        
        Args:
            callback: Function to call when data updates
        """
        pass


class TradeExecutor(ABC):
    """Interface for trade execution."""
    
    @abstractmethod
    async def execute_trade(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an arbitrage trade.
        
        Args:
            opportunity: Opportunity to execute
            
        Returns:
            Execution result
        """
        pass
