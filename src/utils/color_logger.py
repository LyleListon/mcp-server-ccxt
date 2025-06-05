"""
Color Logger Utility
===================

Provides colored logging for trade results to make success/failure easier to spot.
"""

class Colors:
    """ANSI color codes for terminal output."""
    
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Reset
    RESET = '\033[0m'
    
    @classmethod
    def red(cls, text: str) -> str:
        """Make text red (for failures)."""
        return f"{cls.RED}{text}{cls.RESET}"
    
    @classmethod
    def yellow(cls, text: str) -> str:
        """Make text yellow (for success)."""
        return f"{cls.YELLOW}{text}{cls.RESET}"
    
    @classmethod
    def green(cls, text: str) -> str:
        """Make text green."""
        return f"{cls.GREEN}{text}{cls.RESET}"
    
    @classmethod
    def blue(cls, text: str) -> str:
        """Make text blue."""
        return f"{cls.BLUE}{text}{cls.RESET}"
    
    @classmethod
    def bold(cls, text: str) -> str:
        """Make text bold."""
        return f"{cls.BOLD}{text}{cls.RESET}"
    
    @classmethod
    def success(cls, text: str) -> str:
        """Format success message in yellow."""
        return cls.yellow(text)
    
    @classmethod
    def failure(cls, text: str) -> str:
        """Format failure message in red."""
        return cls.red(text)


def log_trade_result(logger, success: bool, profit_usd: float, execution_time: float = None,
                    failure_count: int = None, error_message: str = None):
    """
    Log trade result with FULL COLOR formatting - entire message colored.

    Args:
        logger: Logger instance
        success: Whether trade was successful
        profit_usd: Profit/loss amount in USD
        execution_time: Execution time in seconds (optional)
        failure_count: Current failure count (optional)
        error_message: Error message for failures (optional)
    """
    if success:
        # FULL YELLOW for entire success message
        base_msg = f"✅ Successful trade: ${profit_usd:.2f} profit"
        if execution_time:
            base_msg += f" in {execution_time:.1f}s"
        if failure_count is not None:
            base_msg += f" (failures: {failure_count})"

        # Color the ENTIRE message yellow
        colored_msg = Colors.yellow(base_msg)
        logger.info(colored_msg)
    else:
        # FULL RED for entire failure message
        base_msg = f"❌ Failed trade: ${profit_usd:.2f} loss"
        if execution_time:
            base_msg += f" in {execution_time:.1f}s"
        if error_message:
            base_msg += f" - {error_message}"

        # Color the ENTIRE message red
        colored_msg = Colors.red(base_msg)
        logger.error(colored_msg)


def log_performance_summary(logger, successful_trades: int, total_trades: int,
                          net_profit: float, success_rate: float = None):
    """
    Log performance summary with FULL COLOR formatting - entire message colored.

    Args:
        logger: Logger instance
        successful_trades: Number of successful trades
        total_trades: Total number of trades
        net_profit: Net profit in USD
        success_rate: Success rate percentage (optional)
    """
    if success_rate is None:
        success_rate = (successful_trades / max(total_trades, 1)) * 100

    # Build the complete summary message
    summary = f"   📊 Performance: {successful_trades}/{total_trades} success ({success_rate:.1f}%), ${net_profit:.2f} net profit"

    # Color the ENTIRE message based on overall performance
    if net_profit > 0 and success_rate >= 50:
        # FULL YELLOW for good performance
        colored_msg = Colors.yellow(summary)
        logger.info(colored_msg)
    elif net_profit < 0 or success_rate < 30:
        # FULL RED for poor performance
        colored_msg = Colors.red(summary)
        logger.warning(colored_msg)
    else:
        # Normal color for neutral performance
        logger.info(summary)


def log_execution_result(logger, success: bool, profit_usd: float, execution_time: float,
                        error_message: str = None):
    """
    Log execution result with FULL COLOR formatting - entire message colored.

    Args:
        logger: Logger instance
        success: Whether execution was successful
        profit_usd: Profit/loss amount in USD
        execution_time: Execution time in seconds
        error_message: Error message for failures (optional)
    """
    if success:
        # FULL YELLOW for entire success message
        msg = f"      ✅ Success: ${profit_usd:.2f} profit in {execution_time:.1f}s"
        colored_msg = Colors.yellow(msg)
        logger.info(colored_msg)
    else:
        # FULL RED for entire failure message
        msg = f"      ❌ Failed: {error_message or 'Unknown error'}"
        colored_msg = Colors.red(msg)
        logger.error(colored_msg)


def log_ultimate_result(logger, success: bool, profit_usd: float, execution_time: float,
                       error_message: str = None):
    """
    Log ultimate system result with FULL COLOR formatting - entire message colored.

    Args:
        logger: Logger instance
        success: Whether execution was successful
        profit_usd: Profit/loss amount in USD
        execution_time: Execution time in seconds
        error_message: Error message for failures (optional)
    """
    if success:
        # FULL YELLOW for entire ultimate success message
        msg = f"✅ ULTIMATE SUCCESS: ${profit_usd:.2f} profit in {execution_time:.2f}s"
        colored_msg = Colors.yellow(msg)
        logger.info(colored_msg)
    else:
        # FULL RED for entire ultimate failure message
        msg = f"❌ ULTIMATE FAILURE: {error_message or 'Unknown error'}"
        colored_msg = Colors.red(msg)
        logger.error(colored_msg)
