#!/usr/bin/env python3
"""
Simplified MCP Memory Server that bypasses the complex wrapper.
This directly runs the memory service without the problematic PyTorch detection.
"""

import os
import sys
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the MCP memory service directly."""
    try:
        # Set environment variables for CUDA
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
        
        # Add the src directory to Python path
        src_dir = os.path.join(os.path.dirname(__file__), 'src')
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        logger.info("Starting simplified MCP Memory Service")
        
        # Import and run the server directly
        try:
            from mcp_memory_service.server import main as server_main
            logger.info("Successfully imported memory service server")
            
            # Run the server
            server_main()
            
        except ImportError as e:
            logger.error(f"Failed to import memory service: {e}")
            
            # Try alternative import path
            try:
                import mcp_memory_service.server as server
                logger.info("Using alternative import path")
                server.main()
            except ImportError as e2:
                logger.error(f"Alternative import also failed: {e2}")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Error running memory server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
