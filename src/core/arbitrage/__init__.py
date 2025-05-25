"""Core arbitrage module."""

# Import only working components
from .simple_path_finder import SimplePathFinder
from .simple_profit_calculator import SimpleProfitCalculator
from .simple_risk_analyzer import SimpleRiskAnalyzer

# Try to import enhanced engine, fallback if issues
try:
    from .enhanced_arbitrage_engine import EnhancedArbitrageEngine
    _enhanced_available = True
except ImportError:
    _enhanced_available = False

__all__ = [
    'SimplePathFinder',
    'SimpleProfitCalculator',
    'SimpleRiskAnalyzer'
]

if _enhanced_available:
    __all__.append('EnhancedArbitrageEngine')
