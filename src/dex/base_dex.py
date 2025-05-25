"""Base DEX interface for arbitrage bot."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime


class BaseDEX(ABC):
    """Base class for DEX integrations."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the DEX.
        
        Args:
            name: Name of the DEX
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.connected = False
        self.last_update = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the DEX.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    async def get_pairs(self) -> List[Dict[str, Any]]:
        """Get available trading pairs.
        
        Returns:
            List of trading pair information
        """
        pass
    
    @abstractmethod
    async def get_price(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get current price for a token pair.
        
        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol
            
        Returns:
            Current price or None if not available
        """
        pass
    
    @abstractmethod
    async def get_liquidity(self, base_token: str, quote_token: str) -> Optional[float]:
        """Get liquidity for a token pair.
        
        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol
            
        Returns:
            Liquidity amount or None if not available
        """
        pass
    
    async def disconnect(self) -> None:
        """Disconnect from the DEX."""
        self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to the DEX."""
        return self.connected
    
    def get_name(self) -> str:
        """Get DEX name."""
        return self.name
