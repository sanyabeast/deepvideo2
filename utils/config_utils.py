"""
Configuration utilities for DeepVideo2.

This module provides functions for loading and merging configuration files.
"""

import os
import yaml
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries. Values in override will take precedence over values in base.
    
    Args:
        base: Base dictionary
        override: Dictionary with values to override
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        # If both are dictionaries, merge them recursively
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            # Otherwise, override the value
            result[key] = value
            
    return result

def load_global_config() -> Dict[str, Any]:
    """
    Load the global configuration file.
    
    Returns:
        Global configuration dictionary or empty dict if file not found
    """
    global_config_path = os.path.join(PROJECT_DIR, "config.yaml")
    
    if os.path.exists(global_config_path):
        try:
            with open(global_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️ Warning: Failed to load global config: {e}")
            return {}
    else:
        return {}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file and merge it with the global configuration.
    
    Args:
        config_path: Path to the project-specific config file. Can be either:
            - Full path (e.g. 'configs/motivation.yaml')
            - Just the name (e.g. 'motivation')
        
    Returns:
        Merged configuration dictionary
    """
    if config_path is None:
        print("❌ Error: No config file specified.")
        print("💡 Hint: Use -c or --config to specify a config file. Examples:")
        print("   -c configs/motivation.yaml")
        print("   -c motivation")
        sys.exit(1)
    
    try:
        # Load global config first
        global_config = load_global_config()
        
        # If config_path doesn't end in .yaml, assume it's a shorthand name
        if not config_path.lower().endswith('.yaml'):
            config_path = os.path.join(PROJECT_DIR, 'configs', f"{config_path}.yaml")
            print(f"ℹ️ Using config file: {config_path}")
        
        # Load project-specific config
        with open(config_path, 'r', encoding='utf-8') as f:
            project_config = yaml.safe_load(f) or {}
        
        # Extract project name from config filename if not specified
        if 'project_name' not in project_config:
            # Get the filename without extension
            config_filename = os.path.basename(config_path)
            config_name = os.path.splitext(config_filename)[0]
            project_config['project_name'] = config_name
            print(f"ℹ️ Using config filename '{config_name}' as project name")
        
        # Merge global and project configs
        merged_config = deep_merge(global_config, project_config)
        
        return merged_config
    except FileNotFoundError:
        print(f"❌ Error: Config file not found: {config_path}")
        print(f"💡 Hint: Make sure the config file exists. Example: configs/sample.yaml")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config file: {e}")
        sys.exit(1)
