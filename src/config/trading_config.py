"""
Centralized Trading Configuration
================================

Single source of truth for all trading parameters.
No more scattered configuration values!

Usage:
    from src.config.trading_config import TradingConfig
    
    if profit > TradingConfig.MIN_PROFIT_USD:
        execute_trade()
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class TradingConfig:
    """
    🎯 SINGLE SOURCE OF TRUTH FOR ALL TRADING PARAMETERS
    
    Change values here and they update everywhere in the system.
    No more hunting through multiple files!
    """
    
    # ============================================================================
    # 💰 PROFIT THRESHOLDS
    # ============================================================================
    MIN_PROFIT_USD: float = 0.25           # 🎯 UPDATED: $0.25 minimum to capture more opportunities
    MIN_PROFIT_PERCENTAGE: float = 0.1     # 0.1% minimum profit margin
    TARGET_PROFIT_USD: float = 3.00        # Sweet spot for 7.4s execution
    LARGE_PROFIT_USD: float = 10.00        # Low competition zone
    
    # ============================================================================
    # 💼 POSITION SIZING (75% of wallet strategy)
    # ============================================================================
    MAX_TRADE_PERCENTAGE: float = 0.75     # 75% of total wallet value (~$343)
    TOTAL_CAPITAL_USD: float = 872.0       # Current wallet value
    MIN_TRADE_USD: float = 10.0            # Minimum viable trade size
    RESERVE_PERCENTAGE: float = 0.15       # Keep 15% in reserve

    @property
    def MAX_TRADE_USD(self) -> float:
        """Calculate max trade USD based on capital and percentage."""
        return self.TOTAL_CAPITAL_USD * self.MAX_TRADE_PERCENTAGE
    
    # ============================================================================
    # ⛽ GAS & EXECUTION SETTINGS
    # ============================================================================
    GAS_PRICE_MULTIPLIER: float = 2.0      # 2x gas for priority inclusion
    MAX_GAS_PRICE_GWEI: float = 50.0       # Maximum gas price willing to pay
    MIN_GAS_PRICE_GWEI: float = 0.2        # Minimum gas price (Arbitrum)
    FIXED_GAS_LIMIT: int = 500000          # Skip gas estimation for speed
    EXECUTION_TIMEOUT_SECONDS: int = 30    # Maximum execution time
    
    # ============================================================================
    # 📊 SLIPPAGE & RISK MANAGEMENT
    # ============================================================================
    MAX_SLIPPAGE_PERCENTAGE: float = 5.0   # 5% maximum slippage
    DEFAULT_SLIPPAGE: float = 1.0          # 1% default slippage
    MAX_PRICE_IMPACT: float = 0.5          # 0.5% maximum price impact
    MAX_RISK_SCORE: int = 50               # Maximum acceptable risk score
    
    # ============================================================================
    # ⏱️ TIMING & SCANNING
    # ============================================================================
    SCAN_INTERVAL_SECONDS: float = 2.0     # Scan every 2 seconds
    OPPORTUNITY_MAX_AGE_SECONDS: float = 15.0  # Opportunities expire after 15s
    MAX_EXECUTION_TIME_SECONDS: float = 7.5    # Target: beat current 7.4s
    RETRY_ATTEMPTS: int = 3                # Number of retry attempts
    RETRY_DELAY_SECONDS: float = 1.0       # Delay between retries
    
    # ============================================================================
    # 🌐 NETWORK PREFERENCES
    # ============================================================================
    PREFERRED_NETWORKS: List[str] = field(default_factory=lambda: [
        "arbitrum",     # Primary network (lowest gas)
        "base",         # Secondary network
        "optimism"      # Tertiary network
    ])

    NETWORK_CONFIGS: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'arbitrum': {
            'chain_id': 42161,
            'gas_multiplier': 2.0,
            'min_gas_gwei': 0.2,
            'priority_fee_gwei': 1.5
        },
        'base': {
            'chain_id': 8453,
            'gas_multiplier': 2.0,
            'min_gas_gwei': 0.5,
            'priority_fee_gwei': 1.0
        },
        'optimism': {
            'chain_id': 10,
            'gas_multiplier': 1.8,
            'min_gas_gwei': 0.3,
            'priority_fee_gwei': 1.2
        }
    })
    
    # ============================================================================
    # 🎯 TARGET TOKENS (Focus on what you hold)
    # ============================================================================
    TARGET_TOKENS: List[str] = field(default_factory=lambda: [
        "ETH", "WETH",      # Your primary holdings
        "USDC", "USDT",     # Your stablecoins
        "DAI"               # Additional stablecoin
    ])
    
    # ============================================================================
    # 🔄 TRADING STRATEGY SETTINGS
    # ============================================================================
    ENABLE_SAME_CHAIN: bool = True         # Enable same-chain arbitrage
    ENABLE_CROSS_CHAIN: bool = True        # Enable cross-chain arbitrage
    ENABLE_FLASHLOANS: bool = False        # Flashloans (when deployed)
    MAX_CONCURRENT_TRADES: int = 1         # Focus on one trade at a time
    
    # ============================================================================
    # 📈 LIQUIDITY REQUIREMENTS
    # ============================================================================
    MIN_LIQUIDITY_USD: float = 50000       # Minimum pool liquidity
    MIN_VOLUME_24H_USD: float = 100000     # Minimum 24h volume
    
    # ============================================================================
    # 🚨 CIRCUIT BREAKER SETTINGS
    # ============================================================================
    MAX_CONSECUTIVE_LOSSES: int = 5        # Stop after 5 losses
    MAX_DAILY_LOSS_PERCENTAGE: float = 10.0  # Stop at 10% daily loss

    # 🛡️ AUTO-SHUTDOWN PROTECTION - Any negative return = failed transaction
    MAX_FAILED_TRANSACTIONS: int = 25      # Auto-shutdown after 25 failed (negative return) transactions
    FAILED_TRANSACTION_RESET_HOURS: int = 1  # Reset failure counter every hour

    # ============================================================================
    # 🔥 FLASHLOAN CONFIGURATION
    # ============================================================================
    ENABLE_FLASHLOANS: bool = True          # Enable flashloan arbitrage
    MIN_FLASHLOAN_PROFIT_USD: float = 2.0   # Minimum profit to trigger flashloan
    PREFERRED_FLASHLOAN_PROVIDER: str = "balancer"  # balancer (0% fees) > dydx (0% fees) > aave (0.09% fees)
    MAX_FLASHLOAN_AMOUNT_USD: float = 100000.0  # $100K max flashloan size
    FLASHLOAN_GAS_MULTIPLIER: float = 1.5   # Extra gas for flashloan complexity

    @property
    def DAILY_LOSS_LIMIT_USD(self) -> float:
        """Calculate daily loss limit based on capital and percentage."""
        return self.TOTAL_CAPITAL_USD * (self.MAX_DAILY_LOSS_PERCENTAGE / 100)
    
    # ============================================================================
    # 🎛️ ENVIRONMENT VARIABLE OVERRIDES
    # ============================================================================
    @classmethod
    def from_environment(cls) -> 'TradingConfig':
        """
        Create config with environment variable overrides.
        Allows runtime configuration without code changes.
        """
        config = cls()
        
        # Override with environment variables if present
        if os.getenv('MIN_PROFIT_USD'):
            config.MIN_PROFIT_USD = float(os.getenv('MIN_PROFIT_USD'))
            
        if os.getenv('MAX_TRADE_PERCENTAGE'):
            config.MAX_TRADE_PERCENTAGE = float(os.getenv('MAX_TRADE_PERCENTAGE'))
            
        if os.getenv('GAS_PRICE_MULTIPLIER'):
            config.GAS_PRICE_MULTIPLIER = float(os.getenv('GAS_PRICE_MULTIPLIER'))
            
        if os.getenv('SCAN_INTERVAL'):
            config.SCAN_INTERVAL_SECONDS = float(os.getenv('SCAN_INTERVAL'))
            
        return config
    
    # ============================================================================
    # 📊 CALCULATED PROPERTIES
    # ============================================================================
    @property
    def max_trade_amount_eth(self) -> float:
        """Calculate max trade amount in ETH (assuming $3000/ETH)."""
        eth_price = 3000.0  # TODO: Get from price feed
        return self.MAX_TRADE_USD / eth_price
    
    @property
    def daily_loss_limit_eth(self) -> float:
        """Calculate daily loss limit in ETH."""
        eth_price = 3000.0  # TODO: Get from price feed
        return self.DAILY_LOSS_LIMIT_USD / eth_price
    
    # ============================================================================
    # 🔧 UTILITY METHODS
    # ============================================================================
    def get_network_config(self, network: str) -> Dict[str, Any]:
        """Get configuration for specific network."""
        return self.NETWORK_CONFIGS.get(network, {})
    
    def is_profitable_opportunity(self, profit_usd: float) -> bool:
        """Check if opportunity meets minimum profit threshold."""
        return profit_usd >= self.MIN_PROFIT_USD
    
    def is_valid_trade_size(self, amount_usd: float) -> bool:
        """Check if trade size is within acceptable limits."""
        return self.MIN_TRADE_USD <= amount_usd <= self.MAX_TRADE_USD
    
    def get_gas_price_for_network(self, network: str) -> float:
        """Get optimized gas price for network."""
        network_config = self.get_network_config(network)
        base_gas = network_config.get('min_gas_gwei', 1.0)
        multiplier = network_config.get('gas_multiplier', 1.5)
        return min(base_gas * multiplier, self.MAX_GAS_PRICE_GWEI)


# ============================================================================
# 🎯 GLOBAL INSTANCE - Import this everywhere
# ============================================================================
# Create global instance that can be imported
CONFIG = TradingConfig.from_environment()

# Convenience aliases for common values
MIN_PROFIT = CONFIG.MIN_PROFIT_USD
MAX_TRADE_SIZE = CONFIG.MAX_TRADE_USD
GAS_MULTIPLIER = CONFIG.GAS_PRICE_MULTIPLIER
SCAN_INTERVAL = CONFIG.SCAN_INTERVAL_SECONDS
