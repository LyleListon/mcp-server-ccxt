"""
MayArbi Data Coordination Package
System Integration Plan #3 - Data Flow Coordination

This package provides comprehensive data flow management for all MayArbi components.
"""

from .data_flow_coordinator import (
    DataFlowCoordinator,
    DataPacket,
    DataFlow,
    ComponentDataInterface,
    DataFlowType,
    DataPriority,
    FlowDirection,
    DataState
)

__all__ = [
    'DataFlowCoordinator',
    'DataPacket',
    'DataFlow',
    'ComponentDataInterface',
    'DataFlowType',
    'DataPriority',
    'FlowDirection',
    'DataState'
]

__version__ = '1.0.0'
__author__ = 'MayArbi System Integration Team'
