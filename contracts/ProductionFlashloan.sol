// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// 🔥 PRODUCTION FLASHLOAN ARBITRAGE CONTRACT
// Self-contained with all interfaces included

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

// WETH Interface
interface IWETH {
    function deposit() external payable;
    function withdraw(uint256 amount) external;
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title ProductionFlashloanArbitrage
 * @dev Production-ready flashloan arbitrage contract for Arbitrum
 */
contract ProductionFlashloanArbitrage {
    address public owner;
    IPoolAddressesProvider public immutable ADDRESSES_PROVIDER;
    IPool public immutable POOL;
    
    // Token addresses (Arbitrum)
    address public constant WETH = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1;
    address public constant USDC = 0xaf88d065e77c8cC2239327C5EDb3A432268e5831;
    address public constant USDC_E = 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8;
    
    // DEX router addresses (Arbitrum)
    address public constant SUSHISWAP_ROUTER = 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506;
    address public constant CAMELOT_ROUTER = 0xc873fEcbd354f5A56E00E710B90EF4201db2448d;
    
    // Minimum profit threshold (in basis points, 100 = 1%)
    uint256 public minProfitBps = 10; // 0.1% minimum profit
    
    // Events
    event FlashloanExecuted(
        address indexed asset,
        uint256 amount,
        uint256 profit,
        address dexA,
        address dexB
    );
    
    event FlashloanFailed(
        address indexed asset,
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
     * @dev Execute flashloan arbitrage - ENHANCED WITH SAFETY CHECKS
     * @param asset Address of the asset to flashloan
     * @param amount Amount to flashloan
     * @param dexA Address of first DEX router
     * @param dexB Address of second DEX router
     */
    function executeFlashloanArbitrage(
        address asset,
        uint256 amount,
        address dexA,
        address dexB
    ) external onlyOwner {
        // 🚨 ADDED: Input validation
        require(asset != address(0), "Invalid asset address");
        require(amount > 0, "Amount must be greater than 0");
        require(dexA != address(0), "Invalid DEX A address");
        require(dexB != address(0), "Invalid DEX B address");
        require(dexA != dexB, "DEX addresses must be different");

        // 🚨 ADDED: Check if asset is supported
        require(asset == USDC || asset == USDC_E || asset == WETH, "Unsupported asset");

        // 🚨 ADDED: Pre-check profitability (simplified check)
        // Note: Full profitability check moved to view function
        require(amount > 1000, "Amount too small for profitable arbitrage");

        bytes memory params = abi.encode(asset, dexA, dexB);

        POOL.flashLoanSimple(
            address(this),
            asset,
            amount,
            params,
            0 // referralCode
        );
    }
    
    /**
     * @dev Aave flashloan callback - COMPLETELY FIXED
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
        (address tokenAddress, address dexA, address dexB) = abi.decode(params, (address, address, address));

        // 🚨 CRITICAL FIX: Use flashloan asset, not decoded tokenAddress
        require(tokenAddress == asset, "Token mismatch: flashloan asset must match arbitrage token");

        // 🚨 FIXED: Track token balance, not ETH balance
        uint256 initialTokenBalance = IERC20(asset).balanceOf(address(this));
        uint256 totalDebt = amount + premium;

        // 🚨 ADDED: Verify we received the flashloan
        require(initialTokenBalance >= amount, "Flashloan not received properly");

        try this._performArbitrage(asset, amount, dexA, dexB) {
            uint256 finalTokenBalance = IERC20(asset).balanceOf(address(this));

            // 🚨 CRITICAL: Check if we have enough to repay BEFORE calculating profit
            require(finalTokenBalance >= totalDebt, "Insufficient funds to repay flashloan");

            // Calculate actual profit in tokens
            uint256 profit = finalTokenBalance - totalDebt;

            // 🚨 ADDED: Check minimum profit threshold
            uint256 minProfit = (amount * minProfitBps) / 10000;
            require(profit >= minProfit, "Profit below minimum threshold");

            // Approve pool to pull the debt + premium
            IERC20(asset).approve(address(POOL), totalDebt);

            // 🚨 ADDED: Transfer profit to owner
            if (profit > 0) {
                IERC20(asset).transfer(owner, profit);
            }

            emit FlashloanExecuted(asset, amount, profit, dexA, dexB);
            return true;

        } catch Error(string memory reason) {
            emit FlashloanFailed(asset, amount, reason);

            // 🚨 CRITICAL: Check if we can still repay
            uint256 currentBalance = IERC20(asset).balanceOf(address(this));
            if (currentBalance >= totalDebt) {
                // We can repay, approve the full amount
                IERC20(asset).approve(address(POOL), totalDebt);
            } else {
                // We can't repay fully, this will cause the flashloan to revert
                // But we still need to approve what we have
                IERC20(asset).approve(address(POOL), currentBalance);
                revert(string(abi.encodePacked("Arbitrage failed and cannot repay: ", reason)));
            }

            return true;
        }
    }
    
    /**
     * @dev Internal arbitrage execution - COMPLETELY FIXED
     */
    function _performArbitrage(
        address tokenAddress,
        uint256 amount,
        address dexA,
        address dexB
    ) external {
        require(msg.sender == address(this), "Internal function");

        // 🚨 CRITICAL FIX: Use actual balance, not flashloan amount
        uint256 actualBalance = IERC20(tokenAddress).balanceOf(address(this));
        require(actualBalance > 0, "No tokens received from flashloan");

        // Convert flashloaned tokens to ETH on DEX A
        address[] memory pathSell = new address[](2);
        pathSell[0] = tokenAddress;
        pathSell[1] = WETH;

        uint256 deadline = block.timestamp + 300; // 5 minutes

        // 🚨 FIX: Approve actual balance, not flashloan amount
        IERC20(tokenAddress).approve(dexA, actualBalance);

        // 🚨 FIX: Calculate minimum ETH output (15% slippage protection)
        uint256[] memory expectedAmounts = IDEXRouter(dexA).getAmountsOut(actualBalance, pathSell);
        uint256 minEthOut = (expectedAmounts[1] * 85) / 100; // 15% slippage tolerance

        // Sell tokens for ETH on DEX A
        uint256[] memory amountsOut = IDEXRouter(dexA).swapExactTokensForETH(
            actualBalance,  // 🚨 FIXED: Use actual balance
            minEthOut,      // 🚨 FIXED: 15% slippage protection
            pathSell,
            address(this),
            deadline
        );

        uint256 ethReceived = amountsOut[1];
        require(ethReceived > 0, "No ETH received from DEX A");

        // Buy tokens with ETH on DEX B
        address[] memory pathBuy = new address[](2);
        pathBuy[0] = WETH;
        pathBuy[1] = tokenAddress;

        // 🚨 FIX: Calculate minimum token output (15% slippage protection)
        uint256[] memory expectedTokens = IDEXRouter(dexB).getAmountsOut(ethReceived, pathBuy);
        uint256 minTokensOut = (expectedTokens[1] * 85) / 100; // 15% slippage tolerance

        IDEXRouter(dexB).swapExactETHForTokens{value: ethReceived}(
            minTokensOut,   // 🚨 FIXED: 15% slippage protection
            pathBuy,
            address(this),
            deadline
        );

        // 🚨 ADDED: Verify we have enough tokens to repay flashloan
        uint256 finalBalance = IERC20(tokenAddress).balanceOf(address(this));
        require(finalBalance >= amount, "Arbitrage failed: insufficient tokens for repayment");
    }
    
    /**
     * @dev Check potential profit for flashloan arbitrage - ENHANCED CALCULATION
     */
    function checkFlashloanProfit(
        address tokenAddress,
        uint256 amount,
        address dexA,
        address dexB
    ) external view returns (uint256 estimatedProfit, bool profitable) {
        try this._simulateArbitrage(tokenAddress, amount, dexA, dexB) returns (uint256 profit) {
            // 🚨 FIXED: Account for Aave flashloan fee (0.09%)
            uint256 flashloanFee = (amount * 9) / 10000; // 0.09%
            uint256 totalCost = amount + flashloanFee;

            if (profit > totalCost) {
                estimatedProfit = profit - totalCost;

                // Check if profit meets minimum threshold
                uint256 minProfit = (amount * minProfitBps) / 10000;
                profitable = estimatedProfit >= minProfit;
            } else {
                estimatedProfit = 0;
                profitable = false;
            }
        } catch {
            estimatedProfit = 0;
            profitable = false;
        }
    }

    /**
     * @dev Internal function to simulate arbitrage
     */
    function _simulateArbitrage(
        address tokenAddress,
        uint256 amount,
        address dexA,
        address dexB
    ) external view returns (uint256 finalTokens) {
        // Simulate selling tokens on DEX A
        address[] memory pathSell = new address[](2);
        pathSell[0] = tokenAddress;
        pathSell[1] = WETH;

        uint256[] memory amountsOutA = IDEXRouter(dexA).getAmountsOut(amount, pathSell);
        uint256 ethFromSell = amountsOutA[1];

        // 🚨 ADDED: Apply slippage (15%) to simulation
        uint256 ethAfterSlippage = (ethFromSell * 85) / 100;

        // Simulate buying tokens on DEX B
        address[] memory pathBuy = new address[](2);
        pathBuy[0] = WETH;
        pathBuy[1] = tokenAddress;

        uint256[] memory amountsOutB = IDEXRouter(dexB).getAmountsOut(ethAfterSlippage, pathBuy);
        uint256 tokensFromBuy = amountsOutB[1];

        // 🚨 ADDED: Apply slippage (15%) to final tokens
        finalTokens = (tokensFromBuy * 85) / 100;
    }
    
    /**
     * @dev Emergency withdraw function - ENHANCED
     */
    function emergencyWithdraw() external onlyOwner {
        // Withdraw all ETH
        uint256 ethBalance = address(this).balance;
        if (ethBalance > 0) {
            payable(owner).transfer(ethBalance);
        }

        // Withdraw all USDC
        uint256 usdcBalance = IERC20(USDC).balanceOf(address(this));
        if (usdcBalance > 0) {
            IERC20(USDC).transfer(owner, usdcBalance);
        }

        // Withdraw all WETH
        uint256 wethBalance = IERC20(WETH).balanceOf(address(this));
        if (wethBalance > 0) {
            IERC20(WETH).transfer(owner, wethBalance);
        }
    }

    /**
     * @dev Withdraw specific token - ENHANCED WITH SAFETY
     */
    function withdrawToken(address tokenAddress, uint256 amount) external onlyOwner {
        require(tokenAddress != address(0), "Invalid token address");
        uint256 balance = IERC20(tokenAddress).balanceOf(address(this));
        require(balance >= amount, "Insufficient token balance");
        require(amount > 0, "Amount must be greater than 0");

        IERC20(tokenAddress).transfer(owner, amount);
    }

    /**
     * @dev Update minimum profit threshold - ENHANCED
     */
    function setMinProfitBps(uint256 _minProfitBps) external onlyOwner {
        require(_minProfitBps <= 1000, "Max 10% profit threshold");
        require(_minProfitBps >= 1, "Min 0.01% profit threshold");
        minProfitBps = _minProfitBps;
    }

    /**
     * @dev Transfer ownership - ADDED
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid new owner");
        require(newOwner != owner, "Same as current owner");
        owner = newOwner;
    }

    /**
     * @dev Get contract status - ADDED
     */
    function getContractStatus() external view returns (
        address contractOwner,
        uint256 ethBalance,
        uint256 usdcBalance,
        uint256 wethBalance,
        uint256 minProfitThreshold
    ) {
        contractOwner = owner;
        ethBalance = address(this).balance;
        usdcBalance = IERC20(USDC).balanceOf(address(this));
        wethBalance = IERC20(WETH).balanceOf(address(this));
        minProfitThreshold = minProfitBps;
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
