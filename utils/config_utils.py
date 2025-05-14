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

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration requirements.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If validation fails
    """
    # Check required sections
    if "prompts" not in config:
        raise ValueError("Missing 'prompts' section in config")
    
    prompts = config["prompts"]
    if "topics" not in prompts or "scenario" not in prompts:
        raise ValueError("Config must have both 'topics' and 'scenario' sections under 'prompts'")
    
    # Check topics prompt
    topics_prompt = prompts["topics"]
    if "instruction" not in topics_prompt:
        raise ValueError("Missing 'instruction' in topics prompt")
    if "{THEME}" not in topics_prompt["instruction"]:
        raise ValueError("Topics prompt instruction must contain {THEME} placeholder")
    
    # Check scenario prompt
    scenario_prompt = prompts["scenario"]
    if "instruction" not in scenario_prompt:
        raise ValueError("Missing 'instruction' in scenario prompt")
    if "{TOPIC}" not in scenario_prompt["instruction"]:
        raise ValueError("Scenario prompt instruction must contain {TOPIC} placeholder")

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries. Values in override will take precedence over values in base.
    Lists are overridden, not merged.
    
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
            # For lists and all other values, override completely
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

def load_all_configs() -> list[Dict[str, Any]]:
    """
    Load all configuration files from the configs directory.
    
    Returns:
        List of merged configuration dictionaries
    """
    configs_dir = os.path.join(PROJECT_DIR, 'configs')
    configs = []
    
    # List all .yaml files in configs directory
    for file in os.listdir(configs_dir):
        if file.endswith('.yaml'):
            config_path = os.path.join(configs_dir, file)
            try:
                config = load_config(config_path, validate=False)  # Skip validation for now
                configs.append(config)
            except Exception as e:
                print(f"⚠️ Warning: Failed to load {file}: {e}")
                continue
    
    # Validate all configs after loading
    for config in configs:
        try:
            validate_config(config)
        except ValueError as e:
            print(f"⚠️ Warning: Invalid config {config.get('project_name', 'unknown')}: {e}")
            configs.remove(config)
    
    return configs

def load_config(config_path: Optional[str] = None, validate: bool = True) -> Dict[str, Any]:
    """
    Load configuration from a YAML file and merge it with the global configuration.
    Validates the final merged configuration.
    
    Args:
        config_path: Path to the project-specific config file. Can be either:
            - Full path (e.g. 'configs/motivation.yaml')
            - Just the name (e.g. 'motivation')
        
    Returns:
        Merged configuration dictionary
        
    Raises:
        ValueError: If configuration validation fails
    """
    if config_path is None:
        print("❌ Error: No config file specified.")
        print("💡 Hint: Use -c or --config to specify a config file. Examples:")
        print("   -c configs/motivation.yaml")
        print("   -c motivation")
        print("   -c * (to process all configs)")
        sys.exit(1)
        
    # Handle wildcard to load all configs
    if config_path == '*':
        return load_all_configs()
    
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
        # Validate the merged configuration if requested
        if validate:
            validate_config(merged_config)
    
        # Return the merged configuration
        return merged_config
    except FileNotFoundError:
        print(f"❌ Error: Config file not found: {config_path}")
        print(f"💡 Hint: Make sure the config file exists. Example: configs/sample.yaml")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config file: {e}")
        sys.exit(1)
