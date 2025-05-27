"""Simple path finder for arbitrage opportunities without networkx dependency."""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any

logger = logging.getLogger(__name__)


class SimplePathFinder:
    """Simple path finder for arbitrage opportunities."""
    
    def __init__(self, max_path_length: int = 3):
        """Initialize the path finder.
        
        Args:
            max_path_length: Maximum number of hops in a path.
        """
        self.max_path_length = max_path_length
        self.pairs = {}
        self.tokens = set()
    
    def update_graph(self, market_data: Dict[str, Any]) -> None:
        """Update the graph with market data.
        
        Args:
            market_data: Market data containing pairs information.
        """
        # Clear existing data
        self.pairs.clear()
        self.tokens.clear()
        
        # Process pairs
        for pair in market_data.get("pairs", []):
            base_token = pair.get("base_token")
            quote_token = pair.get("quote_token")
            dex = pair.get("dex")
            price = pair.get("price")
            liquidity = pair.get("liquidity")
            
            if not all([base_token, quote_token, dex, price is not None, liquidity is not None]):
                logger.warning(f"Skipping pair with missing data: {pair}")
                continue
            
            # Add tokens
            self.tokens.add(base_token)
            self.tokens.add(quote_token)
            
            # Store pair information
            pair_key = f"{base_token}-{quote_token}-{dex}"
            self.pairs[pair_key] = {
                'base_token': base_token,
                'quote_token': quote_token,
                'dex': dex,
                'price': price,
                'liquidity': liquidity,
                'reverse_price': 1.0 / price if price > 0 else 0
            }
            
            # Also store reverse pair
            reverse_key = f"{quote_token}-{base_token}-{dex}"
            self.pairs[reverse_key] = {
                'base_token': quote_token,
                'quote_token': base_token,
                'dex': dex,
                'price': 1.0 / price if price > 0 else 0,
                'liquidity': liquidity,
                'reverse_price': price
            }
        
        logger.info(f"Updated graph with {len(self.pairs)} pairs and {len(self.tokens)} tokens")
    
    def find_arbitrage_paths(self, start_token: str, min_profit_threshold: float = 0.01) -> List[Dict[str, Any]]:
        """Find arbitrage paths starting from a specific token.
        
        Args:
            start_token: Token to start arbitrage from
            min_profit_threshold: Minimum profit threshold (as decimal)
            
        Returns:
            List of arbitrage paths
        """
        if start_token not in self.tokens:
            logger.warning(f"Token {start_token} not found in market data")
            return []
        
        paths = []
        
        # Find simple arbitrage (2-hop: A -> B -> A)
        paths.extend(self._find_simple_arbitrage(start_token, min_profit_threshold))
        
        # Find triangular arbitrage (3-hop: A -> B -> C -> A)
        if self.max_path_length >= 3:
            paths.extend(self._find_triangular_arbitrage(start_token, min_profit_threshold))
        
        # Sort by profit potential
        paths.sort(key=lambda x: x.get('profit_ratio', 0), reverse=True)
        
        return paths
    
    def _find_simple_arbitrage(self, start_token: str, min_profit_threshold: float) -> List[Dict[str, Any]]:
        """Find simple arbitrage opportunities (A -> B -> A)."""
        paths = []
        
        # Get all tokens we can trade to from start_token
        intermediate_tokens = self._get_tradeable_tokens(start_token)
        
        for intermediate_token in intermediate_tokens:
            if intermediate_token == start_token:
                continue
            
            # Find path: start_token -> intermediate_token -> start_token
            forward_pairs = self._get_pairs_for_trade(start_token, intermediate_token)
            backward_pairs = self._get_pairs_for_trade(intermediate_token, start_token)
            
            for forward_pair in forward_pairs:
                for backward_pair in backward_pairs:
                    # Calculate profit
                    profit_ratio = self._calculate_path_profit([forward_pair, backward_pair])
                    
                    if profit_ratio > (1.0 + min_profit_threshold):
                        path = {
                            'type': 'simple',
                            'tokens': [start_token, intermediate_token, start_token],
                            'pairs': [forward_pair, backward_pair],
                            'dexs': [forward_pair['dex'], backward_pair['dex']],
                            'profit_ratio': profit_ratio,
                            'profit_percentage': (profit_ratio - 1.0) * 100,
                            'path_length': 2
                        }
                        paths.append(path)
        
        return paths
    
    def _find_triangular_arbitrage(self, start_token: str, min_profit_threshold: float) -> List[Dict[str, Any]]:
        """Find triangular arbitrage opportunities (A -> B -> C -> A)."""
        paths = []
        
        # Get all possible intermediate tokens
        intermediate_tokens_1 = self._get_tradeable_tokens(start_token)
        
        for token_b in intermediate_tokens_1:
            if token_b == start_token:
                continue
            
            intermediate_tokens_2 = self._get_tradeable_tokens(token_b)
            
            for token_c in intermediate_tokens_2:
                if token_c == start_token or token_c == token_b:
                    continue
                
                # Check if we can trade back to start_token
                if not self._can_trade(token_c, start_token):
                    continue
                
                # Find pairs for each leg
                pairs_ab = self._get_pairs_for_trade(start_token, token_b)
                pairs_bc = self._get_pairs_for_trade(token_b, token_c)
                pairs_ca = self._get_pairs_for_trade(token_c, start_token)
                
                for pair_ab in pairs_ab:
                    for pair_bc in pairs_bc:
                        for pair_ca in pairs_ca:
                            # Calculate profit
                            profit_ratio = self._calculate_path_profit([pair_ab, pair_bc, pair_ca])
                            
                            if profit_ratio > (1.0 + min_profit_threshold):
                                path = {
                                    'type': 'triangular',
                                    'tokens': [start_token, token_b, token_c, start_token],
                                    'pairs': [pair_ab, pair_bc, pair_ca],
                                    'dexs': [pair_ab['dex'], pair_bc['dex'], pair_ca['dex']],
                                    'profit_ratio': profit_ratio,
                                    'profit_percentage': (profit_ratio - 1.0) * 100,
                                    'path_length': 3
                                }
                                paths.append(path)
        
        return paths
    
    def _get_tradeable_tokens(self, from_token: str) -> Set[str]:
        """Get all tokens that can be traded to from the given token."""
        tradeable = set()
        
        for pair_key, pair_data in self.pairs.items():
            if pair_data['base_token'] == from_token:
                tradeable.add(pair_data['quote_token'])
        
        return tradeable
    
    def _can_trade(self, from_token: str, to_token: str) -> bool:
        """Check if we can trade from one token to another."""
        for pair_data in self.pairs.values():
            if pair_data['base_token'] == from_token and pair_data['quote_token'] == to_token:
                return True
        return False
    
    def _get_pairs_for_trade(self, from_token: str, to_token: str) -> List[Dict[str, Any]]:
        """Get all pairs that allow trading from one token to another."""
        pairs = []
        
        for pair_data in self.pairs.values():
            if pair_data['base_token'] == from_token and pair_data['quote_token'] == to_token:
                pairs.append(pair_data)
        
        return pairs
    
    def _calculate_path_profit(self, pairs: List[Dict[str, Any]]) -> float:
        """Calculate the profit ratio for a trading path."""
        if not pairs:
            return 1.0
        
        # Start with 1 unit of the first token
        amount = 1.0
        
        # Execute each trade in the path
        for pair in pairs:
            price = pair.get('price', 0)
            if price <= 0:
                return 0.0  # Invalid price
            
            # Apply price (accounting for liquidity would be more complex)
            amount *= price
            
            # Simple slippage simulation (reduce by 0.1% per trade)
            amount *= 0.999
        
        return amount
    
    def get_all_tokens(self) -> Set[str]:
        """Get all available tokens."""
        return self.tokens.copy()
    
    def get_pair_count(self) -> int:
        """Get number of trading pairs."""
        return len(self.pairs)
    
    def get_dex_list(self) -> Set[str]:
        """Get list of all DEXs."""
        dexs = set()
        for pair_data in self.pairs.values():
            dexs.add(pair_data['dex'])
        return dexs
