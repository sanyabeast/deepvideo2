"""
TTS Provider System for DeepVideo2.

This module provides a modular approach to text-to-speech generation,
allowing multiple TTS providers to be used interchangeably.
"""

from .base_provider import BaseTTSProvider
from .provider_factory import get_tts_provider

__all__ = ['BaseTTSProvider', 'get_tts_provider']
