"""
Base TTS Provider Interface for DeepVideo2.

This module defines the base interface that all TTS providers must implement.
"""

from abc import ABC, abstractmethod
import re


class BaseTTSProvider(ABC):
    """Base class for all TTS providers."""
    
    def __init__(self, config):
        """Initialize the TTS provider with configuration.
        
        Args:
            config: Dictionary containing provider-specific configuration
        """
        self.config = config
    
    @abstractmethod
    def generate_voice_line(self, text, output_path, emotion=None, voice_sample=None):
        """Generate a voice line from text and save it to the specified path.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the generated audio file
            emotion: Emotion to apply to the voice (if supported)
            voice_sample: Path to a voice sample file (if supported)
            
        Returns:
            bool: True if generation was successful, False otherwise
        """
        pass
    
    def preprocess_text(self, text):
        """Preprocess text to make it more compatible with TTS.
        
        Args:
            text: The original text to preprocess
            
        Returns:
            Preprocessed text with problematic characters removed/replaced
        """
        if not text:
            return text
        
        # 1. Remove all double quotes
        text = text.replace('"', "")
        
        # 2. Replace three-dots (ellipsis) with a single dot
        text = text.replace("...", ".").replace(". . .", ".")
        
        # 3. Remove the word "ugh" (case insensitive)
        text = re.sub(r'\bugh\b', '', text, flags=re.IGNORECASE)
        
        # Remove any double spaces created by the replacements
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
