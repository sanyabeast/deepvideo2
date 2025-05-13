"""
TTS Provider Factory for DeepVideo2.

This module provides a factory function to create the appropriate TTS provider
based on the configuration.
"""

from .zonos_provider import ZonosTTSProvider
from .orpheus_provider import OrpheusTTSProvider


def get_tts_provider(config):
    """Create and return the appropriate TTS provider based on configuration.
    
    Args:
        config: Dictionary containing voice configuration
        
    Returns:
        An instance of a BaseTTSProvider implementation
    """
    # Get the provider name from config, default to 'zonos'
    provider_name = config.get('provider', 'zonos').lower()
    
    # Create the appropriate provider based on the name
    if provider_name == 'zonos':
        # Get Zonos-specific settings
        provider_config = config.get('zonos_settings', {})
        # Add postprocessing settings
        provider_config['postprocessing'] = config.get('postprocessing', {})
        return ZonosTTSProvider(provider_config)
    elif provider_name == 'orpheus':
        # Get Orpheus-specific settings
        provider_config = config.get('orpheus_settings', {})
        # Add postprocessing settings
        provider_config['postprocessing'] = config.get('postprocessing', {})
        return OrpheusTTSProvider(provider_config)
    else:
        raise ValueError(f"Unknown TTS provider: {provider_name}")
