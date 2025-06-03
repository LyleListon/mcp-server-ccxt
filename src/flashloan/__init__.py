"""
MayArbi Flash Loan Module
Provides multi-provider flash loan capabilities for arbitrage trading.
"""

from .aave_flashloan import AaveFlashLoan
from .multi_provider_flashloan import MultiProviderFlashLoan

__all__ = [
    'AaveFlashLoan',
    'MultiProviderFlashLoan'
]
