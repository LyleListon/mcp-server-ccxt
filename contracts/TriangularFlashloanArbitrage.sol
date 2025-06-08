// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// 🔺 TRIANGULAR FLASHLOAN ARBITRAGE CONTRACT
// Self-contained with all interfaces included - FIXES IDENTICAL_ADDRESSES ERROR

// IERC20 Interface
interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

// Aave V3 Pool Interface (minimal)
interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

// Aave V3 Pool Address Provider Interface
interface IPoolAddressesProvider {
    function getPool() external view returns (address);
}

// DEX Router Interface (Uniswap V2 compatible)
interface IDEXRouter {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);

    function getAmountsOut(uint amountIn, address[] calldata path)
        external view returns (uint[] memory amounts);
}

/**
 * @title TriangularFlashloanArbitrage
 * @dev Flashloan arbitrage contract specifically for triangular arbitrage (A→B→C→A)
 * FIXES IDENTICAL_ADDRESSES ERROR by properly handling triangular paths
 */
contract TriangularFlashloanArbitrage {

    address public owner;
    IPoolAddressesProvider public immutable ADDRESSES_PROVIDER;
    IPool public immutable POOL;
    uint256 public minProfitBps = 10; // 0.1% minimum profit
    
    // Token addresses (Arbitrum)
    address public constant WETH = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1;
    address public constant USDC = 0xaf88d065e77c8cC2239327C5EDb3A432268e5831;
    address public constant USDT = 0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9;
    address public constant USDC_E = 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8;
    
    // Events
    event TriangularArbitrageExecuted(
        address indexed startToken,
        address indexed middleToken,
        address indexed endToken,
        uint256 amount,
        uint256 profit,
        address dexA,
        address dexB,
        address dexC
    );
    
    event TriangularArbitrageFailed(
        address indexed startToken,
        uint256 amount,
        string reason
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(address _addressProvider) {
        ADDRESSES_PROVIDER = IPoolAddressesProvider(_addressProvider);
        POOL = IPool(ADDRESSES_PROVIDER.getPool());
        owner = msg.sender;
    }
    
    /**
     * @dev Execute triangular flashloan arbitrage (A→B→C→A)
     * @param startToken The token to start with (and flashloan)
     * @param amount The amount to flashloan
     * @param arbitrageData Encoded data: (middleToken, endToken, dexA, dexB, dexC)
     */
    function executeTriangularArbitrage(
        address startToken,
        uint256 amount,
        bytes calldata arbitrageData
    ) external onlyOwner {

        // Decode arbitrage data
        (address middleToken, address endToken, address dexA, address dexB, address dexC) =
            abi.decode(arbitrageData, (address, address, address, address, address));

        // Validate triangular path
        require(startToken != middleToken, "Start and middle tokens must be different");
        require(middleToken != endToken, "Middle and end tokens must be different");
        require(endToken != startToken, "End and start tokens must be different");

        // Validate supported tokens
        require(
            startToken == WETH || startToken == USDC || startToken == USDT || startToken == USDC_E,
            "Unsupported start token"
        );

        // Encode parameters for flashloan callback
        bytes memory params = arbitrageData;
        
        // Request flashloan from Aave
        POOL.flashLoanSimple(
            address(this),
            startToken,
            amount,
            params,
            0 // referralCode
        );
    }
    
    /**
     * @dev Aave flashloan callback for triangular arbitrage
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        require(msg.sender == address(POOL), "Caller must be Pool");
        require(initiator == address(this), "Initiator must be this contract");
        
        // Decode parameters
        (address middleToken, address endToken, address dexA, address dexB, address dexC) =
            abi.decode(params, (address, address, address, address, address));
        
        // Asset is the start token for triangular arbitrage
        
        uint256 totalDebt = amount + premium;
        
        try this._performTriangularArbitrage(
            asset, middleToken, endToken, amount, dexA, dexB, dexC
        ) {
            uint256 finalBalance = IERC20(asset).balanceOf(address(this));
            
            // Check if we have enough to repay
            require(finalBalance >= totalDebt, "Insufficient funds to repay flashloan");
            
            // Calculate profit
            uint256 profit = finalBalance - totalDebt;
            
            // Check minimum profit threshold
            uint256 minProfit = (amount * minProfitBps) / 10000;
            require(profit >= minProfit, "Profit below minimum threshold");
            
            // Approve pool to pull the debt + premium
            IERC20(asset).approve(address(POOL), totalDebt);

            // Transfer profit to owner
            if (profit > 0) {
                IERC20(asset).transfer(owner, profit);
            }

            emit TriangularArbitrageExecuted(
                asset, middleToken, endToken, amount, profit, dexA, dexB, dexC
            );
            
            return true;
            
        } catch Error(string memory reason) {
            emit TriangularArbitrageFailed(asset, amount, reason);

            // Try to repay what we can
            uint256 currentBalance = IERC20(asset).balanceOf(address(this));
            if (currentBalance >= totalDebt) {
                IERC20(asset).approve(address(POOL), totalDebt);
            } else {
                IERC20(asset).approve(address(POOL), currentBalance);
                revert(string(abi.encodePacked("Triangular arbitrage failed and cannot repay: ", reason)));
            }
            
            return true;
        }
    }
    
    /**
     * @dev Internal triangular arbitrage execution (external for try/catch)
     */
    function _performTriangularArbitrage(
        address startToken,
        address middleToken,
        address endToken,
        uint256 amount,
        address dexA,
        address dexB,
        address dexC
    ) external {
        require(msg.sender == address(this), "Internal function");
        
        uint256 currentAmount = amount;
        
        // Step 1: startToken → middleToken on DEX A
        currentAmount = _executeSwap(startToken, middleToken, currentAmount, dexA);
        require(currentAmount > 0, "Step 1 failed: no tokens received");
        
        // Step 2: middleToken → endToken on DEX B  
        currentAmount = _executeSwap(middleToken, endToken, currentAmount, dexB);
        require(currentAmount > 0, "Step 2 failed: no tokens received");
        
        // Step 3: endToken → startToken on DEX C
        currentAmount = _executeSwap(endToken, startToken, currentAmount, dexC);
        require(currentAmount > 0, "Step 3 failed: no tokens received");
        
        // Verify we have more than we started with
        uint256 finalBalance = IERC20(startToken).balanceOf(address(this));
        require(finalBalance > amount, "Triangular arbitrage not profitable");
    }
    
    /**
     * @dev Execute a single token swap
     */
    function _executeSwap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        address dexRouter
    ) internal returns (uint256 amountOut) {
        
        // Create swap path
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
        
        // Approve router
        IERC20(tokenIn).approve(dexRouter, amountIn);
        
        // Get expected output with slippage protection
        uint256[] memory expectedAmounts = IDEXRouter(dexRouter).getAmountsOut(amountIn, path);
        uint256 minAmountOut = (expectedAmounts[1] * 90) / 100; // 10% slippage tolerance
        
        // Execute swap
        uint256[] memory amounts = IDEXRouter(dexRouter).swapExactTokensForTokens(
            amountIn,
            minAmountOut,
            path,
            address(this),
            block.timestamp + 300 // 5 minutes deadline
        );
        
        return amounts[1];
    }
    
    /**
     * @dev Emergency withdraw function
     */
    function emergencyWithdraw() external onlyOwner {
        // Withdraw all supported tokens
        _withdrawToken(WETH);
        _withdrawToken(USDC);
        _withdrawToken(USDT);
        _withdrawToken(USDC_E);
        
        // Withdraw ETH
        uint256 ethBalance = address(this).balance;
        if (ethBalance > 0) {
            payable(owner).transfer(ethBalance);
        }
    }
    
    function _withdrawToken(address token) internal {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).transfer(owner, balance);
        }
    }
    
    /**
     * @dev Set minimum profit threshold
     */
    function setMinProfitBps(uint256 _minProfitBps) external onlyOwner {
        require(_minProfitBps <= 1000, "Max 10% profit threshold");
        require(_minProfitBps >= 1, "Min 0.01% profit threshold");
        minProfitBps = _minProfitBps;
    }
    
    /**
     * @dev Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid new owner");
        require(newOwner != owner, "Same as current owner");
        owner = newOwner;
    }
    
    receive() external payable {}
    fallback() external payable {}
}
