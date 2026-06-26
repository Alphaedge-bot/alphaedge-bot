"""
AlphaEdge Agent 48 – Audit Logger
Immutable audit trail (JSON + SHA-256), 7-year retention, tamper-proof
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import hashlib
import os
import gzip
import shutil

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit Logger – Immutable audit trail with tamper-proofing"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "audit_logger"
        self.running = False
        
        # Audit state
        self.audit_chain = []
        self.current_hash = ""
        self.audit_count = 0
        
        # Configuration
        self.config = {
            'retention_years': 7,
            'log_format': 'json',
            'compression': True,
            'max_chain_size': 10000
        }
        
        # Log directory
        self.log_dir = "data/audit/"
        
    async def start(self):
        """Start the audit logger"""
        logger.info("Audit Logger starting...")
        self.running = True
        
        # Create log directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize audit chain
        await self.initialize_audit_chain()
        
        # Subscribe to events
        await self.event_bus.subscribe("audit_event", self.handle_audit_event)
        await self.event_bus.subscribe("audit_request", self.handle_audit_request)
        await self.event_bus.subscribe("verification_request", self.handle_verification_request)
        
        # Start audit cycle
        asyncio.create_task(self.run_audit_cycle())
        
        logger.info("Audit Logger running")
        
    async def stop(self):
        """Stop the audit logger"""
        self.running = False
        
        # Final flush
        await self.flush_audit_chain()
        
        logger.info("Audit Logger stopped")
        
    async def initialize_audit_chain(self):
        """Initialize the audit chain"""
        # Check for existing chain
        chain_file = f"{self.log_dir}audit_chain.json"
        
        if os.path.exists(chain_file):
            try:
                with open(chain_file, 'r') as f:
                    data = json.load(f)
                    self.audit_chain = data.get('chain', [])
                    self.current_hash = data.get('current_hash', "")
                    self.audit_count = data.get('count', 0)
                    logger.info(f"Loaded audit chain with {len(self.audit_chain)} entries")
            except Exception as e:
                logger.error(f"Failed to load audit chain: {e}")
                self.audit_chain = []
                self.current_hash = ""
        else:
            # Initialize new chain
            self.audit_chain = []
            self.current_hash = hashlib.sha256(b"GENESIS").hexdigest()
            self.audit_count = 0
            
            # Create initial entry
            entry = {
                'index': 0,
                'timestamp': datetime.now().isoformat(),
                'event': 'GENESIS',
                'data': {'message': 'Audit chain initialized'},
                'previous_hash': '',
                'hash': self.current_hash
            }
            self.audit_chain.append(entry)
            self.audit_count = 1
            
            # Save initial chain
            await self.save_audit_chain()
            
        await self.state_manager.set('audit_hash', self.current_hash)
        
    async def run_audit_cycle(self):
        """Run regular audit cycle"""
        while self.running:
            try:
                # Flush audit chain if needed
                if len(self.audit_chain) >= self.config['max_chain_size']:
                    await self.flush_audit_chain()
                    
                # Archive old logs
                await self.archive_old_logs()
                
                # Publish audit update
                await self.publish_audit_update()
                
            except Exception as e:
                logger.error(f"Audit cycle error: {e}")
                
            await asyncio.sleep(60)  # Every minute
            
    async def handle_audit_event(self, event: Event):
        """Handle audit events"""
        if not self.running:
            return
            
        event_type = event.data.get('type', 'unknown')
        event_data = event.data.get('data', {})
        
        # Create audit entry
        entry = await self.create_audit_entry(event_type, event_data)
        
        # Add to chain
        self.audit_chain.append(entry)
        self.audit_count += 1
        self.current_hash = entry['hash']
        
        # Store in state
        await self.state_manager.set('audit_hash', self.current_hash)
        
        logger.debug(f"Audit entry: {entry['index']} - {event_type}")
        
    async def handle_audit_request(self, event: Event):
        """Handle audit requests"""
        if not self.running:
            return
            
        start = event.data.get('start', 0)
        end = event.data.get('end', len(self.audit_chain))
        
        # Get audit entries
        entries = self.audit_chain[start:end]
        
        response = Event(
            event_type="audit_response",
            data={
                'start': start,
                'end': end,
                'entries': entries,
                'total': len(self.audit_chain),
                'current_hash': self.current_hash,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_verification_request(self, event: Event):
        """Handle verification requests"""
        if not self.running:
            return
            
        # Verify audit chain integrity
        verification = await self.verify_audit_chain()
        
        response = Event(
            event_type="verification_response",
            data={
                'verified': verification['verified'],
                'details': verification['details'],
                'current_hash': self.current_hash,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def create_audit_entry(self, event_type: str, data: Dict) -> Dict:
        """Create a new audit entry"""
        index = self.audit_count
        
        # Calculate hash
        entry_data = {
            'index': index,
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'data': data,
            'previous_hash': self.current_hash
        }
        
        # Create hash
        entry_string = json.dumps(entry_data, sort_keys=True)
        entry_hash = hashlib.sha256(entry_string.encode()).hexdigest()
        
        entry_data['hash'] = entry_hash
        
        return entry_data
        
    async def verify_audit_chain(self) -> Dict:
        """Verify the integrity of the audit chain"""
        verified = True
        details = []
        
        if len(self.audit_chain) == 0:
            return {'verified': True, 'details': ['Empty chain']}
            
        # Verify each entry
        for i, entry in enumerate(self.audit_chain):
            # Check previous hash
            if i > 0:
                expected_prev_hash = self.audit_chain[i-1]['hash']
                if entry['previous_hash'] != expected_prev_hash:
                    verified = False
                    details.append(f"Invalid previous hash at index {i}")
                    
            # Verify hash
            entry_data = {
                'index': entry['index'],
                'timestamp': entry['timestamp'],
                'event': entry['event'],
                'data': entry['data'],
                'previous_hash': entry['previous_hash']
            }
            entry_string = json.dumps(entry_data, sort_keys=True)
            expected_hash = hashlib.sha256(entry_string.encode()).hexdigest()
            
            if entry['hash'] != expected_hash:
                verified = False
                details.append(f"Invalid hash at index {i}")
                
        # Verify current hash
        if self.audit_chain:
            last_entry = self.audit_chain[-1]
            if self.current_hash != last_entry['hash']:
                verified = False
                details.append("Current hash mismatch")
                
        return {'verified': verified, 'details': details}
        
    async def flush_audit_chain(self):
        """Flush audit chain to disk"""
        if not self.audit_chain:
            return
            
        try:
            # Save chain to file
            await self.save_audit_chain()
            
            # Archive if needed
            if len(self.audit_chain) >= self.config['max_chain_size']:
                await self.archive_audit_chain()
                
        except Exception as e:
            logger.error(f"Failed to flush audit chain: {e}")
            
    async def save_audit_chain(self):
        """Save audit chain to disk"""
        chain_file = f"{self.log_dir}audit_chain.json"
        
        data = {
            'chain': self.audit_chain,
            'current_hash': self.current_hash,
            'count': self.audit_count,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(chain_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    async def archive_audit_chain(self):
        """Archive the audit chain"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_file = f"{self.log_dir}audit_{timestamp}.json"
        
        # Save current chain to archive
        data = {
            'chain': self.audit_chain,
            'current_hash': self.current_hash,
            'count': self.audit_count,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(archive_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        # Compress if enabled
        if self.config['compression']:
            with open(archive_file, 'rb') as f_in:
                with gzip.open(f"{archive_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(archive_file)
            
        # Reset chain
        self.audit_chain = []
        self.current_hash = hashlib.sha256(b"ARCHIVE").hexdigest()
        
        # Create new genesis entry
        entry = await self.create_audit_entry('ARCHIVE', {'archived': timestamp})
        self.audit_chain.append(entry)
        self.current_hash = entry['hash']
        
        await self.save_audit_chain()
        
    async def archive_old_logs(self):
        """Archive logs older than retention period"""
        retention_days = self.config['retention_years'] * 365
        
        # Check all files in log directory
        for filename in os.listdir(self.log_dir):
            if filename.startswith('audit_') and filename.endswith('.json.gz'):
                filepath = os.path.join(self.log_dir, filename)
                
                # Extract date from filename
                try:
                    date_str = filename.split('_')[1].split('.')[0]
                    file_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    
                    # Check age
                    age = (datetime.now() - file_date).days
                    if age > retention_days:
                        # Delete old file
                        os.remove(filepath)
                        logger.info(f"Removed old audit log: {filename}")
                except Exception:
                    continue
                    
    async def publish_audit_update(self):
        """Publish audit data update"""
        audit_data = {
            'total_entries': self.audit_count,
            'chain_size': len(self.audit_chain),
            'current_hash': self.current_hash,
            'retention_years': self.config['retention_years'],
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="audit_update",
            data=audit_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get audit logger status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_entries': self.audit_count,
            'chain_size': len(self.audit_chain),
            'retention_years': self.config['retention_years'],
            'compression': self.config['compression'],
            'timestamp': datetime.now().isoformat()
        }
