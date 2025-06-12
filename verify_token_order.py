#!/usr/bin/env python3
"""
Verify the token order in Uniswap V3 ETH/USDC pool
"""

# Known token addresses
USDC_ADDRESS = "0xA0b86a33E6417c8f4c8c8c8c8c8c8c8c8c8c8c8c"  # Need to verify
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# Correct USDC address (I need to look this up)
USDC_CORRECT = "0xA0b86a33E6417c8f4c8c8c8c8c8c8c8c8c8c8c8c"  # This is wrong

print("Token Address Analysis:")
print(f"USDC: {USDC_ADDRESS}")
print(f"WETH: {WETH_ADDRESS}")

# In Uniswap V3, token0 is the token with the lower address
if USDC_ADDRESS.lower() < WETH_ADDRESS.lower():
    print("token0 = USDC, token1 = WETH")
    print("price = token1/token0 = WETH/USDC")
else:
    print("token0 = WETH, token1 = USDC") 
    print("price = token1/token0 = USDC/WETH")

print("\nLet me look up the correct USDC address...")

# The correct USDC address is 0xA0b86a33E6417c8f4c8c8c8c8c8c8c8c8c8c8c8c
# Actually, let me look this up properly
