"""
Orpheus TTS Provider for DeepVideo2.

This module implements the TTS provider interface for the Orpheus TTS server.
"""

import requests
import json
import os
from .base_provider import BaseTTSProvider


class OrpheusTTSProvider(BaseTTSProvider):
    """TTS provider that uses the Orpheus TTS server."""
    
    def __init__(self, config):
        """Initialize the Orpheus TTS provider.
        
        Args:
            config: Dictionary containing provider-specific configuration
        """
        super().__init__(config)
        self.tts_server = config.get('tts_server', 'http://localhost:5005/v1/audio/speech')
        self.voice_presets = config.get('voice_presets', ['jess'])
        self.default_voice = self.voice_presets[0] if self.voice_presets else 'jess'
        self.speed = config.get('speed', 0.5)
        self.model = config.get('model', 'orpheus')
        
    def generate_voice_line(self, text, output_path, emotion=None, voice_sample=None):
        """Generate a voice line using Orpheus TTS server.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the generated audio file
            emotion: Emotion to apply to the voice (not directly supported by Orpheus)
            voice_sample: Voice to use (if None, uses default_voice from config)
            
        Returns:
            bool: True if generation was successful, False otherwise
        """
        # Preprocess text for better TTS compatibility
        processed_text = self.preprocess_text(text)
        
        # Use provided voice or fall back to default
        voice = voice_sample if voice_sample else self.default_voice
        
        # Prepare request payload
        payload = {
            'model': self.model,
            'input': processed_text,
            'voice': voice,
            'response_format': 'wav',
            'speed': self.speed
        }
        
        # Add emotion-based speed adjustment if emotion is provided
        if emotion:
            # Adjust speed based on emotion (simple heuristic)
            emotion_speed_map = {
                'happiness': 0.55,  # Slightly faster for happy
                'sadness': 0.45,    # Slower for sad
                'disgust': 0.5,     # Normal for disgust
                'fear': 0.6,        # Faster for fear
                'surprise': 0.6,    # Faster for surprise
                'anger': 0.55,      # Slightly faster for anger
                'neutral': 0.5      # Normal for neutral
            }
            # Use emotion-based speed or default if emotion not in map
            payload['speed'] = emotion_speed_map.get(emotion.lower(), self.speed)
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.tts_server, 
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                # Save the audio content to the output file
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"⚠️ Error generating voice line with Orpheus: {response.text}")
                return False
        except Exception as e:
            print(f"⚠️ Exception when calling Orpheus TTS API: {str(e)}")
            return False
