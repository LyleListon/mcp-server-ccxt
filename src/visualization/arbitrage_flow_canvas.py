#!/usr/bin/env python3
"""
🎨 ARBITRAGE FLOW CANVAS 🎨
Beautiful real-time visualization of arbitrage trade flows

The most artistic trading interface ever created!
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import websockets
import threading
from queue import Queue

logger = logging.getLogger(__name__)

@dataclass
class FlowParticle:
    """A single particle representing money flow."""
    id: str
    source_dex: str
    target_dex: str
    token: str
    amount_usd: float
    profit_usd: float
    color: str
    speed: float
    timestamp: float
    status: str  # 'flowing', 'completed', 'failed'
    path_progress: float = 0.0  # 0.0 to 1.0

@dataclass
class DEXNode:
    """A DEX node in the visualization."""
    name: str
    chain: str
    address: str
    position: Dict[str, float]  # x, y coordinates
    activity_level: float = 0.0  # 0.0 to 1.0
    total_volume_24h: float = 0.0
    successful_trades: int = 0
    failed_trades: int = 0
    last_activity: float = 0.0

class ArbitrageFlowCanvas:
    """🎨 The main artistic canvas for arbitrage visualization."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the artistic canvas."""
        self.config = config or {}
        self.dex_nodes: Dict[str, DEXNode] = {}
        self.active_flows: Dict[str, FlowParticle] = {}
        self.completed_flows: List[FlowParticle] = []
        self.websocket_clients: List = []
        self.flow_queue = Queue()
        
        # Artistic settings
        self.canvas_width = 1200
        self.canvas_height = 800
        self.particle_lifetime = 30.0  # seconds
        self.max_particles = 100
        
        # Color palette for different profit levels
        self.profit_colors = {
            'high': '#00ff88',      # Bright green for high profit
            'medium': '#88ff00',    # Yellow-green for medium profit  
            'low': '#ffff00',       # Yellow for low profit
            'loss': '#ff4444',      # Red for losses
            'pending': '#4488ff'    # Blue for pending
        }
        
        logger.info("🎨 Arbitrage Flow Canvas initialized")
    
    def add_dex_node(self, name: str, chain: str, address: str, position: Dict[str, float] = None):
        """Add a DEX node to the canvas."""
        if position is None:
            # Auto-position based on existing nodes
            position = self._calculate_auto_position(name, chain)
        
        self.dex_nodes[f"{chain}_{name}"] = DEXNode(
            name=name,
            chain=chain,
            address=address,
            position=position
        )
        
        logger.info(f"🎯 Added DEX node: {name} on {chain}")
    
    def _calculate_auto_position(self, name: str, chain: str) -> Dict[str, float]:
        """Calculate automatic positioning for DEX nodes."""
        # Chain-based positioning
        chain_positions = {
            'arbitrum': {'base_x': 200, 'base_y': 200},
            'base': {'base_x': 600, 'base_y': 200},
            'optimism': {'base_x': 1000, 'base_y': 200}
        }
        
        base_pos = chain_positions.get(chain, {'base_x': 400, 'base_y': 400})
        
        # Count existing nodes on this chain
        chain_nodes = [node for node in self.dex_nodes.values() if node.chain == chain]
        node_count = len(chain_nodes)
        
        # Arrange in a circle around the base position
        import math
        angle = (node_count * 2 * math.pi) / 8  # Assume max 8 DEXes per chain
        radius = 150
        
        x = base_pos['base_x'] + radius * math.cos(angle)
        y = base_pos['base_y'] + radius * math.sin(angle)
        
        return {'x': x, 'y': y}
    
    def add_arbitrage_flow(self, opportunity: Dict[str, Any]):
        """🌊 Add a new arbitrage flow to the canvas."""
        try:
            # Extract flow information
            flow_id = opportunity.get('id', f"flow_{int(time.time())}")
            source_dex = opportunity.get('buy_dex', 'unknown')
            target_dex = opportunity.get('sell_dex', 'unknown')
            token = opportunity.get('token', 'UNKNOWN')
            amount_usd = opportunity.get('trade_amount_usd', 0.0)
            profit_usd = opportunity.get('net_profit_usd', 0.0)
            
            # Determine color based on profit
            color = self._get_profit_color(profit_usd)
            
            # Calculate speed based on urgency/profit
            speed = self._calculate_flow_speed(profit_usd, amount_usd)
            
            # Create flow particle
            particle = FlowParticle(
                id=flow_id,
                source_dex=source_dex,
                target_dex=target_dex,
                token=token,
                amount_usd=amount_usd,
                profit_usd=profit_usd,
                color=color,
                speed=speed,
                timestamp=time.time(),
                status='flowing'
            )
            
            # Add to active flows
            self.active_flows[flow_id] = particle
            
            # Update DEX activity
            self._update_dex_activity(source_dex, target_dex, amount_usd)
            
            # Queue for websocket broadcast
            self.flow_queue.put({
                'type': 'new_flow',
                'data': asdict(particle)
            })
            
            logger.info(f"🌊 Added flow: {token} ${amount_usd:.2f} profit ${profit_usd:.2f}")
            
        except Exception as e:
            logger.error(f"Error adding arbitrage flow: {e}")
    
    def _get_profit_color(self, profit_usd: float) -> str:
        """Get color based on profit level."""
        if profit_usd > 50:
            return self.profit_colors['high']
        elif profit_usd > 10:
            return self.profit_colors['medium']
        elif profit_usd > 0:
            return self.profit_colors['low']
        else:
            return self.profit_colors['loss']
    
    def _calculate_flow_speed(self, profit_usd: float, amount_usd: float) -> float:
        """Calculate flow speed based on opportunity characteristics."""
        # Higher profit = faster flow
        profit_factor = min(profit_usd / 100.0, 2.0)  # Cap at 2x speed
        
        # Larger amounts = slightly faster
        amount_factor = min(amount_usd / 1000.0, 1.5)  # Cap at 1.5x speed
        
        base_speed = 1.0
        return base_speed * (1.0 + profit_factor + amount_factor * 0.2)
    
    def _update_dex_activity(self, source_dex: str, target_dex: str, amount_usd: float):
        """Update DEX node activity levels."""
        current_time = time.time()
        
        # Update source DEX
        for node_key, node in self.dex_nodes.items():
            if source_dex in node_key:
                node.activity_level = min(node.activity_level + 0.1, 1.0)
                node.total_volume_24h += amount_usd
                node.last_activity = current_time
                break
        
        # Update target DEX
        for node_key, node in self.dex_nodes.items():
            if target_dex in node_key:
                node.activity_level = min(node.activity_level + 0.1, 1.0)
                node.total_volume_24h += amount_usd
                node.last_activity = current_time
                break
    
    def update_flow_status(self, flow_id: str, status: str, actual_profit: float = None):
        """Update the status of a flow (completed, failed, etc.)."""
        if flow_id in self.active_flows:
            particle = self.active_flows[flow_id]
            particle.status = status
            
            if actual_profit is not None:
                particle.profit_usd = actual_profit
                particle.color = self._get_profit_color(actual_profit)
            
            # Move to completed flows if done
            if status in ['completed', 'failed']:
                self.completed_flows.append(particle)
                del self.active_flows[flow_id]
                
                # Update DEX success/failure counts
                self._update_dex_stats(particle, status == 'completed')
            
            # Broadcast update
            self.flow_queue.put({
                'type': 'flow_update',
                'data': asdict(particle)
            })
    
    def _update_dex_stats(self, particle: FlowParticle, success: bool):
        """Update DEX success/failure statistics."""
        for node_key, node in self.dex_nodes.items():
            if particle.source_dex in node_key or particle.target_dex in node_key:
                if success:
                    node.successful_trades += 1
                else:
                    node.failed_trades += 1
    
    async def start_animation_loop(self):
        """🎭 Start the main animation loop."""
        logger.info("🎭 Starting animation loop...")
        
        while True:
            try:
                current_time = time.time()
                
                # Update particle positions
                for particle in list(self.active_flows.values()):
                    # Update progress based on speed and time
                    elapsed = current_time - particle.timestamp
                    particle.path_progress = min(elapsed * particle.speed / 5.0, 1.0)
                    
                    # Remove old particles
                    if elapsed > self.particle_lifetime:
                        particle.status = 'expired'
                        self.completed_flows.append(particle)
                        del self.active_flows[particle.id]
                
                # Decay DEX activity levels
                for node in self.dex_nodes.values():
                    if current_time - node.last_activity > 10.0:  # 10 seconds
                        node.activity_level = max(node.activity_level - 0.01, 0.0)
                
                # Broadcast canvas state
                await self._broadcast_canvas_state()
                
                # Clean up old completed flows
                cutoff_time = current_time - 300  # Keep 5 minutes of history
                self.completed_flows = [
                    flow for flow in self.completed_flows 
                    if flow.timestamp > cutoff_time
                ]
                
                await asyncio.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                logger.error(f"Animation loop error: {e}")
                await asyncio.sleep(1.0)
    
    async def _broadcast_canvas_state(self):
        """Broadcast current canvas state to all connected clients."""
        if not self.websocket_clients:
            return
        
        try:
            canvas_state = {
                'type': 'canvas_update',
                'timestamp': time.time(),
                'dex_nodes': {k: asdict(v) for k, v in self.dex_nodes.items()},
                'active_flows': {k: asdict(v) for k, v in self.active_flows.items()},
                'stats': {
                    'total_active_flows': len(self.active_flows),
                    'total_completed_flows': len(self.completed_flows),
                    'total_dex_nodes': len(self.dex_nodes)
                }
            }
            
            # Send to all connected clients
            disconnected_clients = []
            for client in self.websocket_clients:
                try:
                    await client.send(json.dumps(canvas_state))
                except:
                    disconnected_clients.append(client)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self.websocket_clients.remove(client)
                
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
    
    async def handle_websocket_connection(self, websocket, path):
        """Handle new websocket connections."""
        logger.info(f"🔌 New websocket connection: {websocket.remote_address}")
        self.websocket_clients.append(websocket)
        
        try:
            # Send initial canvas state
            initial_state = {
                'type': 'initial_state',
                'dex_nodes': {k: asdict(v) for k, v in self.dex_nodes.items()},
                'active_flows': {k: asdict(v) for k, v in self.active_flows.items()}
            }
            await websocket.send(json.dumps(initial_state))
            
            # Keep connection alive
            async for message in websocket:
                # Handle client messages if needed
                pass
                
        except Exception as e:
            logger.info(f"Websocket disconnected: {e}")
        finally:
            if websocket in self.websocket_clients:
                self.websocket_clients.remove(websocket)
    
    def load_dex_nodes_from_reports(self, reports_dir: str = "."):
        """🔍 Load DEX nodes from your discovery reports."""
        try:
            # Load from your CSV reports
            import csv
            
            chains = ['arbitrum', 'base', 'optimism']
            for chain in chains:
                csv_file = Path(reports_dir) / f"dex_report_{chain}.csv"
                if csv_file.exists():
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            dex_name = row.get('dex_name', 'unknown')
                            contract_type = row.get('contract_type', '')
                            address = row.get('contract_address', '')
                            
                            if contract_type == 'router' and dex_name != 'unknown':
                                self.add_dex_node(dex_name, chain, address)
            
            logger.info(f"🎯 Loaded {len(self.dex_nodes)} DEX nodes from reports")
            
        except Exception as e:
            logger.error(f"Error loading DEX nodes: {e}")

# Global canvas instance
canvas = ArbitrageFlowCanvas()

def initialize_canvas_with_discovered_dexes():
    """🎨 Initialize canvas with your discovered DEXes."""
    canvas.load_dex_nodes_from_reports()
    return canvas
