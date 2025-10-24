"""
Full-Duplex Telephony Module for Bidirectional Inbound Calls

This module provides bidirectional call handling for inbound calls from extensions 1000-5000.
It integrates STT (Speech-to-Text) and TTS (Text-to-Speech) to create a full-duplex dialog loop.

For calls from extensions outside the 1000-5000 range, it falls back to TTS-only mode.
"""

import os
import time
import yaml
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from loguru import logger


class TelephonyConfig:
    """Configuration loader for telephony settings"""
    
    def __init__(self, config_path: str = "config/telephony.yml"):
        """
        Initialize configuration
        
        Args:
            config_path: Path to telephony configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            # Expand environment variables in path
            config_path = os.path.expandvars(self.config_path)
            
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found: {config_path}, using defaults")
                return self._get_default_config()
                
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            # Expand environment variables in config values
            config = self._expand_env_vars(config)
            
            logger.info(f"Loaded telephony configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using defaults")
            return self._get_default_config()
            
    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in config"""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return os.path.expandvars(obj)
        return obj
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'stt': {
                'provider': 'whisper',
                'model': 'base',
                'language': 'de',
                'device': 'cuda',  # Use GPU (NVIDIA 3060 Ti) for faster transcription
                'stream': {
                    'enabled': True,
                    'chunk_duration_ms': 1000,
                    'silence_threshold': 500
                }
            },
            'tts': {
                'provider': 'coqui',
                'model': 'tts_models/de/thorsten/tacotron2-DDC',
                'language': 'de',
                'sample_rate': 8000,
                'channels': 1,
                'use_gpu': True  # Use GPU (NVIDIA 3060 Ti) for faster synthesis
            },
            'agent': {
                'model': 'gpt-4-turbo-preview',
                'max_duration': 300,
                'response_timeout': 30
            },
            'full_duplex': {
                'enabled': True,
                'min_extension': 1000,
                'max_extension': 5000,
                'fallback_mode': 'tts_only',
                'realtime_streaming': False
            },
            'logging': {
                'level': 'INFO',
                'log_transcripts': True,
                'directory': 'logs/telephony'
            }
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value


