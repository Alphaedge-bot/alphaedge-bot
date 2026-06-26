"""
AlphaEdge Agent 67 – Media Creator
Generate images (BTC TA, Alt TA, Entry Setup, Bounce Confirm), apply watermark
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import random
import base64
from io import BytesIO

from core.event_bus import Event, EventBus
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class MediaCreator:
    """Media Creator – Generates and manages media content"""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.agent_id = "media_creator"
        self.running = False
        
        # Media state
        self.generated_images = []
        self.image_templates = {}
        self.watermark = "AlphaEdge V13.0.5"
        
        # Configuration
        self.config = {
            'image_formats': ['png', 'jpg'],
            'max_images': 100,
            'watermark_position': 'bottom-right',
            'watermark_opacity': 0.7
        }
        
        # Image types
        self.image_types = ['btc_ta', 'alt_ta', 'entry_setup', 'bounce_confirm']
        
    async def start(self):
        """Start the media creator"""
        logger.info("Media Creator starting...")
        self.running = True
        
        # Subscribe to events
        await self.event_bus.subscribe("media_request", self.handle_media_request)
        await self.event_bus.subscribe("image_generation_request", self.handle_image_generation)
        await self.event_bus.subscribe("watermark_request", self.handle_watermark_request)
        
        # Start media cycle
        asyncio.create_task(self.run_media_cycle())
        
        logger.info("Media Creator running")
        
    async def stop(self):
        """Stop the media creator"""
        self.running = False
        logger.info("Media Creator stopped")
        
    async def run_media_cycle(self):
        """Run regular media cycle"""
        while self.running:
            try:
                # Check for pending image requests
                await self.process_pending_requests()
                
                # Clean old images
                await self.clean_old_images()
                
                # Publish media update
                await self.publish_media_update()
                
            except Exception as e:
                logger.error(f"Media cycle error: {e}")
                
            await asyncio.sleep(300)  # Every 5 minutes
            
    async def handle_media_request(self, event: Event):
        """Handle media requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        media_type = event.data.get('media_type')
        content = event.data.get('content')
        
        # Generate media
        result = await self.generate_media(media_type, content)
        
        response = Event(
            event_type="media_response",
            data={
                'request_id': request_id,
                'media_type': media_type,
                'result': result,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_image_generation(self, event: Event):
        """Handle image generation requests"""
        if not self.running:
            return
            
        request_id = event.data.get('request_id')
        image_type = event.data.get('image_type', 'entry_setup')
        data = event.data.get('data', {})
        
        # Generate image
        image = await self.generate_image(image_type, data)
        
        response = Event(
            event_type="image_generation_response",
            data={
                'request_id': request_id,
                'image_type': image_type,
                'image': image,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def handle_watermark_request(self, event: Event):
        """Handle watermark requests"""
        if not self.running:
            return
            
        image = event.data.get('image')
        watermark_text = event.data.get('watermark', self.watermark)
        
        # Apply watermark
        watermarked = await self.apply_watermark(image, watermark_text)
        
        response = Event(
            event_type="watermark_response",
            data={
                'image': watermarked,
                'watermark': watermark_text,
                'timestamp': datetime.now().isoformat()
            },
            source=self.agent_id,
            target=event.source
        )
        await self.event_bus.publish(response)
        
    async def generate_media(self, media_type: str, content: Dict) -> Dict:
        """Generate media content"""
        if media_type == 'image':
            image_type = content.get('image_type', 'entry_setup')
            image = await self.generate_image(image_type, content.get('data', {}))
            return {'media_type': 'image', 'content': image}
        else:
            return {'status': 'unsupported_media_type'}
            
    async def generate_image(self, image_type: str, data: Dict) -> Dict:
        """Generate an image"""
        # In production, use actual image generation (PIL, matplotlib, etc.)
        # For now, simulate image generation
        
        # Validate image type
        if image_type not in self.image_types:
            image_type = 'entry_setup'
            
        # Generate image metadata
        image_id = f"img_{datetime.now().timestamp()}"
        
        # Create image data
        image_data = {
            'id': image_id,
            'type': image_type,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'watermark': self.watermark
        }
        
        # Simulate image generation
        image_content = base64.b64encode(
            f"Simulated image: {image_type}".encode()
        ).decode()
        
        image_result = {
            'id': image_id,
            'type': image_type,
            'content': image_content,
            'format': 'png',
            'watermark_applied': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store image
        self.generated_images.append(image_result)
        if len(self.generated_images) > self.config['max_images']:
            self.generated_images = self.generated_images[-self.config['max_images']:]
            
        return image_result
        
    async def apply_watermark(self, image: Dict, watermark_text: str) -> Dict:
        """Apply watermark to an image"""
        # In production, use PIL or similar
        # For now, simulate watermark application
        
        image['watermark_applied'] = True
        image['watermark_text'] = watermark_text
        image['watermark_position'] = self.config['watermark_position']
        
        return image
        
    async def process_pending_requests(self):
        """Process pending media requests"""
        # In production, process actual image generation queue
        pass
        
    async def clean_old_images(self):
        """Clean old images"""
        # Remove images older than 30 days
        current_time = datetime.now()
        
        to_remove = []
        for i, image in enumerate(self.generated_images):
            if 'timestamp' in image:
                try:
                    img_time = datetime.fromisoformat(image['timestamp'])
                    if (current_time - img_time).days > 30:
                        to_remove.append(i)
                except:
                    pass
                    
        # Remove in reverse order
        for i in reversed(to_remove):
            self.generated_images.pop(i)
            
    async def publish_media_update(self):
        """Publish media data update"""
        media_data = {
            'total_images': len(self.generated_images),
            'recent_images': self.generated_images[-5:],
            'image_types': self.image_types,
            'watermark': self.watermark,
            'timestamp': datetime.now().isoformat()
        }
        
        event = Event(
            event_type="media_update",
            data=media_data,
            source=self.agent_id
        )
        await self.event_bus.publish(event)
        
    async def get_status(self) -> Dict[str, Any]:
        """Get media creator status"""
        return {
            'agent_id': self.agent_id,
            'status': 'running' if self.running else 'stopped',
            'total_images': len(self.generated_images),
            'image_types': self.image_types,
            'watermark': self.watermark,
            'timestamp': datetime.now().isoformat()
        }
