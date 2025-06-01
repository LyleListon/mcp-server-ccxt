"""
MayArbi Error Management Package
System Integration Plan #2 - Error Propagation & Recovery

This package provides comprehensive error handling for all MayArbi components.
"""

from .error_propagation_recovery import (
    ErrorPropagationRecovery,
    ErrorEvent,
    RecoveryAction,
    ComponentCircuitBreaker,
    ErrorSeverity,
    ErrorCategory,
    RecoveryStrategy,
    ComponentState
)

__all__ = [
    'ErrorPropagationRecovery',
    'ErrorEvent',
    'RecoveryAction', 
    'ComponentCircuitBreaker',
    'ErrorSeverity',
    'ErrorCategory',
    'RecoveryStrategy',
    'ComponentState'
]

__version__ = '1.0.0'
__author__ = 'MayArbi System Integration Team'