class FullDuplexHandler:
    """
    Handler for full-duplex bidirectional calls
    
    This handler manages the dialog loop:
    1. Listen for audio from caller
    2. Transcribe audio using STT
    3. Send transcription to agent
    4. Get agent response
    5. Synthesize response using TTS
    6. Play response to caller
    7. Repeat until call ends
    """
    
    def __init__(
        self,
        stt_engine,
        tts_engine,
        conversation_engine,
        ari_client,
        config: Optional[TelephonyConfig] = None
    ):
        """
        Initialize full-duplex handler
        
        Args:
            stt_engine: Speech-to-Text engine instance
            tts_engine: Text-to-Speech engine instance
            conversation_engine: AI conversation engine instance
            ari_client: Asterisk ARI client instance
            config: Telephony configuration
        """
        self.stt = stt_engine
        self.tts = tts_engine
        self.conversation_engine = conversation_engine
        self.ari_client = ari_client
        self.config = config or TelephonyConfig()
        
        # Active call tracking
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self.call_locks: Dict[str, threading.Lock] = {}
        
        # Directories
        self.sounds_dir = os.getenv('ASTERISK_SOUNDS_DIR', '/var/lib/asterisk/sounds/aiagent')
        self.recordings_dir = os.getenv('ASTERISK_RECORDINGS_DIR', '/var/spool/asterisk/recording')
        
        # Create directories
        os.makedirs(self.sounds_dir, exist_ok=True)
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        logger.info("FullDuplexHandler initialized")
        
    def is_extension_in_range(self, caller_number: str) -> bool:
        """
        Check if caller extension is in the full-duplex range
        
        Args:
            caller_number: Caller ID / extension number
            
        Returns:
            True if extension is in range 1000-5000
        """
        try:
            # Extract numeric part of caller number
            numeric_part = ''.join(filter(str.isdigit, caller_number))
            if not numeric_part:
                return False
                
            extension = int(numeric_part)
            min_ext = self.config.get('full_duplex.min_extension', 1000)
            max_ext = self.config.get('full_duplex.max_extension', 5000)
            
            in_range = min_ext <= extension <= max_ext
            logger.debug(f"Extension {extension} in range [{min_ext}, {max_ext}]: {in_range}")
            return in_range
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse extension from {caller_number}: {e}")
            return False
            
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
            import subprocess
            
            # Convert to 8000 Hz, mono, pcm_s16le WAV (Asterisk compatible)
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "wav", "-i", str(input_file),
                "-ac", "1", "-ar", "8000", "-acodec", "pcm_s16le", str(output_file)
            ], check=True)
            
            logger.debug(f"Converted audio to Asterisk format: {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to convert audio: {e}")
            return False
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg: sudo apt install ffmpeg")
            return False
            
    def speak_to_caller(
        self,
        channel_id: str,
        text: str,
        conversation_history: list
    ) -> bool:
        """
        Speak text to caller via TTS
        
        Args:
            channel_id: Asterisk channel ID
            text: Text to speak
            conversation_history: Conversation history to update
            
        Returns:
            True if successful
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
                    return True
                else:
                    logger.error("Failed to convert audio for Asterisk")
                    return False
            else:
                logger.error("Failed to synthesize speech")
                return False
                
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            return False
            
    def listen_and_transcribe(
        self,
        channel_id: str,
        recording_name: str,
        timeout: int = 10
    ) -> Optional[str]:
        """
        Listen to caller and transcribe speech
        
        Args:
            channel_id: Asterisk channel ID
            recording_name: Name for the recording
            timeout: Maximum time to wait for speech (seconds)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Record audio from caller
            # Note: In a real implementation, this would use streaming STT
            # For now, we record a chunk and then transcribe
            
            recording_path = os.path.join(self.recordings_dir, f"{recording_name}.wav")
            
            # Wait for audio to be recorded
            # In production, this should be event-driven or use streaming
            time.sleep(timeout)
            
            # Check if channel still exists before stopping recording
            channel_state = self.ari_client.get_channel_state(channel_id)
            if not channel_state:
                logger.warning(f"Channel {channel_id} no longer exists, caller may have hung up")
                return None
            
            # Stop recording (only pass recording_name, not channel_id)
            try:
                self.ari_client.stop_recording(recording_name)
            except Exception as e:
                logger.warning(f"Failed to stop recording {recording_name}: {e}")
                # Continue gracefully - the recording may have already stopped
            
            # Wait a bit for file to be written
            time.sleep(0.5)
            
            # Check if recording exists
            if not os.path.exists(recording_path):
                logger.warning(f"Recording not found: {recording_path}")
                return None
                
            # Transcribe the recording
            transcription = self.stt.transcribe_file(recording_path)
            
            if transcription:
                logger.info(f"Caller said: {transcription}")
            else:
                logger.warning("No transcription generated")
                
            return transcription
            
        except Exception as e:
            logger.error(f"Error in listen_and_transcribe: {e}")
            return None
            
    def handle_full_duplex_call(
        self,
        channel_id: str,
        caller_number: str,
        conversation_history: list
    ) -> None:
        """
        Handle a full-duplex bidirectional call
        
        Args:
            channel_id: Asterisk channel ID
            caller_number: Caller number/extension
            conversation_history: Conversation history
        """
        try:
            logger.info(f"Starting full-duplex dialog with {caller_number}")
            
            # Track this call
            if channel_id not in self.call_locks:
                self.call_locks[channel_id] = threading.Lock()
                
            # Greet the caller
            greeting = self.conversation_engine.get_response(
                conversation_history,
                "Beginne das Gespräch mit einer freundlichen Begrüßung."
            )
            
            if greeting:
                self.speak_to_caller(channel_id, greeting, conversation_history)
                
            # Dialog loop
            max_turns = 20  # Prevent infinite loops
            turn = 0
            
            while turn < max_turns:
                turn += 1
                logger.debug(f"Dialog turn {turn}/{max_turns}")
                
                # Start recording for this turn
                recording_name = f"dialog_{channel_id}_{int(time.time())}_{turn}"
                recording = self.ari_client.start_recording(channel_id, recording_name)
                
                # Check if recording started successfully
                if not recording:
                    logger.warning(f"Failed to start recording on turn {turn}")
                    # Check if channel still exists
                    channel_state = self.ari_client.get_channel_state(channel_id)
                    if not channel_state:
                        logger.info(f"Channel {channel_id} no longer exists, caller hung up during recording start")
                        break
                    # Skip this turn if recording failed but channel is still alive
                    continue
                
                # Listen and transcribe caller's speech
                user_input = self.listen_and_transcribe(channel_id, recording_name, timeout=8)
                
                if not user_input:
                    # No input detected - check if channel is still alive
                    channel_state = self.ari_client.get_channel_state(channel_id)
                    if not channel_state:
                        logger.info(f"Channel {channel_id} ended during listening, caller hung up")
                        break
                    
                    # Channel is alive but no input - ask if they're still there
                    if turn > 1:  # Give some grace on first turn
                        prompt = "Sind Sie noch da? Können Sie mich hören?"
                        self.speak_to_caller(channel_id, prompt, conversation_history)
                    continue
                    
                # Add user input to conversation history
                conversation_history.append({"role": "user", "content": user_input})
                
                # Check for conversation end signals
                end_signals = ["auf wiederhören", "tschüss", "danke das war alles", "nein danke"]
                if any(signal in user_input.lower() for signal in end_signals):
                    logger.info("Conversation end signal detected")
                    closing = "Vielen Dank für das Gespräch. Auf Wiederhören!"
                    self.speak_to_caller(channel_id, closing, conversation_history)
                    break
                    
                # Get agent response
                response = self.conversation_engine.get_response(conversation_history, user_input)
                
                if response:
                    # Speak the response
                    self.speak_to_caller(channel_id, response, conversation_history)
                else:
                    logger.warning("No response from conversation engine")
                    fallback = "Entschuldigung, ich habe das nicht verstanden. Können Sie das wiederholen?"
                    self.speak_to_caller(channel_id, fallback, conversation_history)
                    
            logger.info(f"Full-duplex dialog completed after {turn} turns")
            
        except Exception as e:
            logger.error(f"Error in full-duplex call handling: {e}")
            
    def handle_tts_only_call(
        self,
        channel_id: str,
        caller_number: str,
        conversation_history: list
    ) -> None:
        """
        Handle a TTS-only call (fallback mode)
        
        Args:
            channel_id: Asterisk channel ID
            caller_number: Caller number/extension
            conversation_history: Conversation history
        """
        try:
            logger.info(f"Starting TTS-only mode for {caller_number}")
            
            # Greet the caller
            greeting = self.conversation_engine.get_response(
                conversation_history,
                "Beginne das Gespräch mit einer freundlichen Begrüßung."
            )
            
            if greeting:
                self.speak_to_caller(channel_id, greeting, conversation_history)
                
            # Simulated conversation flow (TTS-only mode)
            time.sleep(3)
            
            # Sample question
            question = "Können Sie mir mehr über Ihre Dienstleistungen erzählen?"
            logger.info(f"[Simulated customer]: {question}")
            conversation_history.append({"role": "user", "content": question})
            
            response = self.conversation_engine.get_response(conversation_history, question)
            if response:
                self.speak_to_caller(channel_id, response, conversation_history)
                
            time.sleep(3)
            
            # Closing
            closing = "Vielen Dank für Ihren Anruf. Auf Wiederhören!"
            self.speak_to_caller(channel_id, closing, conversation_history)
            
            logger.info("TTS-only call completed")
            
        except Exception as e:
            logger.error(f"Error in TTS-only call handling: {e}")
            
    def route_call(
        self,
        channel_id: str,
        caller_number: str,
        conversation_history: list
    ) -> None:
        """
        Route call based on caller extension
        
        Args:
            channel_id: Asterisk channel ID
            caller_number: Caller number/extension
            conversation_history: Conversation history
        """
        if self.config.get('full_duplex.enabled', True):
            if self.is_extension_in_range(caller_number):
                logger.info(f"Routing to full-duplex mode for extension {caller_number}")
                self.handle_full_duplex_call(channel_id, caller_number, conversation_history)
            else:
                logger.info(f"Routing to TTS-only mode for extension {caller_number}")
                self.handle_tts_only_call(channel_id, caller_number, conversation_history)
        else:
            logger.info("Full-duplex mode disabled, using TTS-only")
            self.handle_tts_only_call(channel_id, caller_number, conversation_history)


# Export main classes
__all__ = ['TelephonyConfig', 'FullDuplexHandler']
