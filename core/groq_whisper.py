"""Groq Whisper API integration for fast transcription"""

import os
import logging
from pathlib import Path
from groq import Groq
from pydub import AudioSegment

logger = logging.getLogger(__name__)


class GroqWhisperProcessor:
    """Process audio transcription using Groq's Whisper API"""
    
    # Groq limits
    MAX_FILE_SIZE = 19.5 * 1024 * 1024  # 19.5 MB in bytes
    MAX_CHUNK_DURATION = 50 * 60 * 1000  # 50 minutes in milliseconds
    
    def __init__(self, api_key: str = None):
        """
        Initialize Groq Whisper processor
        
        Args:
            api_key: Groq API key (or set GROQ_API_KEY environment variable)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Groq API key not found. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.client = Groq(api_key=self.api_key)
        logger.info("✅ Groq Whisper API initialized")
    
    def get_file_size(self, file_path: str) -> float:
        """Get file size in MB"""
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    
    def split_audio(self, audio_path: str, output_dir: str = None) -> list:
        """
        Split audio file into chunks under 19.5MB
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save chunks (default: same as audio)
            
        Returns:
            List of chunk file paths
        """
        logger.info(f"Splitting audio file: {audio_path}")
        
        # Load audio
        audio = AudioSegment.from_file(audio_path)
        duration_ms = len(audio)
        
        # Calculate chunk duration
        file_size = self.get_file_size(audio_path)
        
        if file_size <= 19.5:
            logger.info(f"File size {file_size:.2f}MB is within limit, no splitting needed")
            return [audio_path]
        
        # Calculate number of chunks needed
        num_chunks = int(file_size / 19) + 1
        chunk_duration = duration_ms // num_chunks
        
        logger.info(f"File size: {file_size:.2f}MB, splitting into {num_chunks} chunks")
        
        # Setup output directory
        if output_dir is None:
            output_dir = Path(audio_path).parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Split audio
        chunks = []
        base_name = Path(audio_path).stem
        
        for i in range(num_chunks):
            start_ms = i * chunk_duration
            end_ms = min((i + 1) * chunk_duration, duration_ms)
            
            chunk = audio[start_ms:end_ms]
            chunk_path = output_dir / f"{base_name}_chunk_{i+1}.ogg"
            
            chunk.export(
                str(chunk_path),
                format="ogg",
                codec="libopus",
                parameters=["-b:a", "32k", "-ac", "1"]
            )
            
            chunks.append(str(chunk_path))
            chunk_size = self.get_file_size(str(chunk_path))
            logger.info(f"  Created chunk {i+1}/{num_chunks}: {chunk_size:.2f}MB")
        
        return chunks
    
    def transcribe_audio(self, audio_path: str, language: str = None) -> dict:
        """
        Transcribe audio using Groq Whisper API
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
            
        Returns:
            Dictionary with transcription results
        """
        logger.info(f"Transcribing with Groq: {audio_path}")
        
        file_size = self.get_file_size(audio_path)
        logger.info(f"File size: {file_size:.2f}MB")
        
        # Check if file needs splitting
        if file_size > 19.5:
            logger.warning(f"File too large ({file_size:.2f}MB), splitting into chunks")
            return self.transcribe_large_audio(audio_path, language)
        
        try:
            with open(audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(Path(audio_path).name, file.read()),
                    model="whisper-large-v3-turbo",  # Faster model
                    temperature=0,
                    response_format="verbose_json",
                    language=language
                )
            
            logger.info(f"✅ Transcription complete: {len(transcription.text)} characters")
            
            return {
                'text': transcription.text,
                'language': getattr(transcription, 'language', language or 'unknown'),
                'segments': getattr(transcription, 'segments', []),
                'duration': getattr(transcription, 'duration', None)
            }
        
        except Exception as e:
            logger.error(f"Groq transcription error: {e}")
            raise
    
    def transcribe_large_audio(self, audio_path: str, language: str = None) -> dict:
        """
        Transcribe large audio file by splitting into chunks
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
            
        Returns:
            Combined transcription results
        """
        logger.info("Transcribing large audio file in chunks")
        
        # Split audio
        chunks = self.split_audio(audio_path)
        
        # Transcribe each chunk
        full_text = ""
        all_segments = []
        time_offset = 0
        
        for i, chunk_path in enumerate(chunks):
            logger.info(f"Transcribing chunk {i+1}/{len(chunks)}")
            
            result = self.transcribe_audio(chunk_path, language)
            
            # Append text
            full_text += result['text'] + " "
            
            # Adjust segment timestamps and append
            for segment in result.get('segments', []):
                segment['start'] += time_offset
                segment['end'] += time_offset
                all_segments.append(segment)
            
            # Update time offset
            if result.get('duration'):
                time_offset += result['duration']
            
            # Clean up chunk file
            try:
                os.remove(chunk_path)
                logger.info(f"Cleaned up chunk: {chunk_path}")
            except:
                pass
        
        return {
            'text': full_text.strip(),
            'language': language or 'unknown',
            'segments': all_segments
        }
    
    def process_video_audio(self, audio_path: str, language: str = None) -> dict:
        """
        Main entry point for processing video audio
        
        Args:
            audio_path: Path to extracted audio file
            language: Language code (optional)
            
        Returns:
            Transcription results
        """
        return self.transcribe_audio(audio_path, language)