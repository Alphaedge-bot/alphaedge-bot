"""
AlphaEdge State Manager – State Persistence with 3-Way WAL
Manages bot state, positions, and checkpoints with crash recovery
"""

import asyncio
import logging
import json
import pickle
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class StateManager:
    """
    State Manager with 3-Way Write-Ahead Log (WAL)
    Ensures data durability and crash recovery
    """
    
    def __init__(self, wal):
        """
        Initialize State Manager
        
        Args:
            wal: WriteAheadLog instance for persistence
        """
        self.wal = wal
        self.state: Dict[str, Any] = {}
        self.checkpoints: List[Dict[str, Any]] = []
        self.max_checkpoints = 100
        self.dirty = False
        self.lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize state manager and recover from WAL"""
        logger.info("Initializing State Manager...")
        
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        Path("data/checkpoints").mkdir(exist_ok=True)
        
        # Recover from WAL
        await self.recover()
        
        logger.info("State Manager initialized")
        
    async def recover(self):
        """Recover state from WAL"""
        try:
            # Get last checkpoint
            checkpoint = await self.wal.get_last_checkpoint()
            if checkpoint:
                self.state = checkpoint.get('state', {})
                logger.info(f"Recovered state from checkpoint: {len(self.state)} keys")
                
            # Replay operations after checkpoint
            operations = await self.wal.get_operations_after_checkpoint()
            for op in operations:
                await self._apply_operation(op)
                
            logger.info(f"Replayed {len(operations)} operations")
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self.state = {}
            
    async def _apply_operation(self, operation: Dict[str, Any]):
        """Apply a single operation to the state"""
        op_type = operation.get('type')
        key = operation.get('key')
        value = operation.get('value')
        
        if op_type == 'set':
            self.state[key] = value
        elif op_type == 'delete':
            self.state.pop(key, None)
        elif op_type == 'update':
            if key in self.state and isinstance(self.state[key], dict):
                self.state[key].update(value)
                
    async def set(self, key: str, value: Any, persist: bool = True):
        """
        Set a state value
        
        Args:
            key: State key
            value: Value to set
            persist: If True, write to WAL
        """
        async with self.lock:
            self.state[key] = value
            self.dirty = True
            
            if persist:
                await self.wal.write_operation('set', key, value)
                
    async def get(self, key: str, default: Any = None) -> Any:
        """Get a state value"""
        return self.state.get(key, default)
        
    async def delete(self, key: str, persist: bool = True):
        """Delete a state value"""
        async with self.lock:
            if key in self.state:
                del self.state[key]
                self.dirty = True
                
                if persist:
                    await self.wal.write_operation('delete', key)
                    
    async def update(self, key: str, value: Dict[str, Any], persist: bool = True):
        """Update a nested state value"""
        async with self.lock:
            if key not in self.state:
                self.state[key] = {}
                
            if isinstance(self.state[key], dict):
                self.state[key].update(value)
                self.dirty = True
                
                if persist:
                    await self.wal.write_operation('update', key, value)
                    
    async def save_checkpoint(self) -> bool:
        """Save a checkpoint of the current state"""
        async with self.lock:
            try:
                checkpoint = {
                    'timestamp': datetime.now().isoformat(),
                    'state': self.state.copy(),
                    'checksum': self._calculate_checksum(self.state)
                }
                
                # Store in memory
                self.checkpoints.append(checkpoint)
                if len(self.checkpoints) > self.max_checkpoints:
                    self.checkpoints.pop(0)
                    
                # Write to WAL
                await self.wal.write_checkpoint(checkpoint)
                
                # Write to disk
                checkpoint_file = f"data/checkpoints/checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint, f, indent=2)
                    
                self.dirty = False
                logger.info(f"Checkpoint saved: {checkpoint_file}")
                return True
                
            except Exception as e:
                logger.error(f"Checkpoint save failed: {e}")
                return False
                
    async def load_checkpoint(self, checkpoint_index: int = -1) -> bool:
        """Load a checkpoint"""
        if not self.checkpoints:
            logger.warning("No checkpoints available")
            return False
            
        try:
            checkpoint = self.checkpoints[checkpoint_index]
            
            # Verify checksum
            if self._calculate_checksum(checkpoint['state']) != checkpoint['checksum']:
                logger.error("Checkpoint checksum mismatch")
                return False
                
            self.state = checkpoint['state'].copy()
            self.dirty = False
            logger.info(f"Loaded checkpoint from {checkpoint['timestamp']}")
            return True
            
        except Exception as e:
            logger.error(f"Checkpoint load failed: {e}")
            return False
            
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum of state data"""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()
        
    async def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current state"""
        return self.state.copy()
        
    async def get_checkpoints(self) -> List[Dict[str, Any]]:
        """Get list of checkpoints"""
        return self.checkpoints.copy()
        
    async def export_state(self, filepath: str) -> bool:
        """Export state to file"""
        try:
            async with self.lock:
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'state': self.state,
                    'version': 'V13.0.5'
                }
                
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                logger.info(f"State exported to {filepath}")
                return True
                
        except Exception as e:
            logger.error(f"State export failed: {e}")
            return False
            
    async def import_state(self, filepath: str) -> bool:
        """Import state from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            async with self.lock:
                self.state = data.get('state', {})
                self.dirty = True
                logger.info(f"State imported from {filepath}")
                return True
                
        except Exception as e:
            logger.error(f"State import failed: {e}")
            return False
            
    async def get_position(self, token: str) -> Optional[Dict[str, Any]]:
        """Get position for a specific token"""
        positions = await self.get('positions', {})
        return positions.get(token)
        
    async def set_position(self, token: str, position: Dict[str, Any]):
        """Set position for a token"""
        positions = await self.get('positions', {})
        positions[token] = position
        await self.set('positions', positions)
        
    async def delete_position(self, token: str):
        """Delete position for a token"""
        positions = await self.get('positions', {})
        if token in positions:
            del positions[token]
            await self.set('positions', positions)
            
    async def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all positions"""
        return await self.get('positions', {})
        
    async def shutdown(self):
        """Shutdown state manager"""
        logger.info("State Manager shutting down...")
        await self.save_checkpoint()
