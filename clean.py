#!/usr/bin/env python
"""
Clean script for DeepVideo2 project.

This script has two modes:
1. Default mode: Removes the 'has_video' property from scenario YAML files
2. Hard mode (-h): Removes all generated content for the specified config
   (scenarios, videos, voice lines)
"""

import os
import yaml
import argparse
import shutil
import sys

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

def load_config(config_path=None):
    """Load configuration from config file."""
    if config_path is None:
        # Default to config.yaml in project root for backward compatibility
        config_path = os.path.join(PROJECT_DIR, "config.yaml")
    
    # Check if the path is relative
    if not os.path.isabs(config_path):
        config_path = os.path.join(PROJECT_DIR, config_path)
        
    # Ensure the file exists
    if not os.path.exists(config_path):
        # Check if the user might have meant configs/ instead of config/
        if 'config/' in config_path and not os.path.exists(config_path.replace('config/', 'configs/')):
            raise FileNotFoundError(f"Config file not found: {config_path}\nDid you mean 'configs/' instead of 'config/'?")
        
        # Check if any config files exist in the configs directory
        configs_dir = os.path.join(PROJECT_DIR, 'configs')
        if os.path.exists(configs_dir):
            config_files = [f for f in os.listdir(configs_dir) if f.endswith('.yaml')]
            if config_files:
                available_configs = '\n  - '.join([''] + [f'configs/{f}' for f in config_files])
                raise FileNotFoundError(f"Config file not found: {config_path}\nAvailable config files:{available_configs}")
        
        # Default error message
        raise FileNotFoundError(f"Config file not found: {config_path}\nPlease check the path and try again.")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def reset_scenarios(config, dry_run=False):
    """Remove the has_video property from all scenario YAML files."""
    # Get project name from config
    project_name = config.get("project_name", "DeepVideo2")
    
    # Get the path to the project-specific scenarios directory
    scenarios_dir = os.path.join(PROJECT_DIR, "output", project_name, config["directories"]["scenarios"])
    
    if not os.path.exists(scenarios_dir):
        print(f"❌ Scenarios directory not found: {scenarios_dir}")
        return
    
    # Count how many files were processed
    total_files = 0
    modified_files = 0
    
    # Process each YAML file in the scenarios directory
    for filename in os.listdir(scenarios_dir):
        if filename.endswith('.yaml'):
            total_files += 1
            filepath = os.path.join(scenarios_dir, filename)
            
            # Load the YAML file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Check if the file has the has_video property
            if 'has_video' in data:
                modified_files += 1
                print(f"🔄 Resetting: {filename}")
                
                if not dry_run:
                    # Remove the has_video property
                    del data['has_video']
                    
                    # Save the modified file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    # Print summary
    if dry_run:
        print(f"\n🔍 Dry run: {modified_files} of {total_files} files would be reset")
    else:
        print(f"\n✅ Reset complete: {modified_files} of {total_files} files were reset")

def hard_clean(config, dry_run=False):
    """Remove all generated content for the specified config."""
    # Get project name from config
    project_name = config.get("project_name", "DeepVideo2")
    
    # Get the path to the project-specific output directory
    output_dir = os.path.join(PROJECT_DIR, "output", project_name)
    
    if not os.path.exists(output_dir):
        print(f"❌ Output directory not found: {output_dir}")
        return
    
    # List all subdirectories to be removed
    subdirs = [
        os.path.join(output_dir, config["directories"]["scenarios"]),
        os.path.join(output_dir, config["directories"]["voice_lines"]),
        os.path.join(output_dir, config["directories"]["output_videos"])
    ]
    
    # Check which directories exist
    existing_dirs = [d for d in subdirs if os.path.exists(d)]
    
    if not existing_dirs:
        print(f"❌ No content directories found in: {output_dir}")
        return
    
    # Print what will be removed
    print(f"\n🧹 Hard clean for project: {project_name}")
    for directory in existing_dirs:
        print(f"  🗑️ {os.path.relpath(directory, PROJECT_DIR)}")
    
    # Remove directories if not in dry run mode
    if not dry_run:
        for directory in existing_dirs:
            try:
                shutil.rmtree(directory)
                print(f"  ✅ Removed: {os.path.relpath(directory, PROJECT_DIR)}")
            except Exception as e:
                print(f"  ❌ Error removing {os.path.relpath(directory, PROJECT_DIR)}: {str(e)}")
        
        # Recreate empty directories
        for directory in subdirs:
            os.makedirs(directory, exist_ok=True)
            print(f"  📁 Created empty directory: {os.path.relpath(directory, PROJECT_DIR)}")
        
        print(f"\n✅ Hard clean complete for project: {project_name}")
    else:
        print(f"\n🔍 Dry run: Would remove and recreate the above directories")

def main():
    """Main function."""
    # Create a custom argument parser that doesn't use -h for help
    parser = argparse.ArgumentParser(description='Clean DeepVideo2 project files.', add_help=False)
    
    # Add a custom help option
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    
    # Add other arguments
    parser.add_argument('-c', '--config', type=str, required=True,
                        help='Path to the configuration file')
    parser.add_argument('-h', '--hard', action='store_true', 
                        help='Hard clean: remove all generated content for the specified config')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Get project name
    project_name = config.get("project_name", "DeepVideo2")
    
    if args.hard:
        # Hard clean: remove all generated content
        print(f"\n🚀 Starting hard clean for project: {project_name}")
        hard_clean(config, args.dry_run)
    else:
        # Default: reset scenario files
        print(f"\n🚀 Starting scenario reset for project: {project_name}")
        reset_scenarios(config, args.dry_run)

if __name__ == "__main__":
    main()
