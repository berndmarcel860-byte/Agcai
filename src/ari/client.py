"""
Asterisk ARI client implementation
"""
import requests
import asyncio
import websocket
import json
from typing import Optional, Callable, Dict, Any
from loguru import logger
from threading import Thread


class ARIClient:
    """Asterisk REST Interface client"""
    
    def __init__(self, host: str, port: int, username: str, password: str, app_name: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.app_name = app_name
        self.base_url = f"http://{host}:{port}/ari"
        self.ws = None
        self.ws_thread = None
        self.running = False
        self.event_handlers: Dict[str, Callable] = {}
        
    def connect(self):
        """Connect to ARI WebSocket"""
        try:
            ws_url = f"ws://{self.host}:{self.port}/ari/events?app={self.app_name}&api_key={self.username}:{self.password}"
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            self.running = True
            self.ws_thread = Thread(target=self.ws.run_forever, daemon=True)
            self.ws_thread.start()
            
            logger.info(f"Connected to ARI WebSocket at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to ARI: {e}")
            raise
            
    def disconnect(self):
        """Disconnect from ARI WebSocket"""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("Disconnected from ARI")
        
    def _on_open(self, ws):
        """WebSocket connection opened"""
        logger.info("ARI WebSocket connection opened")
        
    def _on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            event = json.loads(message)
            event_type = event.get('type')
            
            logger.debug(f"Received ARI event: {event_type}")
            
            # Call registered event handlers
            if event_type in self.event_handlers:
                self.event_handlers[event_type](event)
            elif 'default' in self.event_handlers:
                self.event_handlers['default'](event)
                
        except Exception as e:
            logger.error(f"Error processing ARI message: {e}")
            
    def _on_error(self, ws, error):
        """Handle WebSocket error"""
        logger.error(f"ARI WebSocket error: {error}")
        
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"ARI WebSocket closed: {close_status_code} - {close_msg}")
        
    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered handler for event: {event_type}")
        
    def originate_call(self, endpoint: str, caller_id: str, context: str = "default", 
                      extension: str = "s", priority: int = 1, timeout: int = 30) -> Optional[Dict]:
        """Originate an outbound call"""
        try:
            url = f"{self.base_url}/channels"
            
            params = {
                'endpoint': endpoint,
                'app': self.app_name,
                'callerId': caller_id,
                'timeout': timeout
            }
            
            response = requests.post(
                url,
                params=params,
                auth=(self.username, self.password)
            )
            
            if response.status_code in [200, 201]:
                channel = response.json()
                logger.info(f"Originated call to {endpoint}, channel: {channel.get('id')}")
                return channel
            else:
                logger.error(f"Failed to originate call: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error originating call: {e}")
            return None
            
    def answer_channel(self, channel_id: str) -> bool:
        """Answer a channel"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/answer"
            response = requests.post(url, auth=(self.username, self.password))
            
            if response.status_code == 204:
                logger.info(f"Answered channel: {channel_id}")
                return True
            else:
                logger.error(f"Failed to answer channel: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error answering channel: {e}")
            return False
            
    def hangup_channel(self, channel_id: str) -> bool:
        """Hangup a channel"""
        try:
            url = f"{self.base_url}/channels/{channel_id}"
            response = requests.delete(url, auth=(self.username, self.password))
            
            if response.status_code == 204:
                logger.info(f"Hung up channel: {channel_id}")
                return True
            else:
                logger.error(f"Failed to hangup channel: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error hanging up channel: {e}")
            return False
            
    def play_media(self, channel_id: str, media_uri: str) -> Optional[Dict]:
        """Play media on a channel"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/play"
            params = {'media': media_uri}
            
            response = requests.post(
                url,
                params=params,
                auth=(self.username, self.password)
            )
            
            if response.status_code in [200, 201]:
                playback = response.json()
                logger.info(f"Playing media on channel {channel_id}: {media_uri}")
                return playback
            else:
                logger.error(f"Failed to play media: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error playing media: {e}")
            return None
            
    def start_recording(self, channel_id: str, name: str, format: str = "wav") -> Optional[Dict]:
        """Start recording a channel"""
        try:
            url = f"{self.base_url}/channels/{channel_id}/record"
            params = {
                'name': name,
                'format': format,
                'maxDurationSeconds': 300,
                'maxSilenceSeconds': 5,
                'ifExists': 'overwrite',
                'beep': False
            }
            
            response = requests.post(
                url,
                params=params,
                auth=(self.username, self.password)
            )
            
            if response.status_code in [200, 201]:
                recording = response.json()
                logger.info(f"Started recording on channel {channel_id}")
                return recording
            else:
                logger.error(f"Failed to start recording: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return None
            
    def stop_recording(self, recording_name: str) -> bool:
        """Stop a recording"""
        try:
            url = f"{self.base_url}/recordings/live/{recording_name}/stop"
            response = requests.post(url, auth=(self.username, self.password))
            
            if response.status_code == 204:
                logger.info(f"Stopped recording: {recording_name}")
                return True
            else:
                logger.error(f"Failed to stop recording: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False
            
    def get_channel_state(self, channel_id: str) -> Optional[Dict]:
        """Get channel state"""
        try:
            url = f"{self.base_url}/channels/{channel_id}"
            response = requests.get(url, auth=(self.username, self.password))
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting channel state: {e}")
            return None
