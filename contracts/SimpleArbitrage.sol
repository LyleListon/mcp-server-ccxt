// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// 🔥 SIMPLE ARBITRAGE CONTRACT
// Self-contained for fast deployment and testing

// Minimal IERC20 interface
interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
}

// WETH interface
interface IWETH {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
    function balanceOf(address account) external view returns (uint256);
}

// Minimal DEX Router interface
interface IDEXRouter {
    function swapExactETHForTokens(
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external payable returns (uint[] memory amounts);
    
    function swapExactTokensForETH(
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
 * @title SimpleArbitrage
 * @dev Simple arbitrage contract for cross-DEX trading
 */
contract SimpleArbitrage {
    address public owner;
    
    // Token addresses (Arbitrum)
    address public constant WETH = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1;
    address public constant USDC = 0xaf88d065e77c8cC2239327C5EDb3A432268e5831;
    
    // DEX router addresses (Arbitrum)
    address public constant SUSHISWAP_ROUTER = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;
    address public constant CAMELOT_ROUTER = 0xc873fEcbd354f5A56E00E710B90EF4201db2448d;
    
    // Events
    event ArbitrageExecuted(
        address indexed token,
        uint256 amountIn,
        uint256 profit,
        address dexA,
        address dexB
    );
    
    event ArbitrageFailed(
        address indexed token,
        uint256 amountIn,
        string reason
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev Execute simple arbitrage between two DEXes
     * @param tokenAddress Address of the token to arbitrage
     * @param amountIn Amount of ETH to use for arbitrage
     * @param dexA Address of first DEX router
     * @param dexB Address of second DEX router
     * @param minProfit Minimum profit required (in wei)
     */
    function executeArbitrage(
        address tokenAddress,
        uint256 amountIn,
        address dexA,
        address dexB,
        uint256 minProfit
    ) external onlyOwner {
        require(amountIn > 0, "Amount must be greater than 0");
        require(address(this).balance >= amountIn, "Insufficient ETH balance");
        
        uint256 initialBalance = address(this).balance;
        
        try this._performArbitrage(tokenAddress, amountIn, dexA, dexB) {
            uint256 finalBalance = address(this).balance;
            
            if (finalBalance > initialBalance) {
                uint256 profit = finalBalance - initialBalance;
                require(profit >= minProfit, "Profit below minimum threshold");
                
                emit ArbitrageExecuted(tokenAddress, amountIn, profit, dexA, dexB);
            } else {
                emit ArbitrageFailed(tokenAddress, amountIn, "No profit generated");
                revert("Arbitrage not profitable");
            }
        } catch Error(string memory reason) {
            emit ArbitrageFailed(tokenAddress, amountIn, reason);
            revert(reason);
        }
    }
    
    /**
     * @dev Internal function to perform the actual arbitrage
     */
    function _performArbitrage(
        address tokenAddress,
        uint256 amountIn,
        address dexA,
        address dexB
    ) external {
        require(msg.sender == address(this), "Internal function");
        
        // Step 1: Buy token on DEX A
        address[] memory pathBuy = new address[](2);
        pathBuy[0] = WETH;
        pathBuy[1] = tokenAddress;
        
        uint256 deadline = block.timestamp + 300; // 5 minutes
        
        uint256[] memory amountsOut = IDEXRouter(dexA).swapExactETHForTokens{value: amountIn}(
            0, // Accept any amount of tokens out
            pathBuy,
            address(this),
            deadline
        );
        
        uint256 tokenAmount = amountsOut[1];
        
        // Step 2: Approve DEX B to spend tokens
        IERC20(tokenAddress).approve(dexB, tokenAmount);
        
        // Step 3: Sell token on DEX B
        address[] memory pathSell = new address[](2);
        pathSell[0] = tokenAddress;
        pathSell[1] = WETH;
        
        IDEXRouter(dexB).swapExactTokensForETH(
            tokenAmount,
            0, // Accept any amount of ETH out
            pathSell,
            address(this),
            deadline
        );
    }
    
    /**
     * @dev Check potential profit for arbitrage
     */
    function checkArbitrageProfit(
        address tokenAddress,
        uint256 amountIn,
        address dexA,
        address dexB
    ) external view returns (uint256 estimatedProfit) {
        // Get amount out from DEX A (ETH -> Token)
        address[] memory pathBuy = new address[](2);
        pathBuy[0] = WETH;
        pathBuy[1] = tokenAddress;
        
        uint256[] memory amountsOutA = IDEXRouter(dexA).getAmountsOut(amountIn, pathBuy);
        uint256 tokenAmount = amountsOutA[1];
        
        // Get amount out from DEX B (Token -> ETH)
        address[] memory pathSell = new address[](2);
        pathSell[0] = tokenAddress;
        pathSell[1] = WETH;
        
        uint256[] memory amountsOutB = IDEXRouter(dexB).getAmountsOut(tokenAmount, pathSell);
        uint256 ethOut = amountsOutB[1];
        
        if (ethOut > amountIn) {
            estimatedProfit = ethOut - amountIn;
        } else {
            estimatedProfit = 0;
        }
    }
    
    /**
     * @dev Emergency withdraw function
     */
    function emergencyWithdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }
    
    /**
     * @dev Withdraw specific token
     */
    function withdrawToken(address tokenAddress, uint256 amount) external onlyOwner {
        IERC20(tokenAddress).transfer(owner, amount);
    }
    
    /**
     * @dev Receive ETH
     */
    receive() external payable {}
    
    /**
     * @dev Fallback function
     */
    fallback() external payable {}
}
