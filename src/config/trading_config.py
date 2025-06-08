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
    # 💰 PROFIT THRESHOLDS - NO MORE GUARANTEED LOSSES!
    # ============================================================================
    MIN_PROFIT_USD: float = 10.00          # 🎯 RAISED: $10 minimum - NO MORE PENNY TRADES!
    MIN_PROFIT_PERCENTAGE: float = 2.0     # 🚨 RAISED: 2.0% minimum - BEAT THE 750% COST RATIO!
    TARGET_PROFIT_USD: float = 25.00       # Sweet spot for profitable execution
    LARGE_PROFIT_USD: float = 50.00        # High-profit zone
    
    # ============================================================================
    # 💼 POSITION SIZING (75% of wallet strategy)
    # ============================================================================
    MAX_TRADE_PERCENTAGE: float = 0.75     # 75% of total wallet value (~$572)
    TOTAL_CAPITAL_USD: float = 763.00      # 🚨 UPDATED: Current wallet value $763
    MIN_TRADE_USD: float = 10.0            # Minimum viable trade size
    RESERVE_PERCENTAGE: float = 0.15       # Keep 15% in reserve

    @property
    def MAX_TRADE_USD(self) -> float:
        """Calculate max trade USD based on capital and percentage."""
        return self.TOTAL_CAPITAL_USD * self.MAX_TRADE_PERCENTAGE
    
    # ============================================================================
    # ⛽ MEV COMPETITIVE GAS SETTINGS - BEAT OTHER BOTS! 🔥
    # ============================================================================
    GAS_PRICE_MULTIPLIER: float = 4.0      # AGGRESSIVE: 4x gas to BEAT competitors
    MAX_GAS_PRICE_GWEI: float = 300.0      # MAXIMUM: Willing to pay up to 300 gwei for MEV
    MIN_GAS_PRICE_GWEI: float = 25.0       # COMPETITIVE: Start above typical users (was 15.0)
    FIXED_GAS_LIMIT: int = 400000          # Skip gas estimation for speed
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
    SCAN_INTERVAL_SECONDS: float = 0.5     # SPEED BOOST: Scan every 0.5 seconds
    OPPORTUNITY_MAX_AGE_SECONDS: float = 15.0  # Opportunities expire after 15s
    MAX_EXECUTION_TIME_SECONDS: float = 3.0    # SPEED BOOST: Ultra-fast 3s execution target
    RETRY_ATTEMPTS: int = 3                # Number of retry attempts
    RETRY_DELAY_SECONDS: float = 1.0       # Delay between retries
    
    # ============================================================================
    # 🌐 NETWORK PREFERENCES
    # ============================================================================
    PREFERRED_NETWORKS: List[str] = field(default_factory=lambda: [
        "ethereum",     # 🔥 PRIMARY: Your local node + flashloans!
        "arbitrum",     # Secondary network (lowest gas)
        "base",         # Tertiary network
        "optimism"      # Quaternary network
    ])

    NETWORK_CONFIGS: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        'ethereum': {
            'chain_id': 1,
            'gas_multiplier': 1.2,  # Conservative for mainnet
            'min_gas_gwei': 15.0,   # Mainnet minimum
            'priority_fee_gwei': 2.0,
            'flashloan_enabled': True  # 🔥 FLASHLOANS AVAILABLE!
        },
        'arbitrum': {
            'chain_id': 42161,
            'gas_multiplier': 2.0,
            'min_gas_gwei': 1.0,  # Fixed: 1.0 gwei minimum for current network conditions
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
            'min_gas_gwei': 0.5,  # Fixed: 0.5 gwei minimum for current network conditions
            'priority_fee_gwei': 1.2
        }
    })
    
    # ============================================================================
    # 🎯 TARGET TOKENS (Focus on what you hold)
    # ============================================================================
    TARGET_TOKENS: List[str] = field(default_factory=lambda: [
        "ETH", "WETH",      # Your primary holdings
        "USDC", "USDC.e",   # Your stablecoins (USDC.e is your MAJOR holding!)
        "USDT", "DAI"       # Additional stablecoins
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
    # 🎯 TOKEN CONVERSION RATIOS - NO MORE HARDCODED VALUES!
    # ============================================================================
    OTHER_TOKEN_TO_ETH_RATIO: float = 0.0003  # Conservative ratio for unknown tokens
    MIN_ETH_FOR_GAS: float = 0.005          # Minimum ETH needed for gas
    MIN_TRADE_ETH: float = 0.0001           # Minimum trade amount in ETH
    
    # ============================================================================
    # 🚨 CIRCUIT BREAKER SETTINGS
    # ============================================================================
    MAX_CONSECUTIVE_LOSSES: int = 5        # Stop after 5 losses
    MAX_DAILY_LOSS_PERCENTAGE: float = 10.0  # Stop at 10% daily loss

    # 🛡️ AUTO-SHUTDOWN PROTECTION - Any negative return = failed transaction
    MAX_FAILED_TRANSACTIONS: int = 25      # Auto-shutdown after 25 failed (negative return) transactions
    FAILED_TRANSACTION_RESET_HOURS: int = 1  # Reset failure counter every hour

    # ============================================================================
    # 🔥 FLASHLOAN CONFIGURATION - PROFITABLE TRADES ONLY!
    # ============================================================================
    ENABLE_FLASHLOANS: bool = True          # Enable flashloan arbitrage
    MIN_FLASHLOAN_PROFIT_USD: float = 50.0  # 🎯 RAISED: $50 minimum flashloan profit - NO MORE LOSSES!
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
    # 📊 DYNAMIC CALCULATED PROPERTIES (NO MORE HARDCODED $3000!)
    # ============================================================================
    async def get_max_trade_amount_eth(self, dynamic_data_service) -> float:
        """Calculate max trade amount in ETH using REAL ETH price."""
        eth_price = await dynamic_data_service.get_eth_price_usd()
        return self.MAX_TRADE_USD / eth_price

    async def get_daily_loss_limit_eth(self, dynamic_data_service) -> float:
        """Calculate daily loss limit in ETH using REAL ETH price."""
        eth_price = await dynamic_data_service.get_eth_price_usd()
        return self.DAILY_LOSS_LIMIT_USD / eth_price

    async def get_current_wallet_value_usd(self, dynamic_data_service, wallet_address: str) -> float:
        """Get REAL-TIME wallet value instead of hardcoded $763."""
        return await dynamic_data_service.get_total_wallet_value_usd(wallet_address)

    async def get_dynamic_max_trade_usd(self, dynamic_data_service, wallet_address: str) -> float:
        """Calculate max trade USD based on REAL wallet value."""
        real_wallet_value = await self.get_current_wallet_value_usd(dynamic_data_service, wallet_address)
        return real_wallet_value * self.MAX_TRADE_PERCENTAGE
    
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
