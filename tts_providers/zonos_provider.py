"""
Zonos TTS Provider for DeepVideo2.

This module implements the TTS provider interface for the Zonos TTS server.
"""

import requests
from pathlib import Path
from .base_provider import BaseTTSProvider


class ZonosTTSProvider(BaseTTSProvider):
    """TTS provider that uses the Zonos TTS server."""
    
    def __init__(self, config):
        """Initialize the Zonos TTS provider.
        
        Args:
            config: Dictionary containing provider-specific configuration
        """
        super().__init__(config)
        self.tts_server = config.get('tts_server', 'http://localhost:5001/generate')
        self.speech_rate = config.get('speech_rate', '15')
        self.voice_samples = config.get('voice_samples', [])
    
    def normalize_path(self, path):
        """Normalize path to use forward slashes consistently."""
        return str(Path(path)).replace('\\', '/')
    
    def generate_voice_line(self, text, output_path, emotion="neutral", voice_sample=None):
        """Generate a voice line using Zonos TTS server.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the generated audio file
            emotion: Emotion to apply to the voice (default: neutral)
            voice_sample: Path to a voice sample file
            
        Returns:
            bool: True if generation was successful, False otherwise
        """
        # Normalize the output path to use forward slashes
        normalized_output_path = self.normalize_path(output_path)
        
        # Preprocess text for better TTS compatibility
        processed_text = self.preprocess_text(text)
        
        params = {
            'text': processed_text,
            'path': normalized_output_path,
            'voice': voice_sample,
            'emotion': emotion.capitalize(),  # Capitalize emotion for the API
            'rate': self.speech_rate
        }
        
        try:
            response = requests.get(self.tts_server, params=params)
            if response.status_code == 200:
                return True
            else:
                print(f"⚠️ Error generating voice line: {response.text}")
                return False
        except Exception as e:
            print(f"⚠️ Exception when calling Zonos TTS API: {str(e)}")
            return False
