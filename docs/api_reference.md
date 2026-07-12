
# AlphaEdge V13.0.5 – API Reference

## Overview

This document provides a comprehensive API reference for AlphaEdge V13.0.5. The API is organized by agent functionality and includes both internal and external interfaces.

---

## Table of Contents

1. [Core APIs](#core-apis)
2. [Agent APIs](#agent-apis)
3. [Gold Swap APIs](#gold-swap-apis)
4. [RPC APIs](#rpc-apis)
5. [Risk Management APIs](#risk-management-apis)
6. [Event Bus APIs](#event-bus-apis)
7. [State Manager APIs](#state-manager-apis)
8. [Command APIs](#command-apis)

---

## Core APIs

### EventBus

The central event bus for inter-agent communication.

```python
class EventBus:
    """Central event bus for inter-agent communication"""
    
    async def publish(event: Event) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event: Event object with type and data
            
        Example:
            event = Event(
                event_type="gold_swap_requested",
                data={'amount': 1000, 'asset': 'paxg'},
                source="command_interface"
            )
            await event_bus.publish(event)
        """
        
    async def subscribe(event_type: str, handler: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: String identifier for the event
            handler: Async function to handle the event
            
        Example:
            await event_bus.subscribe("depeg_detected", self.handle_depeg)
        """
        
    async def unsubscribe(event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event type"""
```

StateManager

Persistent state management across agents.

```python
class StateManager:
    """Persistent state management"""
    
    async def get(key: str, default: Any = None) -> Any:
        """
        Get value from state
        
        Args:
            key: String key for the value
            default: Default value if key not found
            
        Returns:
            Stored value or default
            
        Example:
            holdings = await state_manager.get('gold_holdings', {})
        """
        
    async def set(key: str, value: Any) -> None:
        """
        Set value in state
        
        Args:
            key: String key for the value
            value: Value to store
            
        Example:
            await state_manager.set('gold_holdings', {'paxg': 0.25})
        """
        
    async def delete(key: str) -> None:
        """Delete a key from state"""
        
    async def get_all() -> Dict[str, Any]:
        """Get all state values"""
```

---

Agent APIs

Agent 63 – Profit Taking Executor

Main executor for profit taking and gold swaps.

```python
class ProfitTakingExecutor:
    """Profit Taking Executor with gold swap capabilities"""
    
    # ============================================
    # Gold Swap APIs
    # ============================================
    
    async def execute_gold_swap(
        usdt_amount: float,
        preferred_asset: str = 'paxg'
    ) -> Dict:
        """
        Execute USDT to gold swap
        
        Args:
            usdt_amount: Amount of USDT to swap
            preferred_asset: 'paxg' (primary) or 'xaut' (fallback)
            
        Returns:
            Dict with swap results
            
        Example:
            result = await executor.execute_gold_swap(1000, 'paxg')
            # Returns: {'status': 'executed', 'asset_received': 0.2525}
        """
        
    async def execute_stable_swap(
        asset: str = None,
        amount: float = None
    ) -> Dict:
        """
        Swap gold back to stablecoins
        
        Args:
            asset: 'paxg', 'xaut', or None (all)
            amount: Amount to swap, or None (all)
            
        Returns:
            Dict with recovery results
            
        Example:
            result = await executor.execute_stable_swap()
            # Returns: {'status': 'executed', 'total_usdt': 15000}
        """
        
    async def check_asset_availability(
        asset: str,
        amount: float
    ) -> bool:
        """
        Check if asset is available for swap
        
        Args:
            asset: 'paxg' or 'xaut'
            amount: Amount to check liquidity for
            
        Returns:
            True if asset is available
            
        Example:
            available = await executor.check_asset_availability('paxg', 1000)
        """
        
    async def find_best_platform_for_asset(
        usdt_amount: float,
        asset: str
    ) -> Optional[Dict]:
        """
        Find best platform for specific asset
        
        Args:
            usdt_amount: Amount to swap
            asset: 'paxg' or 'xaut'
            
        Returns:
            Platform dict with metrics or None
            
        Example:
            platform = await executor.find_best_platform_for_asset(1000, 'paxg')
            # Returns: {'name': 'jupiter', 'chain': 'solana', 'total_cost': 2.01}
        """
        
    async def store_gold_swap(
        result: Dict,
        asset: str
    ) -> None:
        """
        Store gold swap result in state
        
        Args:
            result: Swap result dict
            asset: Asset swapped
        """

### Agent 18 – Risk Guardian

Risk management and protection.

```python
class RiskGuardian:
    """Risk management and protection"""
    
    async def calculate_stop_loss(
        token: str,
        cap_tier: str
    ) -> float:
        """
        Calculate stop loss for a token
        
        Args:
            token: Token symbol
            cap_tier: 'micro_cap', 'small_cap', 'mid_cap', 'large_cap'
            
        Returns:
            Stop loss price
            
        Example:
            sl = await guardian.calculate_stop_loss('SOL', 'mid_cap')
        """
        
    async def calculate_take_profit(
        token: str,
        entry_price: float
    ) -> Dict[str, float]:
        """
        Calculate take profit targets
        
        Args:
            token: Token symbol
            entry_price: Entry price
            
        Returns:
            Dict with tier targets
            
        Example:
            targets = await guardian.calculate_take_profit('SOL', 100.0)
            # Returns: {'tier_1': 115.0, 'tier_2': 125.0, ...}
        """
        
    async def calculate_position_size(
        token: str,
        cap_tier: str,
        entry_price: float
    ) -> float:
        """
        Calculate position size
        
        Args:
            token: Token symbol
            cap_tier: Cap tier
            entry_price: Entry price
            
        Returns:
            Position size in token units
        """
        
    async def check_drawdown(
        current_value: float,
        peak_value: float
    ) -> bool:
        """
        Check if drawdown exceeds threshold
        
        Args:
            current_value: Current portfolio value
            peak_value: Peak portfolio value
            
        Returns:
            True if drawdown exceeds threshold
        """
```

Agent 72 – Command Interface

Telegram/web dashboard commands.

```python
class CommandInterface:
    """Command interface for bot control"""
    
    async def cmd_swap_gold(args: List[str]) -> Dict:
        """
        /swap_gold [amount] [--paxg|--xaut]
        
        Args:
            args: ['1000', '--paxg']
            
        Returns:
            Command response dict
        """
        
    async def cmd_gold_holdings(args: List[str]) -> Dict:
        """
        /gold_holdings
        
        Returns:
            Gold holdings status
        """
        
    async def cmd_gold_price(args: List[str]) -> Dict:
        """
        /gold_price
        
        Returns:
            Current PAXG price
        """
        
    async def cmd_swap_stable(args: List[str]) -> Dict:
        """
        /swap_stable [amount|all]
        
        Args:
            args: ['all'] or ['1000']
            
        Returns:
            Recovery status
        """
```

---

Gold Swap APIs

Platform Selection

```python
# Best platforms for gold swap
PLATFORMS = {
    'jupiter': {
        'chain': 'solana',
        'fee': 0.002,
        'priority': 1,
        'supported_assets': ['paxg']
    },
    '1inch': {
        'chain': 'ethereum',
        'fee': 0.001,
        'priority': 2,
        'supported_assets': ['paxg', 'xaut']
    },
    'pancakeswap': {
        'chain': 'bsc',
        'fee': 0.0025,
        'priority': 3,
        'supported_assets': ['paxg', 'xaut']
    }
}

async def get_platform_metrics(
    platform: str,
    amount: float,
    asset: str
) -> Dict:
    """
    Get real-time platform metrics
    
    Args:
        platform: Platform name
        amount: Trade amount
        asset: Asset to trade
        
    Returns:
        Metrics dict with fees, slippage, liquidity
        
    Example:
        metrics = await get_platform_metrics('jupiter', 1000, 'paxg')
        # Returns: {'fees': 2.0, 'slippage': 1.0, 'gas_cost': 0.01}
    """
```

Asset Configuration

```python
ASSETS = {
    'paxg': {
        'symbol': 'PAXG',
        'name': 'Paxos Gold',
        'priority': 1,
        'min_liquidity': 100000,
        'max_deviation': 0.005,
        'chains': {
            'solana': {'address': 'So111...', 'platforms': ['jupiter']},
            'ethereum': {'address': '0x4580...', 'platforms': ['1inch', 'curve']},
            'bsc': {'address': '0x8ac7...', 'platforms': ['pancakeswap']}
        }
    },
    'xaut': {
        'symbol': 'XAUT',
        'name': 'Tether Gold',
        'priority': 2,
        'min_liquidity': 50000,
        'max_deviation': 0.01,
        'chains': {
            'ethereum': {'address': '0x6874...', 'platforms': ['1inch']},
            'bsc': {'address': '0x1b81...', 'platforms': ['pancakeswap']}
        }
    }
}
```

---

RPC APIs

RPC Manager

```python
class RPCManager:
    """RPC connection manager with failover"""
    
    async def get_connection(chain: str) -> Optional[Dict]:
        """
        Get an active RPC connection
        
        Args:
            chain: 'solana', 'ethereum', 'bsc'
            
        Returns:
            RPC endpoint dict or None
            
        Example:
            rpc = await rpc_manager.get_connection('solana')
            # Returns: {'name': 'jito', 'url': 'https://...'}
        """
        
    async def test_connection(
        chain: str,
        endpoint: str
    ) -> bool:
        """
        Test RPC connection
        
        Args:
            chain: Chain name
            endpoint: Endpoint name
            
        Returns:
            True if connection successful
        """
        
    def mark_failed(chain: str, endpoint: str) -> None:
        """Mark an endpoint as failed"""
        
    async def recover_endpoints() -> None:
        """Attempt to recover failed endpoints"""
```

---

Event Bus APIs

Event Types

```python
# Core Events
EVENT_TYPES = {
    # Gold Swap Events
    'depeg_detected': {
        'data': {'usdc_price': float, 'usdt_price': float}
    },
    'gold_swap_requested': {
        'data': {'amount': float, 'asset': str}
    },
    'gold_swap_executed': {
        'data': {'status': str, 'asset_received': float}
    },
    'stablecoin_recovered': {
        'data': {'usdc_price': float, 'usdt_price': float}
    },
    'stable_recovery_executed': {
        'data': {'total_usdt': float}
    },
    
    # Trading Events
    'profit_take_request': {
        'data': {'request_id': str, 'order': Dict}
    },
    'profit_take_response': {
        'data': {'request_id': str, 'result': Dict}
    },
    'order_status_request': {
        'data': {'order_id': str}
    },
    'execution_cancel_request': {
        'data': {'order_id': str}
    },
    
    # System Events
    'agent_status_update': {
        'data': {'agent_id': str, 'status': str}
    },
    'system_startup': {
        'data': {'timestamp': str}
    },
    'system_shutdown': {
        'data': {'timestamp': str}
    }
}
```

---

State Manager APIs

State Keys

```python
STATE_KEYS = {
    # Gold Swap
    'gold_holdings': {
        'paxg': float,
        'xaut': float,
        'last_swap': Dict,
        'last_update': str
    },
    'gold_swap_history': List[Dict],
    'last_gold_swap': Dict,
    
    # Wallet
    'wallet_1_holdings': Dict[str, float],
    'wallet_2_holdings': Dict[str, float],
    'wallet_3_holdings': Dict[str, float],
    
    # Trading
    'positions': List[Dict],
    'trade_history': List[Dict],
    'performance_metrics': Dict,
    
    # Risk
    'risk_metrics': Dict,
    'drawdown_history': List[Dict],
    'circuit_breaker_state': Dict
}
```

---

Command APIs

Command Registry

```python
# Telegram/Web Commands
COMMANDS = {
    # Gold Swap
    '/swap_gold': {
        'description': 'Swap USDT to PAXG/XAUT',
        'usage': '/swap_gold 1000 [--paxg|--xaut]'
    },
    '/gold_status': {
        'description': 'Check gold holdings',
        'usage': '/gold_status'
    },
    '/gold_price': {
        'description': 'Check PAXG price',
        'usage': '/gold_price'
    },
    '/swap_stable': {
        'description': 'Swap gold back to stable',
        'usage': '/swap_stable [amount|all]'
    },
    '/gold_swap_history': {
        'description': 'View swap history',
        'usage': '/gold_swap_history'
    },
    
    # Trading
    '/status': {
        'description': 'Bot status',
        'usage': '/status'
    },
    '/balance': {
        'description': 'Wallet balances',
        'usage': '/balance'
    },
    '/positions': {
        'description': 'Current positions',
        'usage': '/positions'
    },
    '/performance': {
        'description': 'Bot performance',
        'usage': '/performance'
    },
    
    # Risk
    '/risk': {
        'description': 'Risk metrics',
        'usage': '/risk'
    },
    '/hedge': {
        'description': 'Hedge status',
        'usage': '/hedge'
    }
}
```

---

Error Codes

```python
ERROR_CODES = {
    # Configuration Errors (1000-1099)
    'CONFIG_NOT_FOUND': 1001,
    'CONFIG_INVALID': 1002,
    'CONFIG_MISSING_KEY': 1003,
    
    # RPC Errors (2000-2099)
    'RPC_CONNECTION_FAILED': 2001,
    'RPC_TIMEOUT': 2002,
    'RPC_RATE_LIMITED': 2003,
    'RPC_INVALID_RESPONSE': 2004,
    
    # Gold Swap Errors (3000-3099)
    'SWAP_LIQUIDITY_LOW': 3001,
    'SWAP_SLIPPAGE_HIGH': 3002,
    'SWAP_ASSET_UNAVAILABLE': 3003,
    'SWAP_EXECUTION_FAILED': 3004,
    'SWAP_GAS_INSUFFICIENT': 3005,
    
    # Risk Errors (4000-4099)
    'RISK_DRAWDOWN_EXCEEDED': 4001,
    'RISK_CIRCUIT_BREAKER': 4002,
    'RISK_BLACK_SWAN': 4003,
    'RISK_CORRELATION_HIGH': 4004,
    
    # System Errors (5000-5099)
    'SYSTEM_AGENT_FAILED': 5001,
    'SYSTEM_STARTUP_FAILED': 5002,
    'SYSTEM_SHUTDOWN_FAILED': 5003
}
```

---

Version History

Version Date Changes
V13.0.5 July 7, 2026 Added PAXG + XAUT gold swap support
V13.0.4 June 24, 2026 Added FPGA dual node support
V13.0.3 June 20, 2026 Added TPS and BPG scoring
V13.0.2 June 15, 2026 Added multi-chain execution
V13.0.1 June 10, 2026 Initial Solana integration

---

AlphaEdge V13.0.5 – API Reference Complete
