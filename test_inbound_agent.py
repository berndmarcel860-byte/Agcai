#!/usr/bin/env python3
"""
Manual Test Script for AI Call Agent

This script allows you to test the AI agent by calling extension 5000 from extension 1000.
It handles inbound calls through ARI's Stasis application for interactive testing.

For calls from extensions 1000-5000, the agent now operates in full-duplex mode,
allowing bidirectional conversation where the caller can speak and the agent responds.
For other extensions, it falls back to TTS-only mode.

Usage:
    python test_inbound_agent.py

Then dial 5000 from extension 1000 to test the agent.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from ari import ARIClient
from ai import ConversationEngine
from tts import TextToSpeech
from stt import SpeechToText
from utils import setup_logging
from telephony import TelephonyConfig, FullDuplexHandler

from loguru import logger


class InboundTestAgent:
    """Test agent for handling inbound calls to extension 5000 with full-duplex support"""
    
    def __init__(self):
        """Initialize the test agent"""
        self.config = Config()
        setup_logging(log_level="INFO", log_file="logs/test_agent.log")
        
        # Set up audio directories from config or defaults
        self.sounds_dir = os.getenv('ASTERISK_SOUNDS_DIR', '/var/lib/asterisk/sounds/aiagent')
        self.recordings_dir = os.getenv('ASTERISK_RECORDINGS_DIR', '/var/spool/asterisk/recording')
        
        # Create directories
        os.makedirs(self.sounds_dir, exist_ok=True)
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        logger.info(f"Using sounds directory: {self.sounds_dir}")
        logger.info(f"Using recordings directory: {self.recordings_dir}")
        
        # Initialize components
        self.ari_client = None
        self.conversation_engine = None
        self.tts = None
        self.stt = None
        
        # Initialize telephony configuration and full-duplex handler
        self.telephony_config = None
        self.full_duplex_handler = None
        
        # Track active calls
        self.active_calls = {}
        
        # Running flag
        self.running = False
        
    def initialize(self):
        """Initialize all components"""
        logger.info("Initializing test agent components...")
        
        try:
            # Initialize ARI client
            logger.info("Connecting to Asterisk ARI...")
            self.ari_client = ARIClient(
                host=self.config.ari.host,
                port=self.config.ari.port,
                username=self.config.ari.user,
                password=self.config.ari.password,
                app_name=self.config.ari.app
            )
            self.ari_client.connect()
            
            # Initialize AI conversation engine
            logger.info("Initializing AI conversation engine...")
            self.conversation_engine = ConversationEngine(
                api_key=self.config.openai.api_key,
                model=self.config.openai.model,
                http_proxy=self.config.openai.http_proxy,
                https_proxy=self.config.openai.https_proxy
            )
            
            # Initialize TTS
            logger.info("Loading TTS model (this may take a few minutes on first run)...")
            self.tts = TextToSpeech(
                model_name=self.config.tts.model,
                language=self.config.tts.language,
                use_gpu=self.config.tts.use_gpu
            )
            self.tts.load_model()
            
            # Initialize STT
            logger.info("Loading STT model (this may take a few minutes on first run)...")
            self.stt = SpeechToText(
                model_size=self.config.stt.model,
                language=self.config.stt.language,
                device=self.config.stt.device
            )
            self.stt.load_model()
            
            # Initialize telephony configuration
            logger.info("Loading telephony configuration...")
            self.telephony_config = TelephonyConfig()
            
            # Initialize full-duplex handler
            logger.info("Initializing full-duplex handler...")
            self.full_duplex_handler = FullDuplexHandler(
                stt_engine=self.stt,
                tts_engine=self.tts,
                conversation_engine=self.conversation_engine,
                ari_client=self.ari_client,
                config=self.telephony_config
            )
            
            logger.info("✅ All components initialized successfully!")
            logger.info("📞 Agent ready to receive calls on extension 5000")
            logger.info("🔄 Full-duplex mode enabled for extensions 1000-5000")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise
            
    def convert_audio_for_asterisk(self, input_file: str, output_file: str) -> bool:
        """
        Convert audio file to Asterisk-compatible WAV format
        
        Args:
            input_file: Input audio file path
            output_file: Output WAV file path
            
        Returns:
            True if successful
        """
        try:
            # Convert to 8000 Hz, mono, pcm_s16le WAV (Asterisk compatible)
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "wav", "-i", str(input_file),
                "-ac", "1", "-ar", "8000", "-acodec", "pcm_s16le", str(output_file)
            ], check=True)
            
            logger.info(f"Converted audio to Asterisk format: {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to convert audio: {e}")
            return False
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg: sudo apt install ffmpeg")
            return False
            
    def speak(self, channel_id: str, text: str, conversation_history: list):
        """
        Speak text via TTS and play to caller
        
        Args:
            channel_id: Asterisk channel ID
            text: Text to speak
            conversation_history: Conversation history to update
        """
        try:
            logger.info(f"Agent says: {text}")
            
            # Generate unique filename
            timestamp = int(time.time() * 1000)
            temp_file = f"/tmp/tts_{timestamp}.wav"
            
            # Generate filename for Asterisk sounds directory
            filename = f"tts_{timestamp}"
            asterisk_wav = os.path.join(self.sounds_dir, f"{filename}.wav")
            
            # Synthesize speech
            if self.tts.synthesize(text, temp_file):
                # Convert to Asterisk-compatible format
                if self.convert_audio_for_asterisk(temp_file, asterisk_wav):
                    # Play audio via ARI (without extension, Asterisk adds it)
                    media_uri = f"sound:aiagent/{filename}"
                    self.ari_client.play_media(channel_id, media_uri)
                    
                    # Add to conversation history
                    conversation_history.append({"role": "assistant", "content": text})
                    
                    # Clean up temp file
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    
                    # Wait for playback to complete (estimate based on text length)
                    time.sleep(max(2, len(text) / 15))  # Rough estimate: 15 chars per second
                else:
                    logger.error("Failed to convert audio for Asterisk")
            else:
                logger.error("Failed to synthesize speech")
                
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            
    def handle_stasis_start(self, event):
        """Handle incoming call to Stasis application"""
        try:
            channel = event.get('channel', {})
            channel_id = channel.get('id')
            caller_number = channel.get('caller', {}).get('number', 'Unknown')
            
            logger.info(f"📞 Incoming call from {caller_number} on channel {channel_id}")
            
            # Answer the call
            self.ari_client.answer_channel(channel_id)
            logger.info(f"✅ Call answered on channel {channel_id}")
            
            # Initialize conversation for this call
            conversation_history = self.conversation_engine.start_conversation()
            self.active_calls[channel_id] = {
                'conversation_history': conversation_history,
                'caller': caller_number,
                'start_time': datetime.now()
            }
            
            # Start recording
            recording_name = f"test_{channel_id}_{int(time.time())}"
            self.ari_client.start_recording(channel_id, recording_name)
            logger.info(f"🎙️ Recording started: {recording_name}")
            
            # Route call through full-duplex handler
            # This will automatically handle full-duplex mode for extensions 1000-5000
            # and fall back to TTS-only mode for other extensions
            self.full_duplex_handler.route_call(
                channel_id,
                caller_number,
                conversation_history
            )
            
            # End the call
            logger.info("📴 Ending test call")
            self.ari_client.hangup_channel(channel_id)
            
        except Exception as e:
            logger.error(f"Error handling call: {e}")
            if channel_id:
                self.ari_client.hangup_channel(channel_id)
                
    def handle_channel_destroyed(self, event):
        """Handle call hangup"""
        channel = event.get('channel', {})
        channel_id = channel.get('id')
        
        if channel_id in self.active_calls:
            call_info = self.active_calls[channel_id]
            duration = (datetime.now() - call_info['start_time']).seconds
            
            logger.info(f"📴 Call ended from {call_info['caller']}, duration: {duration}s")
            
            # Extract appointment info if any
            try:
                appointment_info = self.conversation_engine.extract_appointment_info(
                    call_info['conversation_history']
                )
                if appointment_info:
                    logger.info(f"📅 Appointment info extracted: {appointment_info}")
            except Exception as e:
                logger.error(f"Error extracting appointment info: {e}")
                
            del self.active_calls[channel_id]
            
    def handle_stasis_end(self, event):
        """Handle when channel leaves Stasis application"""
        channel = event.get('channel', {})
        channel_id = channel.get('id')
        
        logger.info(f"Channel {channel_id} left Stasis application")
        
    def register_handlers(self):
        """Register ARI event handlers"""
        self.ari_client.on('StasisStart', self.handle_stasis_start)
        self.ari_client.on('ChannelDestroyed', self.handle_channel_destroyed)
        self.ari_client.on('StasisEnd', self.handle_stasis_end)
        
        logger.info("Event handlers registered")
        
    def run(self):
        """Run the test agent"""
        self.running = True
        
        logger.info("=" * 60)
        logger.info("🤖 AI Call Agent Test Mode - Full-Duplex Enabled")
        logger.info("=" * 60)
        logger.info("")
        logger.info("📞 Call extension 5000 from extension 1000-5000 for full-duplex mode")
        logger.info("   (Real bidirectional conversation with STT/TTS)")
        logger.info("")
        logger.info("📞 Call from other extensions will use TTS-only mode")
        logger.info("")
        logger.info("Configuration:")
        logger.info(f"  - ARI App: {self.config.ari.app}")
        logger.info(f"  - ARI Host: {self.config.ari.host}:{self.config.ari.port}")
        logger.info(f"  - Sounds Dir: {self.sounds_dir}")
        logger.info(f"  - Recordings Dir: {self.recordings_dir}")
        logger.info(f"  - Full-Duplex Range: 1000-5000")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopping test agent...")
            
    def shutdown(self):
        """Shutdown the agent"""
        logger.info("Shutting down...")
        self.running = False
        
        # Hangup any active calls
        for channel_id in list(self.active_calls.keys()):
            try:
                self.ari_client.hangup_channel(channel_id)
            except:
                pass
                
        # Disconnect ARI
        if self.ari_client:
            self.ari_client.disconnect()
            
        logger.info("Shutdown complete")


def main():
    """Main entry point"""
    agent = None
    
    def signal_handler(signum, frame):
        """Handle shutdown signals"""
        if agent:
            agent.shutdown()
        sys.exit(0)
        
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and initialize agent
        agent = InboundTestAgent()
        agent.initialize()
        
        # Register event handlers
        agent.register_handlers()
        
        # Run agent
        agent.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if agent:
            agent.shutdown()
        sys.exit(1)


if __name__ == '__main__':
    main()
