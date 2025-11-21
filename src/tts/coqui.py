"""
Text-to-Speech using Coqui TTS
"""
from TTS.api import TTS
from loguru import logger
import os
from typing import Optional


class TextToSpeech:
    """Text-to-Speech processor using Coqui TTS"""
    
    def __init__(self, model_name: str = "tts_models/de/thorsten/tacotron2-DDC", language: str = "de", use_gpu: bool = False):
        """
        Initialize Coqui TTS model
        
        Args:
            model_name: TTS model name
            language: Language code
            use_gpu: Whether to use GPU acceleration
        """
        self.model_name = model_name
        self.language = language
        self.use_gpu = use_gpu
        self.tts = None
        
    def load_model(self):
        """Load TTS model"""
        try:
            logger.info(f"Loading Coqui TTS model: {self.model_name} (GPU: {self.use_gpu})")
            self.tts = TTS(model_name=self.model_name, progress_bar=False, gpu=self.use_gpu)
            logger.info("Coqui TTS model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}")
            raise
            
    def synthesize(self, text: str, output_file_path: str) -> bool:
        """
        Convert text to speech and save to file
        
        Args:
            text: Text to convert
            output_file_path: Path to save audio file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.tts:
            logger.error("Model not loaded. Call load_model() first")
            return False
            
        try:
            logger.info(f"Synthesizing speech: {text[:50]}...")
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # Synthesize speech
            self.tts.tts_to_file(text=text, file_path=output_file_path)
            
            logger.info(f"Speech synthesized and saved to: {output_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {e}")
            return False
            
    def synthesize_to_bytes(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech and return as bytes
        
        Args:
            text: Text to convert
            
        Returns:
            Audio data as bytes or None if failed
        """
        if not self.tts:
            logger.error("Model not loaded. Call load_model() first")
            return None
            
        try:
            import tempfile
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
            # Synthesize to file
            if self.synthesize(text, tmp_path):
                # Read file as bytes
                with open(tmp_path, 'rb') as f:
                    audio_bytes = f.read()
                    
                # Clean up temporary file
                os.remove(tmp_path)
                
                return audio_bytes
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to synthesize speech to bytes: {e}")
            return None
            
    def get_available_models(self) -> list:
        """Get list of available TTS models"""
        try:
            return TTS.list_models()
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
