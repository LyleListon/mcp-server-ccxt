"""Data models for arbitrage bot."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StrategyType(Enum):
    """Types of arbitrage strategies."""
    SIMPLE = "simple"
    TRIANGULAR = "triangular"
    FLASH_LOAN = "flash_loan"
    CROSS_CHAIN = "cross_chain"


@dataclass
class TokenAmount:
    """Represents an amount of a specific token."""
    token: str
    amount: float
    decimals: int = 18
    
    def to_wei(self) -> int:
        """Convert to wei (smallest unit)."""
        return int(self.amount * (10 ** self.decimals))
    
    @classmethod
    def from_wei(cls, token: str, wei_amount: int, decimals: int = 18) -> 'TokenAmount':
        """Create from wei amount."""
        amount = wei_amount / (10 ** decimals)
        return cls(token=token, amount=amount, decimals=decimals)


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity."""
    id: str
    timestamp: datetime
    strategy_type: StrategyType
    tokens: List[str]
    dexs: List[str]
    path: List[str]
    estimated_profit: float
    estimated_gas_cost: float
    profit_percentage: float
    risk_score: float
    liquidity_requirements: Dict[str, float]
    market_conditions: Dict[str, Any]
    
    def net_profit(self) -> float:
        """Calculate net profit after gas costs."""
        return self.estimated_profit - self.estimated_gas_cost
    
    def is_profitable(self) -> bool:
        """Check if opportunity is profitable after costs."""
        return self.net_profit() > 0
