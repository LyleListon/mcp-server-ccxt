// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@aave/core-v3/contracts/flashloan/base/FlashLoanSimpleReceiverBase.sol";
import "@aave/core-v3/contracts/interfaces/IPoolAddressesProvider.sol";
import "@aave/core-v3/contracts/interfaces/IPool.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title BatchFlashloanArbitrage
 * @dev Execute multiple arbitrage opportunities in a single flashloan transaction
 */
contract BatchFlashloanArbitrage is FlashLoanSimpleReceiverBase, Ownable {
    
    struct ArbitrageParams {
        address tokenIn;
        address tokenOut;
        address dexA;
        address dexB;
        uint256 amountIn;
        bytes swapDataA;
        bytes swapDataB;
    }
    
    struct BatchParams {
        ArbitrageParams[] arbitrages;
        uint256 totalFlashloanAmount;
        address flashloanAsset;
    }
    
    event BatchArbitrageExecuted(
        uint256 opportunitiesCount,
        uint256 totalProfit,
        address indexed executor
    );
    
    event ArbitrageExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 profit,
        bool success
    );
    
    mapping(address => bool) public authorizedExecutors;
    uint256 public totalProfitGenerated;
    uint256 public totalArbitragesExecuted;
    
    modifier onlyAuthorized() {
        require(authorizedExecutors[msg.sender] || msg.sender == owner(), "Not authorized");
        _;
    }
    
    constructor(address _addressProvider) 
        FlashLoanSimpleReceiverBase(IPoolAddressesProvider(_addressProvider)) 
    {
        authorizedExecutors[msg.sender] = true;
    }
    
    /**
     * @dev Execute multiple arbitrage opportunities in batch
     */
    function executeBatchArbitrage(BatchParams calldata params) external onlyAuthorized {
        require(params.arbitrages.length > 0, "No arbitrages provided");
        require(params.totalFlashloanAmount > 0, "Invalid flashloan amount");
        
        // Encode batch parameters for flashloan callback
        bytes memory data = abi.encode(params);
        
        // Request flashloan
        POOL.flashLoanSimple(
            address(this),
            params.flashloanAsset,
            params.totalFlashloanAmount,
            data,
            0
        );
    }
    
    /**
     * @dev Flashloan callback - execute all arbitrages
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(POOL), "Invalid caller");
        require(initiator == address(this), "Invalid initiator");
        
        // Decode batch parameters
        BatchParams memory batchParams = abi.decode(params, (BatchParams));
        
        uint256 totalProfit = 0;
        uint256 successCount = 0;
        
        // Execute each arbitrage opportunity
        for (uint256 i = 0; i < batchParams.arbitrages.length; i++) {
            ArbitrageParams memory arb = batchParams.arbitrages[i];
            
            try this.executeSingleArbitrage(arb) returns (uint256 profit) {
                totalProfit += profit;
                successCount++;
                
                emit ArbitrageExecuted(
                    arb.tokenIn,
                    arb.tokenOut,
                    arb.amountIn,
                    profit,
                    true
                );
            } catch {
                emit ArbitrageExecuted(
                    arb.tokenIn,
                    arb.tokenOut,
                    arb.amountIn,
                    0,
                    false
                );
            }
        }
        
        // Update statistics
        totalProfitGenerated += totalProfit;
        totalArbitragesExecuted += successCount;
        
        // Ensure we can repay the flashloan
        uint256 repayAmount = amount + premium;
        require(
            IERC20(asset).balanceOf(address(this)) >= repayAmount,
            "Insufficient balance to repay flashloan"
        );
        
        // Approve repayment
        IERC20(asset).approve(address(POOL), repayAmount);
        
        emit BatchArbitrageExecuted(successCount, totalProfit, tx.origin);
        
        return true;
    }
    
    /**
     * @dev Execute a single arbitrage opportunity
     */
    function executeSingleArbitrage(ArbitrageParams memory params) 
        external 
        returns (uint256 profit) 
    {
        require(msg.sender == address(this), "Internal call only");
        
        uint256 initialBalance = IERC20(params.tokenIn).balanceOf(address(this));
        
        // Step 1: Swap on DEX A
        IERC20(params.tokenIn).approve(params.dexA, params.amountIn);
        (bool successA, ) = params.dexA.call(params.swapDataA);
        require(successA, "DEX A swap failed");
        
        // Step 2: Swap on DEX B
        uint256 intermediateBalance = IERC20(params.tokenOut).balanceOf(address(this));
        IERC20(params.tokenOut).approve(params.dexB, intermediateBalance);
        (bool successB, ) = params.dexB.call(params.swapDataB);
        require(successB, "DEX B swap failed");
        
        // Calculate profit
        uint256 finalBalance = IERC20(params.tokenIn).balanceOf(address(this));
        require(finalBalance > initialBalance, "No profit generated");
        
        profit = finalBalance - initialBalance;
        return profit;
    }
    
    /**
     * @dev Execute parallel arbitrages (different tokens)
     */
    function executeParallelArbitrages(ArbitrageParams[] calldata arbitrages) 
        external 
        onlyAuthorized 
    {
        require(arbitrages.length > 0, "No arbitrages provided");
        
        uint256 totalProfit = 0;
        uint256 successCount = 0;
        
        // Execute all arbitrages in parallel (no flashloan needed)
        for (uint256 i = 0; i < arbitrages.length; i++) {
            try this.executeSingleArbitrage(arbitrages[i]) returns (uint256 profit) {
                totalProfit += profit;
                successCount++;
                
                emit ArbitrageExecuted(
                    arbitrages[i].tokenIn,
                    arbitrages[i].tokenOut,
                    arbitrages[i].amountIn,
                    profit,
                    true
                );
            } catch {
                emit ArbitrageExecuted(
                    arbitrages[i].tokenIn,
                    arbitrages[i].tokenOut,
                    arbitrages[i].amountIn,
                    0,
                    false
                );
            }
        }
        
        totalProfitGenerated += totalProfit;
        totalArbitragesExecuted += successCount;
        
        emit BatchArbitrageExecuted(successCount, totalProfit, msg.sender);
    }
    
    /**
     * @dev Multi-token flashloan for complex arbitrages
     */
    function executeMultiTokenBatch(
        address[] calldata assets,
        uint256[] calldata amounts,
        ArbitrageParams[] calldata arbitrages
    ) external onlyAuthorized {
        require(assets.length == amounts.length, "Arrays length mismatch");
        require(arbitrages.length > 0, "No arbitrages provided");
        
        // Encode parameters for callback
        bytes memory data = abi.encode(arbitrages);
        
        // Request multi-asset flashloan
        uint256[] memory modes = new uint256[](assets.length);
        // All modes = 0 (no debt)
        
        POOL.flashLoan(
            address(this),
            assets,
            amounts,
            modes,
            address(this),
            data,
            0
        );
    }
    
    /**
     * @dev Authorize/deauthorize executors
     */
    function setExecutorAuthorization(address executor, bool authorized) 
        external 
        onlyOwner 
    {
        authorizedExecutors[executor] = authorized;
    }
    
    /**
     * @dev Emergency withdrawal
     */
    function emergencyWithdraw(address token, uint256 amount) 
        external 
        onlyOwner 
    {
        if (token == address(0)) {
            payable(owner()).transfer(amount);
        } else {
            IERC20(token).transfer(owner(), amount);
        }
    }
    
    /**
     * @dev Get contract statistics
     */
    function getStats() external view returns (
        uint256 totalProfit,
        uint256 totalExecutions,
        uint256 averageProfit
    ) {
        totalProfit = totalProfitGenerated;
        totalExecutions = totalArbitragesExecuted;
        averageProfit = totalExecutions > 0 ? totalProfit / totalExecutions : 0;
    }
    
    receive() external payable {}
}
