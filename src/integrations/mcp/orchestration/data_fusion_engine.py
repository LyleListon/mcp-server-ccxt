"""
Data Fusion Engine - Phase 3 Chunk 2

Intelligently combines data from multiple MCP sources with conflict resolution,
data validation, and priority-based selection for the arbitrage system.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

from .server_registry import MCPServerRegistry, ServerStatus, ServerType

logger = logging.getLogger(__name__)


class DataQuality(Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    PRIORITY_BASED = "priority_based"
    MAJORITY_VOTE = "majority_vote"
    NEWEST_WINS = "newest_wins"
    HIGHEST_QUALITY = "highest_quality"
    MERGE_ALL = "merge_all"


@dataclass
class DataSource:
    """Information about a data source."""
    server_id: str
    server_name: str
    capability: str
    priority: int
    quality_score: float = 1.0
    latency_ms: float = 0.0
    last_updated: Optional[datetime] = None
    reliability: float = 1.0  # 0.0 to 1.0


@dataclass
class FusedData:
    """Result of data fusion operation."""
    data: Any
    sources: List[DataSource]
    quality: DataQuality
    confidence: float
    fusion_strategy: ConflictResolution
    timestamp: datetime
    conflicts_detected: int = 0
    resolution_notes: List[str] = field(default_factory=list)


@dataclass
class FusionRequest:
    """Request for data fusion."""
    data_type: str
    query_params: Dict[str, Any]
    required_capabilities: List[str]
    preferred_servers: List[str] = field(default_factory=list)
    conflict_resolution: ConflictResolution = ConflictResolution.PRIORITY_BASED
    max_sources: int = 5
    timeout_seconds: float = 10.0
    quality_threshold: DataQuality = DataQuality.FAIR


class DataFusionEngine:
    """
    Intelligent data fusion engine for combining MCP server data.
    
    This is Chunk 2 of the Phase 3 MCP Orchestration Engine.
    """

    def __init__(self, server_registry: MCPServerRegistry, config: Dict[str, Any] = None):
        """Initialize the data fusion engine."""
        self.server_registry = server_registry
        self.config = config or {}
        
        # Fusion configuration
        self.default_timeout = self.config.get('default_timeout', 10.0)
        self.max_concurrent_requests = self.config.get('max_concurrent_requests', 10)
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5 minutes
        
        # Data cache for performance
        self.data_cache: Dict[str, Tuple[FusedData, datetime]] = {}
        
        # Quality scoring weights
        self.quality_weights = {
            'freshness': 0.3,      # How recent the data is
            'reliability': 0.25,   # Server reliability score
            'priority': 0.2,       # Server priority
            'latency': 0.15,       # Response time
            'completeness': 0.1    # Data completeness
        }

    async def fuse_data(self, request: FusionRequest) -> FusedData:
        """
        Fuse data from multiple MCP servers based on the request.
        
        Args:
            request: Fusion request with parameters and preferences
            
        Returns:
            FusedData: Combined and validated data from multiple sources
        """
        try:
            logger.info(f"Starting data fusion for {request.data_type}")
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                logger.debug(f"Returning cached data for {request.data_type}")
                return cached_data
            
            # Discover suitable servers
            suitable_servers = self._discover_servers(request)
            if not suitable_servers:
                raise ValueError(f"No suitable servers found for {request.data_type}")
            
            # Collect data from multiple sources
            source_data = await self._collect_source_data(suitable_servers, request)
            
            if not source_data:
                raise ValueError(f"No data collected for {request.data_type}")
            
            # Fuse the collected data
            fused_result = self._fuse_collected_data(source_data, request)
            
            # Cache the result
            self._cache_data(cache_key, fused_result)
            
            logger.info(f"Data fusion complete for {request.data_type}: "
                       f"{len(source_data)} sources, quality={fused_result.quality.value}")
            
            return fused_result
            
        except Exception as e:
            logger.error(f"Error in data fusion for {request.data_type}: {e}")
            # Return empty result with error information
            return FusedData(
                data=None,
                sources=[],
                quality=DataQuality.INVALID,
                confidence=0.0,
                fusion_strategy=request.conflict_resolution,
                timestamp=datetime.now(),
                resolution_notes=[f"Fusion failed: {str(e)}"]
            )

    def _discover_servers(self, request: FusionRequest) -> List[DataSource]:
        """Discover servers suitable for the fusion request."""
        suitable_servers = []
        
        # Get servers by required capabilities
        for capability in request.required_capabilities:
            servers = self.server_registry.get_servers_by_capability(capability)
            
            for server in servers:
                # Only include connected servers
                if server.status != ServerStatus.CONNECTED:
                    continue
                
                # Check if server is preferred
                is_preferred = server.server_id in request.preferred_servers
                
                # Calculate priority (lower number = higher priority)
                effective_priority = server.priority
                if is_preferred:
                    effective_priority -= 1  # Boost preferred servers
                
                # Find the specific capability
                server_capability = None
                for cap in server.capabilities:
                    if cap.name == capability:
                        server_capability = cap
                        break
                
                if server_capability:
                    data_source = DataSource(
                        server_id=server.server_id,
                        server_name=server.name,
                        capability=capability,
                        priority=effective_priority,
                        reliability=self._calculate_server_reliability(server)
                    )
                    suitable_servers.append(data_source)
        
        # Sort by priority and limit to max_sources
        suitable_servers.sort(key=lambda x: (x.priority, -x.reliability))
        return suitable_servers[:request.max_sources]

    def _calculate_server_reliability(self, server) -> float:
        """Calculate server reliability score based on historical performance."""
        # Base reliability
        reliability = 1.0
        
        # Reduce based on recent errors
        if server.connection_attempts > 0:
            reliability *= max(0.1, 1.0 - (server.connection_attempts * 0.2))
        
        # Consider uptime
        if server.uptime_start:
            uptime = datetime.now() - server.uptime_start
            if uptime < timedelta(minutes=5):
                reliability *= 0.8  # Recently connected, slightly less reliable
        
        return max(0.0, min(1.0, reliability))

    async def _collect_source_data(self, sources: List[DataSource], 
                                 request: FusionRequest) -> List[Tuple[DataSource, Any]]:
        """Collect data from multiple sources concurrently."""
        tasks = []
        
        for source in sources:
            task = asyncio.create_task(
                self._fetch_from_source(source, request),
                name=f"fetch_{source.server_id}"
            )
            tasks.append((source, task))
        
        # Wait for all tasks with timeout
        source_data = []
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                timeout=request.timeout_seconds
            )
            
            for i, result in enumerate(results):
                source = tasks[i][0]
                if isinstance(result, Exception):
                    logger.warning(f"Error fetching from {source.server_id}: {result}")
                    continue
                
                if result is not None:
                    source_data.append((source, result))
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout collecting data for {request.data_type}")
        
        return source_data

    async def _fetch_from_source(self, source: DataSource, request: FusionRequest) -> Any:
        """Fetch data from a specific source."""
        start_time = datetime.now()
        
        try:
            # This is a placeholder for actual MCP server communication
            # In real implementation, this would call the actual MCP server
            logger.debug(f"Fetching {request.data_type} from {source.server_id}")
            
            # TODO: Implement real MCP server communication
            # For now, return None to avoid mock data contamination
            logger.warning(f"Real MCP communication not implemented for {source.server_id}")

            # Update source metrics
            source.latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            source.last_updated = datetime.now()

            return None  # No mock data - implement real MCP communication
            
        except Exception as e:
            logger.error(f"Error fetching from {source.server_id}: {e}")
            return None

    # Mock data generation function removed to eliminate contamination
    # Real MCP server communication should be implemented instead

    def _fuse_collected_data(self, source_data: List[Tuple[DataSource, Any]], 
                           request: FusionRequest) -> FusedData:
        """Fuse data from multiple sources using the specified strategy."""
        if not source_data:
            return FusedData(
                data=None,
                sources=[],
                quality=DataQuality.INVALID,
                confidence=0.0,
                fusion_strategy=request.conflict_resolution,
                timestamp=datetime.now(),
                resolution_notes=["No source data available"]
            )
        
        # Analyze data for conflicts
        conflicts = self._detect_conflicts(source_data)
        
        # Apply fusion strategy
        if request.conflict_resolution == ConflictResolution.PRIORITY_BASED:
            fused_data = self._fuse_priority_based(source_data)
        elif request.conflict_resolution == ConflictResolution.MAJORITY_VOTE:
            fused_data = self._fuse_majority_vote(source_data)
        elif request.conflict_resolution == ConflictResolution.HIGHEST_QUALITY:
            fused_data = self._fuse_highest_quality(source_data)
        else:
            # Default to priority-based
            fused_data = self._fuse_priority_based(source_data)
        
        # Calculate overall quality and confidence
        quality = self._calculate_data_quality(source_data, conflicts)
        confidence = self._calculate_confidence(source_data, conflicts)
        
        return FusedData(
            data=fused_data,
            sources=[source for source, _ in source_data],
            quality=quality,
            confidence=confidence,
            fusion_strategy=request.conflict_resolution,
            timestamp=datetime.now(),
            conflicts_detected=len(conflicts),
            resolution_notes=[f"Fused data from {len(source_data)} sources"]
        )

    def _detect_conflicts(self, source_data: List[Tuple[DataSource, Any]]) -> List[str]:
        """Detect conflicts between data sources."""
        conflicts = []
        
        # Simple conflict detection for numeric values
        numeric_fields = {}
        for source, data in source_data:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        if key not in numeric_fields:
                            numeric_fields[key] = []
                        numeric_fields[key].append((source.server_id, value))
        
        # Check for significant differences
        for field, values in numeric_fields.items():
            if len(values) > 1:
                vals = [v[1] for v in values]
                if max(vals) - min(vals) > max(vals) * 0.05:  # 5% difference threshold
                    conflicts.append(f"Conflict in {field}: {values}")
        
        return conflicts

    def _fuse_priority_based(self, source_data: List[Tuple[DataSource, Any]]) -> Dict[str, Any]:
        """Fuse data using priority-based strategy (highest priority wins)."""
        # Sort by priority (lower number = higher priority)
        sorted_data = sorted(source_data, key=lambda x: x[0].priority)
        
        # Start with highest priority source
        fused = dict(sorted_data[0][1]) if sorted_data[0][1] else {}
        
        # Add missing fields from lower priority sources
        for source, data in sorted_data[1:]:
            if isinstance(data, dict):
                for key, value in data.items():
                    if key not in fused:
                        fused[key] = value
        
        return fused

    def _fuse_majority_vote(self, source_data: List[Tuple[DataSource, Any]]) -> Dict[str, Any]:
        """Fuse data using majority vote strategy."""
        # For simplicity, fall back to priority-based for now
        # In a full implementation, this would implement actual majority voting
        return self._fuse_priority_based(source_data)

    def _fuse_highest_quality(self, source_data: List[Tuple[DataSource, Any]]) -> Dict[str, Any]:
        """Fuse data using highest quality strategy."""
        # Sort by quality score
        sorted_data = sorted(source_data, key=lambda x: x[0].quality_score, reverse=True)
        return self._fuse_priority_based(sorted_data)

    def _calculate_data_quality(self, source_data: List[Tuple[DataSource, Any]], 
                              conflicts: List[str]) -> DataQuality:
        """Calculate overall data quality."""
        if not source_data:
            return DataQuality.INVALID
        
        # Base quality on number of sources and conflicts
        source_count = len(source_data)
        conflict_count = len(conflicts)
        
        if conflict_count == 0 and source_count >= 3:
            return DataQuality.EXCELLENT
        elif conflict_count <= 1 and source_count >= 2:
            return DataQuality.GOOD
        elif conflict_count <= 2:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR

    def _calculate_confidence(self, source_data: List[Tuple[DataSource, Any]], 
                            conflicts: List[str]) -> float:
        """Calculate confidence score for the fused data."""
        if not source_data:
            return 0.0
        
        # Base confidence on source reliability and conflicts
        avg_reliability = sum(source.reliability for source, _ in source_data) / len(source_data)
        conflict_penalty = min(0.5, len(conflicts) * 0.1)
        
        confidence = avg_reliability - conflict_penalty
        return max(0.0, min(1.0, confidence))

    def _generate_cache_key(self, request: FusionRequest) -> str:
        """Generate cache key for the request."""
        key_data = {
            'data_type': request.data_type,
            'query_params': request.query_params,
            'capabilities': sorted(request.required_capabilities),
            'servers': sorted(request.preferred_servers)
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_data(self, cache_key: str) -> Optional[FusedData]:
        """Get cached data if still valid."""
        if cache_key in self.data_cache:
            cached_data, cache_time = self.data_cache[cache_key]
            if datetime.now() - cache_time < timedelta(seconds=self.cache_ttl):
                return cached_data
            else:
                # Remove expired cache entry
                del self.data_cache[cache_key]
        return None

    def _cache_data(self, cache_key: str, data: FusedData) -> None:
        """Cache the fused data."""
        self.data_cache[cache_key] = (data, datetime.now())
        
        # Clean up old cache entries
        if len(self.data_cache) > 100:  # Limit cache size
            oldest_key = min(self.data_cache.keys(), 
                           key=lambda k: self.data_cache[k][1])
            del self.data_cache[oldest_key]

    async def fuse_arbitrage_data(self, tokens: List[str]) -> FusedData:
        """Convenience method to fuse arbitrage-related data."""
        request = FusionRequest(
            data_type='arbitrage_analysis',
            query_params={'tokens': tokens},
            required_capabilities=['arbitrage_memory', 'exchange_data'],
            conflict_resolution=ConflictResolution.PRIORITY_BASED,
            max_sources=3
        )
        return await self.fuse_data(request)

    async def fuse_market_data(self, pairs: List[str]) -> FusedData:
        """Convenience method to fuse market data."""
        request = FusionRequest(
            data_type='market_data',
            query_params={'pairs': pairs},
            required_capabilities=['exchange_data'],
            conflict_resolution=ConflictResolution.MAJORITY_VOTE,
            max_sources=5
        )
        return await self.fuse_data(request)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self.data_cache),
            'cache_ttl': self.cache_ttl,
            'oldest_entry': min(
                (cache_time for _, cache_time in self.data_cache.values()),
                default=None
            ),
            'newest_entry': max(
                (cache_time for _, cache_time in self.data_cache.values()),
                default=None
            )
        }
