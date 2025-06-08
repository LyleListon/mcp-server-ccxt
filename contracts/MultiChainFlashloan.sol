// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// 🌐 MULTI-CHAIN FLASHLOAN ARBITRAGE CONTRACT
// Deployable on Arbitrum, Optimism, and Base with chain-specific configurations

// IERC20 Interface
interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

// Aave V3 Pool Interface
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

/**
 * @title MultiChainFlashloanArbitrage
 * @dev Multi-chain flashloan arbitrage contract with chain-specific configurations
 */
contract MultiChainFlashloanArbitrage {
    address public owner;
    IPoolAddressesProvider public immutable ADDRESSES_PROVIDER;
    IPool public immutable POOL;
    
    // Chain-specific token addresses (set in constructor)
    address public WETH;
    address public USDC;
    address public USDT;
    address public DAI;
    
    // Chain-specific DEX router addresses (set in constructor)
    address public DEX_ROUTER_A;
    address public DEX_ROUTER_B;
    address public DEX_ROUTER_C;
    
    // Chain identification
    uint256 public immutable CHAIN_ID;
    string public CHAIN_NAME;
    
    // Minimum profit threshold (in basis points, 100 = 1%)
    uint256 public minProfitBps = 10; // 0.1% minimum profit
    
    // Events
    event FlashloanExecuted(
        address indexed asset,
        uint256 amount,
        uint256 profit,
        address dexA,
        address dexB,
        uint256 chainId
    );
    
    event FlashloanFailed(
        address indexed asset,
        uint256 amount,
        string reason,
        uint256 chainId
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(
        address _addressProvider,
        address _weth,
        address _usdc,
        address _usdt,
        address _dai,
        address _dexRouterA,
        address _dexRouterB,
        address _dexRouterC,
        string memory _chainName
    ) {
        ADDRESSES_PROVIDER = IPoolAddressesProvider(_addressProvider);
        POOL = IPool(ADDRESSES_PROVIDER.getPool());
        owner = msg.sender;
        
        // Set chain-specific token addresses
        WETH = _weth;
        USDC = _usdc;
        USDT = _usdt;
        DAI = _dai;
        
        // Set chain-specific DEX router addresses
        DEX_ROUTER_A = _dexRouterA;
        DEX_ROUTER_B = _dexRouterB;
        DEX_ROUTER_C = _dexRouterC;
        
        // Set chain identification
        CHAIN_ID = block.chainid;
        CHAIN_NAME = _chainName;
    }
    
    /**
     * @dev Execute flashloan arbitrage with enhanced validation
     */
    function executeFlashloanArbitrage(
        address asset,
        uint256 amount,
        address dexA,
        address dexB
    ) external onlyOwner {
        // 🚨 ENHANCED: Input validation
        require(asset != address(0), "Invalid asset address");
        require(amount > 1000, "Amount too small for profitable arbitrage");
        require(dexA != address(0), "Invalid DEX A address");
        require(dexB != address(0), "Invalid DEX B address");
        require(dexA != dexB, "DEX addresses must be different");
        
        // 🚨 ENHANCED: Check if asset is supported
        require(
            asset == USDC || asset == WETH || asset == USDT || asset == DAI, 
            "Unsupported asset"
        );
        
        // 🚨 ENHANCED: Validate DEX routers
        require(
            dexA == DEX_ROUTER_A || dexA == DEX_ROUTER_B || dexA == DEX_ROUTER_C,
            "Invalid DEX A router"
        );
        require(
            dexB == DEX_ROUTER_A || dexB == DEX_ROUTER_B || dexB == DEX_ROUTER_C,
            "Invalid DEX B router"
        );
        
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
        
        // 🚨 FIXED: Track token balance, not ETH balance
        uint256 initialTokenBalance = IERC20(asset).balanceOf(address(this));
        uint256 totalDebt = amount + premium;
        
        // 🚨 ADDED: Verify we received the flashloan
        require(initialTokenBalance >= amount, "Flashloan not received properly");
        
        try this._performArbitrage(tokenAddress, amount, dexA, dexB) {
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
            
            emit FlashloanExecuted(asset, amount, profit, dexA, dexB, CHAIN_ID);
            return true;
            
        } catch Error(string memory reason) {
            emit FlashloanFailed(asset, amount, reason, CHAIN_ID);
            
            // 🚨 CRITICAL: Check if we can still repay
            uint256 currentBalance = IERC20(asset).balanceOf(address(this));
            if (currentBalance >= totalDebt) {
                IERC20(asset).approve(address(POOL), totalDebt);
            } else {
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
        
        // 🚨 FIX: Calculate minimum ETH output (5% slippage protection)
        uint256[] memory expectedAmounts = IDEXRouter(dexA).getAmountsOut(actualBalance, pathSell);
        uint256 minEthOut = (expectedAmounts[1] * 95) / 100; // 5% slippage tolerance
        
        // Sell tokens for ETH on DEX A
        uint256[] memory amountsOut = IDEXRouter(dexA).swapExactTokensForETH(
            actualBalance,  // 🚨 FIXED: Use actual balance
            minEthOut,      // 🚨 FIXED: Slippage protection
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
        
        // 🚨 FIX: Calculate minimum token output (5% slippage protection)
        uint256[] memory expectedTokens = IDEXRouter(dexB).getAmountsOut(ethReceived, pathBuy);
        uint256 minTokensOut = (expectedTokens[1] * 95) / 100; // 5% slippage tolerance
        
        IDEXRouter(dexB).swapExactETHForTokens{value: ethReceived}(
            minTokensOut,   // 🚨 FIXED: Slippage protection
            pathBuy,
            address(this),
            deadline
        );
        
        // 🚨 ADDED: Verify we have enough tokens to repay flashloan
        uint256 finalBalance = IERC20(tokenAddress).balanceOf(address(this));
        require(finalBalance >= amount, "Arbitrage failed: insufficient tokens for repayment");
    }
    
    /**
     * @dev Get contract information
     */
    function getContractInfo() external view returns (
        string memory chainName,
        uint256 chainId,
        address weth,
        address usdc,
        address dexA,
        address dexB,
        address dexC,
        uint256 minProfitThreshold
    ) {
        chainName = CHAIN_NAME;
        chainId = CHAIN_ID;
        weth = WETH;
        usdc = USDC;
        dexA = DEX_ROUTER_A;
        dexB = DEX_ROUTER_B;
        dexC = DEX_ROUTER_C;
        minProfitThreshold = minProfitBps;
    }
    
    /**
     * @dev Emergency withdraw function
     */
    function emergencyWithdraw() external onlyOwner {
        // Withdraw all ETH
        uint256 ethBalance = address(this).balance;
        if (ethBalance > 0) {
            payable(owner).transfer(ethBalance);
        }
        
        // Withdraw all supported tokens
        address[] memory tokens = new address[](4);
        tokens[0] = USDC;
        tokens[1] = WETH;
        tokens[2] = USDT;
        tokens[3] = DAI;
        
        for (uint i = 0; i < tokens.length; i++) {
            if (tokens[i] != address(0)) {
                uint256 balance = IERC20(tokens[i]).balanceOf(address(this));
                if (balance > 0) {
                    IERC20(tokens[i]).transfer(owner, balance);
                }
            }
        }
    }
    
    /**
     * @dev Update minimum profit threshold
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
    
    /**
     * @dev Receive ETH
     */
    receive() external payable {}
    
    /**
     * @dev Fallback function
     */
    fallback() external payable {}
}
