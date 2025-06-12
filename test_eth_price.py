#!/usr/bin/env python3
"""
Test ETH price calculation fix
"""

from web3 import Web3

def test_eth_price():
    """Test the fixed ETH price calculation"""
    
    # Connect to RPC
    rpcs = [
        'https://eth.llamarpc.com',
        'https://rpc.ankr.com/eth',
        'https://ethereum.publicnode.com'
    ]
    
    w3 = None
    for rpc in rpcs:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc))
            if w3.is_connected():
                print(f"✅ Connected to {rpc}")
                break
        except Exception as e:
            print(f"❌ Failed to connect to {rpc}: {e}")
            continue
    
    if not w3 or not w3.is_connected():
        print("❌ Could not connect to any RPC")
        return
    
    # Uniswap V3 ETH/USDC pool
    pool_address = '0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640'
    pool_abi = [
        {
            'inputs': [],
            'name': 'slot0',
            'outputs': [
                {'internalType': 'uint160', 'name': 'sqrtPriceX96', 'type': 'uint160'},
                {'internalType': 'int24', 'name': 'tick', 'type': 'int24'},
                {'internalType': 'uint16', 'name': 'observationIndex', 'type': 'uint16'},
                {'internalType': 'uint16', 'name': 'observationCardinality', 'type': 'uint16'},
                {'internalType': 'uint16', 'name': 'observationCardinalityNext', 'type': 'uint16'},
                {'internalType': 'uint8', 'name': 'feeProtocol', 'type': 'uint8'},
                {'internalType': 'bool', 'name': 'unlocked', 'type': 'bool'}
            ],
            'stateMutability': 'view',
            'type': 'function'
        }
    ]
    
    try:
        pool_contract = w3.eth.contract(address=pool_address, abi=pool_abi)
        slot0 = pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]
        
        print(f"\n📊 Uniswap V3 ETH/USDC Pool Data:")
        print(f"sqrtPriceX96: {sqrt_price_x96}")
        
        # OLD calculation (wrong)
        price_ratio_old = (sqrt_price_x96 / (2**96)) ** 2
        eth_price_old = (1 / price_ratio_old) * (10**12)
        
        # NEW calculation (fixed)
        price_ratio_new = (sqrt_price_x96 / (2**96)) ** 2
        eth_price_new = price_ratio_new / (10**12)
        
        print(f"\n💰 Price Calculations:")
        print(f"OLD (wrong): ${eth_price_old:.2f}")
        print(f"NEW (fixed): ${eth_price_new:.2f}")
        print(f"Etherscan:   $1912.96")
        
        print(f"\n📈 Error Analysis:")
        old_error = ((eth_price_old / 1912.96) - 1) * 100
        new_error = ((eth_price_new / 1912.96) - 1) * 100
        
        print(f"OLD error: {old_error:+.1f}%")
        print(f"NEW error: {new_error:+.1f}%")
        
        # Check if new calculation is reasonable
        if abs(new_error) < 5:
            print(f"\n✅ NEW calculation is within 5% of Etherscan!")
        elif abs(new_error) < 10:
            print(f"\n⚠️  NEW calculation is within 10% of Etherscan")
        else:
            print(f"\n❌ NEW calculation is still off by more than 10%")
            
        # Additional debugging
        print(f"\n🔍 Debug Info:")
        print(f"price_ratio: {price_ratio_new}")
        print(f"2^96: {2**96}")
        print(f"sqrt_price_x96 / 2^96: {sqrt_price_x96 / (2**96)}")
        
    except Exception as e:
        print(f"❌ Error getting price: {e}")

if __name__ == "__main__":
    test_eth_price()
