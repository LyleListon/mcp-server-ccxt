"""Base DEX interface for arbitrage bot."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


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

    @abstractmethod
    async def get_quote(self, base_token: str, quote_token: str, amount: float) -> Optional[Dict[str, Any]]:
        """Get a quote for swapping tokens.

        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol
            amount: Amount to swap

        Returns:
            Quote information including expected output, slippage, gas costs
        """
        pass

    async def execute_trade(self, base_token: str, quote_token: str, amount: float,
                          wallet_address: str, private_key: str = None) -> Optional[Dict[str, Any]]:
        """Execute a trade on this DEX.

        Args:
            base_token: Base token symbol
            quote_token: Quote token symbol
            amount: Amount to swap
            wallet_address: Wallet address for the trade
            private_key: Private key for signing (optional, for simulation)

        Returns:
            Trade execution result or None if failed
        """
        # Default implementation - subclasses should override for real trading
        logger.warning(f"{self.name} does not support real trade execution yet")
        return None

    async def disconnect(self) -> None:
        """Disconnect from the DEX."""
        # Close aiohttp session if it exists
        if hasattr(self, 'session') and self.session:
            try:
                await self.session.close()
                self.session = None
            except Exception as e:
                # Log but don't fail
                pass

        self.connected = False

    def is_connected(self) -> bool:
        """Check if connected to the DEX."""
        return self.connected

    def get_name(self) -> str:
        """Get DEX name."""
        return self.name
