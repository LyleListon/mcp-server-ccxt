"""
Flash loan interfaces and data structures
"""

from typing import Dict, Any, Optional, NamedTuple
from dataclasses import dataclass
from decimal import Decimal
from eth_typing import ChecksumAddress


@dataclass
class Transaction:
    """Transaction data structure"""
    from_: ChecksumAddress
    to: ChecksumAddress
    data: bytes
    gas: int
    gas_price: int
    value: int = 0
    nonce: Optional[int] = None


@dataclass
class TokenPair:
    """Token pair for trading"""
    token0: ChecksumAddress
    token1: ChecksumAddress
    fee: int = 3000  # Default 0.3% fee


@dataclass
class LiquidityData:
    """Liquidity information for a pool"""
    liquidity: Decimal
    fee: int
    token0_reserve: Decimal
    token1_reserve: Decimal
    price: Decimal


@dataclass
class FlashLoanParams:
    """Flash loan parameters"""
    token: ChecksumAddress
    amount: int
    provider: str
    fee_percentage: Decimal
    callback_data: bytes = b""


class FlashLoanCallback:
    """Base class for flash loan callbacks"""
    
    async def execute(self, params: FlashLoanParams) -> bool:
        """Execute the flash loan callback"""
        raise NotImplementedError
    
    async def validate(self, params: FlashLoanParams) -> bool:
        """Validate flash loan parameters"""
        return True


@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity data"""
    buy_dex: str
    sell_dex: str
    token_in: ChecksumAddress
    token_out: ChecksumAddress
    amount_in: int
    expected_amount_out: int
    profit_percentage: Decimal
    gas_estimate: int
    timestamp: float


@dataclass
class FlashLoanQuote:
    """Flash loan quote information"""
    provider: str
    token: ChecksumAddress
    amount: int
    fee_amount: int
    fee_percentage: Decimal
    max_available: int
    gas_estimate: int
    viable: bool = True


@dataclass
class ExecutionResult:
    """Result of flash loan execution"""
    success: bool
    transaction_hash: Optional[str] = None
    profit_realized: Optional[Decimal] = None
    gas_used: Optional[int] = None
    error_message: Optional[str] = None
