"""
Utility functions for audio processing
"""
import os
from pydub import AudioSegment
from loguru import logger


def convert_audio_format(input_file: str, output_file: str, 
                        sample_rate: int = 8000, channels: int = 1) -> bool:
    """
    Convert audio file to different format
    
    Args:
        input_file: Input audio file path
        output_file: Output audio file path
        sample_rate: Target sample rate
        channels: Number of channels
        
    Returns:
        True if successful
    """
    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_frame_rate(sample_rate)
        audio = audio.set_channels(channels)
        audio.export(output_file, format=output_file.split('.')[-1])
        
        logger.info(f"Converted audio: {input_file} -> {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        return False


def get_audio_duration(file_path: str) -> float:
    """Get audio file duration in seconds"""
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000.0
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        return 0.0


def merge_audio_files(file_list: list, output_file: str) -> bool:
    """Merge multiple audio files"""
    try:
        combined = AudioSegment.empty()
        
        for file_path in file_list:
            audio = AudioSegment.from_file(file_path)
            combined += audio
            
        combined.export(output_file, format=output_file.split('.')[-1])
        
        logger.info(f"Merged {len(file_list)} audio files")
        return True
        
    except Exception as e:
        logger.error(f"Error merging audio files: {e}")
        return False
