"""
Transaction Security Validator

Critical security module for validating all transaction parameters
before execution to prevent loss of funds.
"""

import re
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from web3 import Web3

logger = logging.getLogger(__name__)

class TransactionSecurityValidator:
    """Validates transaction security before execution."""
    
    def __init__(self):
        self.max_gas_price_gwei = 100  # Emergency brake
        self.max_trade_amount_usd = 1000  # Hard limit
        self.min_trade_amount_usd = 1  # Minimum viable
        self.max_slippage_percent = 5.0  # 5% max slippage
        
        # Known malicious addresses (add as discovered)
        self.blacklisted_addresses = set([
            # Add known malicious contract addresses here
        ])
        
        # Trusted router addresses only
        self.trusted_routers = {
            'arbitrum': {
                '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',  # Uniswap V3
                '0xc873fEcbd354f5A56E00E710B90EF4201db2448d',  # Camelot
                '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506',  # SushiSwap
                '0xAAA87963EFeB6f7E0a2711F397663105Acb1805e',  # Ramses
            }
        }
    
    def validate_transaction(self, transaction: Dict[str, Any], network: str) -> Dict[str, Any]:
        """
        Comprehensive transaction validation.
        
        Returns:
            Dict with 'valid': bool and 'errors': List[str]
        """
        errors = []
        
        try:
            # 1. Validate basic transaction structure
            structure_errors = self._validate_transaction_structure(transaction)
            errors.extend(structure_errors)
            
            # 2. Validate addresses
            address_errors = self._validate_addresses(transaction, network)
            errors.extend(address_errors)
            
            # 3. Validate amounts and limits
            amount_errors = self._validate_amounts(transaction)
            errors.extend(amount_errors)
            
            # 4. Validate gas parameters
            gas_errors = self._validate_gas_parameters(transaction)
            errors.extend(gas_errors)
            
            # 5. Validate slippage protection
            slippage_errors = self._validate_slippage_protection(transaction)
            errors.extend(slippage_errors)
            
            # 6. Check for suspicious patterns
            pattern_errors = self._check_suspicious_patterns(transaction)
            errors.extend(pattern_errors)
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("✅ Transaction passed all security validations")
            else:
                logger.error(f"❌ Transaction failed validation: {errors}")
            
            return {
                'valid': is_valid,
                'errors': errors,
                'warnings': []  # Could add warnings for risky but valid transactions
            }
            
        except Exception as e:
            logger.error(f"Security validation error: {e}")
            return {
                'valid': False,
                'errors': [f"Validation system error: {str(e)}"],
                'warnings': []
            }
    
    def _validate_transaction_structure(self, transaction: Dict[str, Any]) -> List[str]:
        """Validate basic transaction structure."""
        errors = []
        
        required_fields = ['to', 'value', 'gas', 'gasPrice', 'from']
        for field in required_fields:
            if field not in transaction:
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def _validate_addresses(self, transaction: Dict[str, Any], network: str) -> List[str]:
        """Validate all addresses in transaction."""
        errors = []
        
        # Validate 'to' address (router)
        to_address = transaction.get('to', '').lower()
        if not self._is_valid_ethereum_address(to_address):
            errors.append(f"Invalid 'to' address: {to_address}")
        
        # Check if router is trusted
        trusted_routers = self.trusted_routers.get(network, set())
        if to_address not in {addr.lower() for addr in trusted_routers}:
            errors.append(f"Untrusted router address: {to_address}")
        
        # Check blacklist
        if to_address in self.blacklisted_addresses:
            errors.append(f"Blacklisted address detected: {to_address}")
        
        # Validate 'from' address
        from_address = transaction.get('from', '').lower()
        if not self._is_valid_ethereum_address(from_address):
            errors.append(f"Invalid 'from' address: {from_address}")
        
        return errors
    
    def _validate_amounts(self, transaction: Dict[str, Any]) -> List[str]:
        """Validate transaction amounts."""
        errors = []
        
        try:
            value_wei = int(transaction.get('value', 0))
            value_eth = Web3.from_wei(value_wei, 'ether')
            
            # Rough USD conversion (should use real price feed)
            eth_price_usd = 3000  # Conservative estimate
            value_usd = float(value_eth) * eth_price_usd
            
            # Check maximum trade size
            if value_usd > self.max_trade_amount_usd:
                errors.append(f"Trade amount ${value_usd:.2f} exceeds maximum ${self.max_trade_amount_usd}")
            
            # Check minimum trade size
            if value_usd < self.min_trade_amount_usd:
                errors.append(f"Trade amount ${value_usd:.2f} below minimum ${self.min_trade_amount_usd}")
            
            # Check for zero value (unless it's a token swap)
            if value_wei == 0:
                # This might be valid for token-to-token swaps
                logger.warning("Zero ETH value transaction - ensure this is intentional")
        
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid value format: {e}")
        
        return errors
    
    def _validate_gas_parameters(self, transaction: Dict[str, Any]) -> List[str]:
        """Validate gas parameters."""
        errors = []
        
        try:
            gas_limit = int(transaction.get('gas', 0))
            gas_price_wei = int(transaction.get('gasPrice', 0))
            gas_price_gwei = Web3.from_wei(gas_price_wei, 'gwei')
            
            # Check gas price limits
            if gas_price_gwei > self.max_gas_price_gwei:
                errors.append(f"Gas price {gas_price_gwei} gwei exceeds maximum {self.max_gas_price_gwei} gwei")
            
            # Check reasonable gas limits
            if gas_limit < 21000:
                errors.append(f"Gas limit {gas_limit} too low (minimum 21000)")
            
            if gas_limit > 1000000:
                errors.append(f"Gas limit {gas_limit} suspiciously high")
        
        except (ValueError, TypeError) as e:
            errors.append(f"Invalid gas parameters: {e}")
        
        return errors
    
    def _validate_slippage_protection(self, transaction: Dict[str, Any]) -> List[str]:
        """Validate slippage protection parameters."""
        errors = []
        
        # This would need to be enhanced based on the specific DEX function being called
        # For now, just check if transaction data exists
        data = transaction.get('data', '')
        if not data or data == '0x':
            errors.append("Missing transaction data - no function call specified")
        
        return errors
    
    def _check_suspicious_patterns(self, transaction: Dict[str, Any]) -> List[str]:
        """Check for suspicious transaction patterns."""
        errors = []
        
        # Check for unusual gas price patterns
        gas_price_wei = int(transaction.get('gasPrice', 0))
        gas_price_gwei = Web3.from_wei(gas_price_wei, 'gwei')
        
        # Flag extremely high gas prices (possible front-running attempt)
        if gas_price_gwei > 50:
            errors.append(f"Suspiciously high gas price: {gas_price_gwei} gwei")
        
        # Check transaction data for suspicious patterns
        data = transaction.get('data', '')
        if len(data) > 10000:  # Very long transaction data
            errors.append("Suspiciously long transaction data")
        
        return errors
    
    def _is_valid_ethereum_address(self, address: str) -> bool:
        """Validate Ethereum address format."""
        if not address:
            return False
        
        # Check basic format
        if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
            return False
        
        # Additional checksum validation could be added here
        return True
    
    def validate_private_key_usage(self, context: str) -> bool:
        """Validate that private key usage is appropriate for context."""
        
        # Private keys should only be used in specific, secure contexts
        allowed_contexts = [
            'transaction_signing',
            'wallet_initialization',
            'secure_testing'
        ]
        
        if context not in allowed_contexts:
            logger.error(f"❌ Private key usage not allowed in context: {context}")
            return False
        
        logger.info(f"✅ Private key usage validated for context: {context}")
        return True
