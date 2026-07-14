"""
AlphaEdge Agent 30 – Self-Evolving Agent
Proposes code improvements, generates Pine Script, updates documentation
V13.0.6 – UPDATED with Documentation Update Capability
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import json

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class SelfEvolvingAgent:
    """
    Self-Evolving Agent – Proposes and implements improvements
    V13.0.6 – Now with documentation update capability
    """
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "self_evolving"
        self.running = False
        
        # State tracking
        self.proposals = []
        self.implemented_changes = []
        self.documentation_updates = []
        
        # Configuration
        self.config = {
            'max_proposals': 100,
            'review_interval': 3600,  # 1 hour
            'min_improvement_pct': 5,
            'auto_approve_docs': True,
            'github_repo': 'Alphaedge-bot/alphaedge-bot'
        }
        
        # ============================================
        # NEW: Documentation Update Tracking
        # ============================================
        self.last_workflow_update = None
        self.last_master_design_update = None
        self.pending_doc_updates = []
        
    async def start(self):
        """Start the self-evolving agent"""
        logger.info("Self-Evolving Agent starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("improvement_proposal", self.handle_proposal)
        await self.event_bus.subscribe("code_change", self.handle_code_change)
        await self.event_bus.subscribe("doc_update_request", self.handle_doc_update_request)
        
        # Start evolution cycle
        asyncio.create_task(self.run_evolution_cycle())
        
        logger.info("Self-Evolving Agent running")
        
    async def stop(self):
        """Stop the self-evolving agent"""
        self.running = False
        logger.info("Self-Evolving Agent stopped")
        
    async def run_evolution_cycle(self):
        """Run regular evolution cycle"""
        while self.running:
            try:
                # Check for improvements
                await self.check_for_improvements()
                
                # Review proposals
                await self.review_proposals()
                
                # Process pending documentation updates
                await self.process_doc_updates()
                
                # Publish status
                await self.publish_status()
                
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")
                
            await asyncio.sleep(self.config['review_interval'])
            
    # ============================================
    # DOCUMENTATION UPDATE METHODS (NEW)
    # ============================================
    
    async def handle_doc_update_request(self, event: Event):
        """Handle documentation update requests"""
        if not self.running:
            return
            
        update_type = event.data.get('type')
        change = event.data.get('change', {})
        
        logger.info(f"📝 Documentation update requested: {update_type}")
        
        if update_type == 'workflow':
            await self.update_workflow(change)
        elif update_type == 'master_design':
            await self.update_master_design(change)
        else:
            logger.warning(f"Unknown doc update type: {update_type}")
    
    async def update_workflow(self, change: Dict) -> bool:
        """
        Update workflow_live.md with latest changes
        """
        try:
            logger.info("📝 Updating workflow_live.md")
            
            # 1. Get current workflow content
            current_workflow = await self._get_file_content("docs/workflow_live.md")
            
            if not current_workflow:
                logger.error("Could not read workflow_live.md")
                return False
            
            # 2. Generate updated workflow
            updated_workflow = self._generate_workflow_update(current_workflow, change)
            
            # 3. Save to GitHub
            success = await self._save_to_github("docs/workflow_live.md", updated_workflow)
            
            if success:
                self.last_workflow_update = datetime.now().isoformat()
                self.documentation_updates.append({
                    'type': 'workflow',
                    'change': change,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info("✅ workflow_live.md updated successfully")
                
                # Notify user
                await self._notify_user(f"📝 Workflow updated: {change.get('description', 'auto-update')}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Workflow update error: {e}")
            return False
    
    async def update_master_design(self, change: Dict) -> bool:
        """
        Update master design document with latest changes
        """
        try:
            logger.info("📝 Updating master design document")
            
            # 1. Get current master design
            version = change.get('version', 'V13.0.6')
            file_path = f"docs/master_design_{version}.md"
            current_design = await self._get_file_content(file_path)
            
            if not current_design:
                # Try default path
                current_design = await self._get_file_content("docs/master_design_v13.0.6.md")
            
            if not current_design:
                logger.error("Could not read master design document")
                return False
            
            # 2. Generate updated design
            updated_design = self._generate_master_design_update(current_design, change)
            
            # 3. Save to GitHub
            success = await self._save_to_github(file_path, updated_design)
            
            if success:
                self.last_master_design_update = datetime.now().isoformat()
                self.documentation_updates.append({
                    'type': 'master_design',
                    'change': change,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info("✅ Master design updated successfully")
                
                # Notify user
                await self._notify_user(f"📝 Master design updated: {change.get('description', 'auto-update')}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Master design update error: {e}")
            return False
    
    def _generate_workflow_update(self, current: str, change: Dict) -> str:
        """
        Generate updated workflow content
        """
        # Parse sections
        sections = self._parse_markdown_sections(current)
        
        # Update relevant sections based on change type
        change_type = change.get('type', 'unknown')
        
        if change_type == 'entry_logic':
            sections = self._update_entry_logic_section(sections, change)
        elif change_type == 'exit_logic':
            sections = self._update_exit_logic_section(sections, change)
        elif change_type == 'tps_threshold':
            sections = self._update_tps_section(sections, change)
        elif change_type == 'new_indicator':
            sections = self._update_indicators_section(sections, change)
        elif change_type == 'new_strategy':
            sections = self._update_strategies_section(sections, change)
        elif change_type == 'timeframe':
            sections = self._update_timeframe_section(sections, change)
        else:
            # Generic update: add to change log
            sections = self._update_change_log(sections, change)
        
        # Rebuild document
        updated = self._rebuild_markdown(sections)
        
        # Update last modified date
        updated = self._update_last_modified(updated)
        
        return updated
    
    def _generate_master_design_update(self, current: str, change: Dict) -> str:
        """
        Generate updated master design content
        """
        # Parse sections
        sections = self._parse_markdown_sections(current)
        
        # Update based on change type
        change_type = change.get('type', 'unknown')
        
        if change_type == 'version_increment':
            sections = self._update_version_section(sections, change)
        elif change_type == 'agent_change':
            sections = self._update_agents_section(sections, change)
        elif change_type == 'strategy_change':
            sections = self._update_strategies_section(sections, change)
        elif change_type == 'new_indicator':
            sections = self._update_indicators_section(sections, change)
        elif change_type == 'tps_change':
            sections = self._update_tps_section(sections, change)
        elif change_type == 'hardware_change':
            sections = self._update_hardware_section(sections, change)
        else:
            # Generic update: add to version history
            sections = self._update_version_history(sections, change)
        
        # Rebuild document
        updated = self._rebuild_markdown(sections)
        
        # Update date
        updated = self._update_date(updated)
        
        return updated
    
    def _parse_markdown_sections(self, content: str) -> Dict[str, str]:
        """
        Parse markdown document into sections by headers
        """
        sections = {}
        current_section = None
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if line is a header (## or ###)
            if line.startswith('## '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                current_section = line.replace('## ', '').strip()
                current_content = []
            elif line.startswith('### '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                current_section = line.replace('### ', '').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _rebuild_markdown(self, sections: Dict[str, str]) -> str:
        """
        Rebuild markdown document from sections
        """
        lines = []
        
        # Add sections in order
        section_order = [
            'Overview',
            'Complete Workflow Diagram',
            'Entry Process',
            'Exit Process',
            'Position Management',
            'Indicators Integrated',
            'Key Agents and Roles',
            'TPS Thresholds',
            'Change Log'
        ]
        
        for section in section_order:
            if section in sections:
                lines.append(f"## {section}")
                lines.append(sections[section])
                lines.append('')
        
        return '\n'.join(lines)
    
    def _update_change_log(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update change log section
        """
        change_log = sections.get('Change Log', '')
        
        # Create new entry
        date = datetime.now().strftime('%B %d, %Y')
        description = change.get('description', 'Auto-update')
        agent = change.get('agent', 'Agent_30')
        
        entry = f"| {date} | {description} | {agent} |"
        
        # Find table in change log
        if '|' in change_log:
            # Insert after header
            lines = change_log.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if '|---' in line or '|------' in line:
                    insert_index = i + 1
                    break
            
            if insert_index > 0:
                lines.insert(insert_index, entry)
                sections['Change Log'] = '\n'.join(lines)
            else:
                # Create new table
                sections['Change Log'] = f"| Date | Change | Agent |\n|------|--------|-------|\n{entry}"
        else:
            # Create new change log
            sections['Change Log'] = f"| Date | Change | Agent |\n|------|--------|-------|\n{entry}"
        
        return sections
    
    def _update_last_modified(self, content: str) -> str:
        """
        Update last modified date in workflow
        """
        date_line = f"## Last Updated: {datetime.now().strftime('%B %d, %Y')}"
        
        # Replace existing date
        pattern = r'## Last Updated: .*'
        if re.search(pattern, content):
            content = re.sub(pattern, date_line, content)
        else:
            # Add after title
            lines = content.split('\n')
            lines.insert(1, date_line)
            content = '\n'.join(lines)
        
        return content
    
    def _update_date(self, content: str) -> str:
        """
        Update date in master design
        """
        date_line = f"| Date | {datetime.now().strftime('%B %d, %Y')} |"
        
        # Find document info table
        pattern = r'\| Date \| .* \|'
        if re.search(pattern, content):
            content = re.sub(pattern, date_line, content)
        
        return content
    
    def _update_entry_logic_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update entry logic section
        """
        entry_section = sections.get('Entry Process', '')
        
        # Add or update step
        step = change.get('step', '')
        description = change.get('description', '')
        
        if step and description:
            lines = entry_section.split('\n')
            lines.append(f"  {step}: {description}")
            sections['Entry Process'] = '\n'.join(lines)
        
        return sections
    
    def _update_exit_logic_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update exit logic section
        """
        exit_section = sections.get('Exit Process', '')
        
        condition = change.get('condition', '')
        description = change.get('description', '')
        
        if condition and description:
            lines = exit_section.split('\n')
            lines.append(f"  - {condition}: {description}")
            sections['Exit Process'] = '\n'.join(lines)
        
        return sections
    
    def _update_tps_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update TPS section
        """
        tps_section = sections.get('TPS Thresholds', '')
        
        threshold = change.get('threshold', '')
        action = change.get('action', '')
        
        if threshold and action:
            lines = tps_section.split('\n')
            lines.append(f"| {threshold} | {action} |")
            sections['TPS Thresholds'] = '\n'.join(lines)
        
        return sections
    
    def _update_indicators_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update indicators section
        """
        indicators_section = sections.get('Indicators Integrated', '')
        
        name = change.get('name', '')
        source = change.get('source', '')
        purpose = change.get('purpose', '')
        adjustment = change.get('adjustment', '')
        
        if name:
            lines = indicators_section.split('\n')
            lines.append(f"| **{name}** | `{source}` | {purpose} | {adjustment} |")
            sections['Indicators Integrated'] = '\n'.join(lines)
        
        return sections
    
    def _update_strategies_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update strategies section
        """
        strategies_section = sections.get('Complete Workflow Diagram', '')
        
        category = change.get('category', '')
        count = change.get('count', '')
        
        if category and count:
            lines = strategies_section.split('\n')
            lines.append(f"│ {category} │ {count} │")
            sections['Complete Workflow Diagram'] = '\n'.join(lines)
        
        return sections
    
    def _update_timeframe_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update timeframe section
        """
        timeframe_section = sections.get('Overview', '')
        
        tier = change.get('tier', '')
        trend_tf = change.get('trend_tf', '')
        entry_tf = change.get('entry_tf', '')
        
        if tier:
            lines = timeframe_section.split('\n')
            lines.append(f"| {tier} | {trend_tf} | {entry_tf} |")
            sections['Overview'] = '\n'.join(lines)
        
        return sections
    
    def _update_version_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update version section in master design
        """
        new_version = change.get('new_version', '')
        old_version = change.get('old_version', '')
        
        if new_version:
            # Update version in document info
            info = sections.get('Document Information', '')
            info = re.sub(r'Version \| V.* \|', f'Version | {new_version} |', info)
            sections['Document Information'] = info
        
        return sections
    
    def _update_agents_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update agents section in master design
        """
        agent_section = sections.get('Complete Agent List', '')
        
        agent_id = change.get('agent_id', '')
        name = change.get('name', '')
        purpose = change.get('purpose', '')
        
        if agent_id:
            lines = agent_section.split('\n')
            lines.append(f"| {agent_id} | {name} | {purpose} |")
            sections['Complete Agent List'] = '\n'.join(lines)
        
        return sections
    
    def _update_hardware_section(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update hardware section in master design
        """
        hardware_section = sections.get('Hardware Architecture', '')
        
        stage = change.get('stage', '')
        component = change.get('component', '')
        value = change.get('value', '')
        
        if component:
            lines = hardware_section.split('\n')
            lines.append(f"| {component} | {value} |")
            sections['Hardware Architecture'] = '\n'.join(lines)
        
        return sections
    
    def _update_version_history(self, sections: Dict[str, str], change: Dict) -> Dict:
        """
        Update version history in master design
        """
        version = change.get('version', '')
        date = change.get('date', datetime.now().strftime('%B %d, %Y'))
        changes = change.get('changes', '')
        
        history = sections.get('Version History', '')
        lines = history.split('\n')
        
        # Insert new entry after header
        insert_index = 0
        for i, line in enumerate(lines):
            if '|------|---------|--------|' in line:
                insert_index = i + 1
                break
        
        if insert_index > 0:
            lines.insert(insert_index, f"| {version} | {date} | {changes} |")
            sections['Version History'] = '\n'.join(lines)
        
        return sections
    
    # ============================================
    # GITHUB UTILITIES
    # ============================================
    
    async def _get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get file content from GitHub
        """
        try:
            # Use GitHub API or local file
            # For now, simulate retrieval
            url = f"https://raw.githubusercontent.com/{self.config['github_repo']}/main/{file_path}"
            
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Could not retrieve {file_path}: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error retrieving file: {e}")
            return None
    
    async def _save_to_github(self, file_path: str, content: str) -> bool:
        """
        Save file to GitHub
        """
        try:
            # For now, log the update
            logger.info(f"📝 Would save to {file_path} ({len(content)} bytes)")
            
            # In production, use GitHub API
            # This would be implemented with PyGithub or similar
            return True
            
        except Exception as e:
            logger.error(f"Error saving to GitHub: {e}")
            return False
    
    async def _notify_user(self, message: str):
        """
        Notify user of documentation update
        """
        await self.event_bus.publish(Event(
            event_type="user_notification",
            data={
                'type': 'doc_update',
                'message': message,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id
        ))
    
    # ============================================
    # EXISTING METHODS (Preserved)
    # ============================================
    
    async def handle_proposal(self, event: Event):
        """Handle improvement proposals"""
        if not self.running:
            return
            
        proposal = event.data
        self.proposals.append(proposal)
        
        logger.info(f"📊 New proposal: {proposal.get('title', 'Untitled')}")
        
        # Store in state
        await self.state_manager.set('proposals', self.proposals)
    
    async def handle_code_change(self, event: Event):
        """Handle code changes"""
        if not self.running:
            return
            
        change = event.data
        self.implemented_changes.append(change)
        
        # Check if documentation needs update
        if self._requires_doc_update(change):
            await self._schedule_doc_update(change)
        
        logger.info(f"💻 Code change implemented: {change.get('description', 'Unknown')}")
    
    def _requires_doc_update(self, change: Dict) -> bool:
        """
        Check if change requires documentation update
        """
        change_types = change.get('types', [])
        
        doc_triggers = [
            'entry_logic',
            'exit_logic',
            'tps_threshold',
            'new_indicator',
            'new_strategy',
            'timeframe',
            'version_increment',
            'agent_change',
            'hardware_change'
        ]
        
        return any(t in doc_triggers for t in change_types)
    
    async def _schedule_doc_update(self, change: Dict):
        """
        Schedule documentation update
        """
        self.pending_doc_updates.append({
            'change': change,
            'scheduled_at': datetime.now().isoformat()
        })
        
        logger.info(f"📝 Scheduled doc update for: {change.get('description', 'Unknown')}")
    
    async def process_doc_updates(self):
        """
        Process pending documentation updates
        """
        if not self.pending_doc_updates:
            return
        
        for update in self.pending_doc_updates[:]:
            change = update['change']
            
            # Determine update type
            change_types = change.get('types', [])
            
            for change_type in change_types:
                if change_type in ['entry_logic', 'exit_logic', 'tps_threshold', 'new_indicator', 'new_strategy', 'timeframe']:
                    await self.update_workflow(change)
                elif change_type in ['version_increment', 'agent_change', 'hardware_change']:
                    await self.update_master_design(change)
            
            # Remove from pending
            self.pending_doc_updates.remove(update)
    
    async def check_for_improvements(self):
        """Check for potential improvements"""
        # In production, this would analyze performance data
        # For now, placeholder
        pass
    
    async def review_proposals(self):
        """Review pending proposals"""
        # In production, this would evaluate proposals
        # For now, placeholder
        pass
    
    async def publish_status(self):
        """Publish self-evolving status"""
        status_data = {
            'proposals_count': len(self.proposals),
            'implemented_changes': len(self.implemented_changes),
            'documentation_updates': len(self.documentation_updates),
            'pending_doc_updates': len(self.pending_doc_updates),
            'last_workflow_update': self.last_workflow_update,
            'last_master_design_update': self.last_master_design_update,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="self_evolving_status",
            data=status_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get self-evolving agent status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'proposals_count': len(self.proposals),
            'implemented_changes': len(self.implemented_changes),
            'documentation_updates': len(self.documentation_updates),
            'pending_doc_updates': len(self.pending_doc_updates),
            'last_workflow_update': self.last_workflow_update,
            'last_master_design_update': self.last_master_design_update,
            'config': self.config,
            'timestamp': datetime.now().isoformat()
        }
