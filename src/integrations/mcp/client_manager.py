"""
MCP Client Manager for Arbitrage Bot

Manages connections to all MCP servers and provides unified interface
for accessing memory, knowledge graph, web3 data, and other MCP services.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.utils.simple_data_storage import SimpleDataStorage

logger = logging.getLogger(__name__)


class MCPClientManager:
    """Manages all MCP server connections for the arbitrage bot."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize MCP client manager.

        Args:
            config: Configuration dictionary with MCP server settings
        """
        self.config = config
        self.clients = {}
        self.connected = False

        # Fallback storage for when MCP servers fail
        self.fallback_storage = SimpleDataStorage("data/arbitrage")

        # MCP Server configurations
        self.server_configs = {
            'dexmind': {
                'type': 'memory',
                'description': 'Custom memory server for arbitrage patterns',
                'required': True
            },
            'memory_service': {
                'type': 'memory',
                'description': 'General memory and pattern storage',
                'required': True
            },
            'knowledge_graph': {
                'type': 'graph',
                'description': 'Token and market relationship storage',
                'required': True
            },
            'coincap': {
                'type': 'market_data',
                'description': 'Real-time cryptocurrency price data',
                'required': True
            },
            'coinmarket': {
                'type': 'market_data',
                'description': 'Market cap and volume data',
                'required': True
            },
            'ccxt': {
                'type': 'exchange',
                'description': 'Exchange data and trading pairs',
                'required': True
            },
            'filescopemcp': {
                'type': 'organization',
                'description': 'Project file organization and tracking',
                'required': False
            }
        }

    async def connect_all(self) -> bool:
        """Connect to all configured MCP servers.

        Returns:
            bool: True if all required servers connected successfully
        """
        logger.info("Connecting to MCP servers...")

        connection_tasks = []
        for server_name, config in self.server_configs.items():
            task = asyncio.create_task(
                self._connect_server(server_name, config),
                name=f"connect_{server_name}"
            )
            connection_tasks.append(task)

        # Wait for all connections
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)

        # Check results
        connected_servers = []
        failed_servers = []

        for i, result in enumerate(results):
            server_name = list(self.server_configs.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to connect to {server_name}: {result}")
                failed_servers.append(server_name)
            elif result:
                connected_servers.append(server_name)
                logger.info(f"Successfully connected to {server_name}")
            else:
                failed_servers.append(server_name)

        # Check if all required servers are connected
        required_failed = [
            server for server in failed_servers
            if self.server_configs[server]['required']
        ]

        if required_failed:
            logger.error(f"Failed to connect to required servers: {required_failed}")
            self.connected = False
            return False

        self.connected = True
        logger.info(f"MCP integration ready. Connected: {connected_servers}")
        if failed_servers:
            logger.warning(f"Optional servers failed: {failed_servers}")

        return True

    async def _connect_server(self, server_name: str, config: Dict[str, Any]) -> bool:
        """Connect to a specific MCP server.

        Args:
            server_name: Name of the server to connect to
            config: Server configuration

        Returns:
            bool: True if connection successful
        """
        try:
            # This is a placeholder for actual MCP client connection
            # In real implementation, you would use the MCP client library
            logger.info(f"Connecting to {server_name} ({config['description']})")

            # Simulate connection delay
            await asyncio.sleep(0.1)

            # Store mock client for now
            self.clients[server_name] = {
                'type': config['type'],
                'connected': True,
                'last_ping': datetime.now()
            }

            return True

        except Exception as e:
            logger.error(f"Error connecting to {server_name}: {e}")
            return False

    async def store_arbitrage_pattern(self, opportunity: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Store successful arbitrage pattern in memory servers.

        Args:
            opportunity: The arbitrage opportunity data
            result: The execution result

        Returns:
            bool: True if stored successfully
        """
        # Always store in fallback storage first
        fallback_success = self.fallback_storage.store_arbitrage_pattern(opportunity, result)

        if not self.connected:
            logger.warning("MCP clients not connected, using fallback storage only")
            return fallback_success

        try:
            # Create pattern data with original opportunity and result preserved
            pattern_data = {
                'timestamp': datetime.now().isoformat(),
                'opportunity': opportunity,  # Preserve original opportunity structure
                'result': result,           # Preserve original result structure
                'tokens': opportunity.get('tokens', []),
                'dexs': opportunity.get('dexs', []),
                'profit_margin': result.get('profit', 0),
                'gas_used': result.get('gas_used', 0),
                'execution_time': result.get('execution_time', 0),
                'market_conditions': opportunity.get('market_conditions', {}),
                'success': result.get('success', False)
            }

            # Store in DexMind
            if 'dexmind' in self.clients:
                await self._store_in_dexmind(pattern_data)

            # Store in general memory service
            if 'memory_service' in self.clients:
                await self._store_in_memory_service(pattern_data)

            # Update knowledge graph
            if 'knowledge_graph' in self.clients:
                await self._update_knowledge_graph(pattern_data)

            logger.info("Arbitrage pattern stored successfully")
            return True

        except Exception as e:
            logger.error(f"Error storing arbitrage pattern: {e}")
            return False

    async def store_execution_result(self, opportunity: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Store execution result in memory servers.

        Args:
            opportunity: The arbitrage opportunity data
            result: The execution result

        Returns:
            bool: True if stored successfully
        """
        return await self.store_arbitrage_pattern(opportunity, result)

    async def _store_in_dexmind(self, pattern_data: Dict[str, Any]) -> None:
        """Store pattern in DexMind memory server."""
        if 'dexmind' not in self.clients:
            logger.warning("DexMind client not available")
            return

        try:
            # Extract trade data from pattern
            opportunity = pattern_data.get('opportunity', {})
            result = pattern_data.get('result', {})

            # Prepare trade data for DexMind - use correct field names
            trade_data = {
                'tokenA': opportunity.get('base_token', 'UNKNOWN'),
                'tokenB': opportunity.get('quote_token', 'UNKNOWN'),
                'dexA': opportunity.get('buy_dex', 'unknown'),
                'dexB': opportunity.get('sell_dex', 'unknown'),
                'chain': 'ethereum',  # Default to ethereum for now
                'priceA': opportunity.get('buy_price', 0),
                'priceB': opportunity.get('sell_price', 0),
                'profitUSD': result.get('profit', 0),
                'gasSpentUSD': result.get('gas_cost', 0.01),  # Estimate if not provided
                'wasExecuted': result.get('success', False)
            }

            # Call DexMind store_penny_trade tool
            await self._call_mcp_tool('dexmind', 'store_penny_trade', trade_data)
            logger.info(f"Stored trade in DexMind: {trade_data['tokenA']}/{trade_data['tokenB']}")

        except Exception as e:
            logger.error(f"Error storing pattern in DexMind: {e}")

    async def _store_in_memory_service(self, pattern_data: Dict[str, Any]) -> None:
        """Store pattern in general memory service."""
        if 'memory_service' not in self.clients:
            logger.warning("Memory service client not available")
            return

        try:
            # Extract key information from pattern
            opportunity = pattern_data.get('opportunity', {})
            result = pattern_data.get('result', {})

            # Create memory content - use correct field names
            base_token = opportunity.get('base_token', 'UNKNOWN')
            quote_token = opportunity.get('quote_token', 'UNKNOWN')
            buy_dex = opportunity.get('buy_dex', 'unknown')
            sell_dex = opportunity.get('sell_dex', 'unknown')
            profit = result.get('profit', 0)
            success = result.get('success', False)

            content = f"Arbitrage pattern: {base_token}/{quote_token} between {buy_dex} and {sell_dex}. "
            content += f"Profit: ${profit:.2f}, Success: {success}"

            # Store in memory service with tags
            metadata = {
                'tags': f"arbitrage,{base_token},{quote_token},{buy_dex},{sell_dex}",
                'type': 'arbitrage_pattern'
            }

            # Call memory service store tool
            await self._call_mcp_tool('memory_service', 'store_memory', {
                'content': content,
                'metadata': metadata
            })

            logger.info(f"Stored pattern in memory service: {base_token}/{quote_token}")

        except Exception as e:
            logger.error(f"Error storing pattern in memory service: {e}")

    async def _update_knowledge_graph(self, pattern_data: Dict[str, Any]) -> None:
        """Update knowledge graph with pattern relationships."""
        if 'knowledge_graph' not in self.clients:
            logger.warning("Knowledge graph client not available")
            return

        try:
            # Extract information from pattern - use correct field names
            opportunity = pattern_data.get('opportunity', {})
            result = pattern_data.get('result', {})

            base_token = opportunity.get('base_token', 'UNKNOWN')
            quote_token = opportunity.get('quote_token', 'UNKNOWN')
            buy_dex = opportunity.get('buy_dex', 'unknown')
            sell_dex = opportunity.get('sell_dex', 'unknown')
            profit = result.get('profit', 0)
            success = result.get('success', False)

            # Create entities for tokens and DEXs
            entities = [
                {
                    'name': base_token,
                    'entityType': 'Token',
                    'observations': [f"Used in arbitrage with profit ${profit:.2f}"]
                },
                {
                    'name': quote_token,
                    'entityType': 'Token',
                    'observations': [f"Used in arbitrage with profit ${profit:.2f}"]
                },
                {
                    'name': buy_dex,
                    'entityType': 'DEX',
                    'observations': [f"Arbitrage opportunity with {success} success"]
                },
                {
                    'name': sell_dex,
                    'entityType': 'DEX',
                    'observations': [f"Arbitrage opportunity with {success} success"]
                }
            ]

            # Create relations
            relations = [
                {
                    'from': base_token,
                    'to': quote_token,
                    'relationType': 'arbitrage_pair'
                },
                {
                    'from': buy_dex,
                    'to': sell_dex,
                    'relationType': 'price_difference'
                }
            ]

            # Store in knowledge graph
            if entities:
                await self._call_mcp_tool('knowledge_graph', 'create_entities', {'entities': entities})
            if relations:
                await self._call_mcp_tool('knowledge_graph', 'create_relations', {'relations': relations})

            logger.info(f"Updated knowledge graph with {len(entities)} entities and {len(relations)} relations")

        except Exception as e:
            logger.error(f"Error updating knowledge graph: {e}")

    async def get_market_data(self, tokens: List[str]) -> Dict[str, Any]:
        """Get real-time market data for specified tokens.

        Args:
            tokens: List of token symbols

        Returns:
            Dict containing market data from multiple sources
        """
        if not self.connected:
            logger.warning("MCP clients not connected, cannot get market data")
            return {}

        market_data = {}

        try:
            # Get data from Coincap
            if 'coincap' in self.clients:
                coincap_data = await self._get_coincap_data(tokens)
                market_data['coincap'] = coincap_data

            # Get data from Coinmarket
            if 'coinmarket' in self.clients:
                coinmarket_data = await self._get_coinmarket_data(tokens)
                market_data['coinmarket'] = coinmarket_data

            # Get exchange data from CCXT
            if 'ccxt' in self.clients:
                ccxt_data = await self._get_ccxt_data(tokens)
                market_data['ccxt'] = ccxt_data

            return market_data

        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {}

    async def _get_coincap_data(self, tokens: List[str]) -> Dict[str, Any]:
        """Get data from Coincap MCP server."""
        # Placeholder for Coincap data retrieval
        return {'source': 'coincap', 'tokens': tokens}

    async def _get_coinmarket_data(self, tokens: List[str]) -> Dict[str, Any]:
        """Get data from Coinmarket MCP server."""
        # Placeholder for Coinmarket data retrieval
        return {'source': 'coinmarket', 'tokens': tokens}

    async def _get_ccxt_data(self, tokens: List[str]) -> Dict[str, Any]:
        """Get data from CCXT MCP server."""
        # Placeholder for CCXT data retrieval
        return {'source': 'ccxt', 'tokens': tokens}

    async def get_similar_opportunities(self, current_opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get similar past opportunities from memory servers.

        Args:
            current_opportunity: Current opportunity to find similar patterns for

        Returns:
            List of similar opportunities from memory
        """
        if not self.connected:
            return []

        try:
            # Query memory servers for similar patterns
            similar_patterns = []

            if 'memory_service' in self.clients:
                query = f"arbitrage opportunities with tokens {current_opportunity.get('tokens', [])}"
                patterns = await self._query_memory_service(query)
                similar_patterns.extend(patterns)

            return similar_patterns

        except Exception as e:
            logger.error(f"Error getting similar opportunities: {e}")
            return []

    async def _query_memory_service(self, query: str) -> List[Dict[str, Any]]:
        """Query the memory service."""
        if 'memory_service' not in self.clients:
            logger.warning("Memory service client not available")
            return []

        try:
            # Call memory service retrieve tool
            result = await self._call_mcp_tool('memory_service', 'retrieve_memory', {
                'query': query,
                'n_results': 10
            })

            # Extract memories from result
            memories = result.get('memories', []) if isinstance(result, dict) else []
            logger.debug(f"Retrieved {len(memories)} memories for query: {query}")
            return memories

        except Exception as e:
            logger.error(f"Error querying memory service: {e}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all MCP connections.

        Returns:
            Dict with health status of each server
        """
        health_status = {}

        for server_name, client_info in self.clients.items():
            try:
                # Placeholder for actual health check
                health_status[server_name] = {
                    'connected': client_info.get('connected', False),
                    'last_ping': client_info.get('last_ping'),
                    'type': client_info.get('type')
                }
            except Exception as e:
                health_status[server_name] = {
                    'connected': False,
                    'error': str(e)
                }

        return health_status

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        logger.info("Disconnecting from MCP servers...")

        for server_name in list(self.clients.keys()):
            try:
                # Placeholder for actual disconnection
                del self.clients[server_name]
                logger.info(f"Disconnected from {server_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")

        self.connected = False
        logger.info("All MCP connections closed")

    async def _call_mcp_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool response
        """
        if server_name not in self.clients:
            raise ValueError(f"MCP server {server_name} not connected")

        try:
            # Get the client for this server
            client = self.clients[server_name]

            # For now, simulate the tool call since we don't have actual MCP client implementation
            # In a real implementation, this would be: result = await client.call_tool(tool_name, arguments)
            logger.info(f"Calling {tool_name} on {server_name} with args: {arguments}")

            # Simulate different responses based on tool type
            if tool_name == 'store_penny_trade':
                return {"success": True, "trade_id": f"trade_{datetime.now().timestamp()}"}
            elif tool_name == 'store_memory':
                return {"success": True, "memory_id": f"mem_{datetime.now().timestamp()}"}
            elif tool_name == 'create_entities':
                return {"success": True, "entities_created": len(arguments.get('entities', []))}
            elif tool_name == 'create_relations':
                return {"success": True, "relations_created": len(arguments.get('relations', []))}
            elif tool_name == 'retrieve_memory':
                return {"success": True, "memories": []}
            else:
                return {"success": True, "message": f"Called {tool_name} successfully"}

        except Exception as e:
            logger.error(f"Error calling {tool_name} on {server_name}: {e}")
            raise
