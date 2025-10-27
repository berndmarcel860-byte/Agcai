"""
Configuration management for the AI call agent
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from loguru import logger


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class ARIConfig:
    """Asterisk ARI configuration"""
    host: str
    port: int
    user: str
    password: str
    app: str
    
    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class OpenAIConfig:
    """OpenAI configuration"""
    api_key: str
    model: str = "gpt-4-turbo-preview"
    http_proxy: str = None
    https_proxy: str = None


@dataclass
class TTSConfig:
    """Text-to-Speech configuration"""
    model: str
    language: str
    use_gpu: bool = False


@dataclass
class STTConfig:
    """Speech-to-Text configuration"""
    model: str
    language: str
    device: str = "cpu"


@dataclass
class CampaignConfig:
    """Campaign configuration"""
    name: str
    caller_id: str
    max_concurrent_calls: int
    call_timeout: int


@dataclass
class AudioConfig:
    """Audio processing configuration"""
    sample_rate: int
    channels: int


class Config:
    """Main configuration class"""
    
    def __init__(self, env_file: str = ".env"):
        load_dotenv(env_file)
        
        # Database configuration
        self.database = DatabaseConfig(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "aiagent"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "ai_calls")
        )
        
        # ARI configuration
        self.ari = ARIConfig(
            host=os.getenv("ARI_HOST", "127.0.0.1"),
            port=int(os.getenv("ARI_PORT", "8088")),
            user=os.getenv("ARI_USER", "ai_agent"),
            password=os.getenv("ARI_PASS", ""),
            app=os.getenv("ARI_APP", "aiagent")
        )
        
        # OpenAI configuration
        self.openai = OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            http_proxy=os.getenv("OPENAI_HTTP_PROXY"),
            https_proxy=os.getenv("OPENAI_HTTPS_PROXY")
        )
        
        # TTS configuration
        self.tts = TTSConfig(
            model=os.getenv("TTS_MODEL", "tts_models/de/thorsten/tacotron2-DDC"),
            language=os.getenv("TTS_LANGUAGE", "de"),
            use_gpu=os.getenv("TTS_USE_GPU", "true").lower() == "true"
        )
        
        # STT configuration
        self.stt = STTConfig(
            model=os.getenv("WHISPER_MODEL", "base"),
            language=os.getenv("WHISPER_LANGUAGE", "de"),
            device=os.getenv("WHISPER_DEVICE", "cuda")
        )
        
        # Campaign configuration
        self.campaign = CampaignConfig(
            name=os.getenv("CAMPAIGN_NAME", "Fund Recovery Lead Generation"),
            caller_id=os.getenv("OUTBOUND_CALLER_ID", ""),
            max_concurrent_calls=int(os.getenv("MAX_CONCURRENT_CALLS", "5")),
            call_timeout=int(os.getenv("CALL_TIMEOUT", "300"))
        )
        
        # Audio configuration
        self.audio = AudioConfig(
            sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "8000")),
            channels=int(os.getenv("AUDIO_CHANNELS", "1"))
        )
        
        self._validate()
        
    def _validate(self):
        """Validate configuration"""
        if not self.database.password:
            logger.warning("Database password not set")
        if not self.ari.password:
            logger.warning("ARI password not set")
        if not self.openai.api_key:
            logger.warning("OpenAI API key not set")
        if not self.campaign.caller_id:
            logger.warning("Outbound caller ID not set")
            
        logger.info("Configuration loaded successfully")
