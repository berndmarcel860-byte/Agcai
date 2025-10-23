"""
Speech-to-Text using Faster Whisper
"""
from faster_whisper import WhisperModel
from loguru import logger
import os
from typing import Optional, List, Tuple


class SpeechToText:
    """Speech-to-Text processor using Faster Whisper"""
    
    def __init__(self, model_size: str = "base", language: str = "de", device: str = "cpu"):
        """
        Initialize Faster Whisper model
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code (de, en, etc.)
            device: Device to use (cpu, cuda)
        """
        self.model_size = model_size
        self.language = language
        self.device = device
        self.model = None
        
    def load_model(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Faster Whisper model: {self.model_size}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16"
            )
            logger.info("Faster Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
            
    def transcribe_file(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.model:
            logger.error("Model not loaded. Call load_model() first")
            return None
            
        try:
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
                
            logger.info(f"Transcribing audio file: {audio_file_path}")
            
            segments, info = self.model.transcribe(
                audio_file_path,
                language=self.language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Combine all segments
            transcription = " ".join([segment.text for segment in segments])
            
            logger.info(f"Transcription completed: {transcription[:100]}...")
            return transcription.strip()
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
            return None
            
    def transcribe_with_timestamps(self, audio_file_path: str) -> Optional[List[Tuple[float, float, str]]]:
        """
        Transcribe audio file with timestamps
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            List of (start_time, end_time, text) tuples or None if failed
        """
        if not self.model:
            logger.error("Model not loaded. Call load_model() first")
            return None
            
        try:
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
                
            logger.info(f"Transcribing audio file with timestamps: {audio_file_path}")
            
            segments, info = self.model.transcribe(
                audio_file_path,
                language=self.language,
                beam_size=5,
                vad_filter=True
            )
            
            # Create list of timestamped segments
            result = [(segment.start, segment.end, segment.text) for segment in segments]
            
            logger.info(f"Transcription with timestamps completed: {len(result)} segments")
            return result
            
        except Exception as e:
            logger.error(f"Failed to transcribe audio with timestamps: {e}")
            return None
            
    def detect_language(self, audio_file_path: str) -> Optional[str]:
        """
        Detect language of audio file
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Language code or None if failed
        """
        if not self.model:
            logger.error("Model not loaded. Call load_model() first")
            return None
            
        try:
            if not os.path.exists(audio_file_path):
                logger.error(f"Audio file not found: {audio_file_path}")
                return None
                
            segments, info = self.model.transcribe(audio_file_path, beam_size=5)
            
            detected_language = info.language
            logger.info(f"Detected language: {detected_language}")
            return detected_language
            
        except Exception as e:
            logger.error(f"Failed to detect language: {e}")
            return None
