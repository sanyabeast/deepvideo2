#!/usr/bin/env python
"""
Clean script for DeepVideo2 project.

This script has two modes:
1. Default mode: Removes the 'has_video' property from scenario YAML files
2. Hard mode (-d): Removes all generated content for the specified config
   (scenarios, videos, voice lines)
3. All mode (-a): Removes all output directories without requiring a config file
"""

import os
import yaml
import argparse
import shutil
import sys

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

def load_config(config_path=None):
    """Load configuration from YAML file."""
    if config_path is None:
        print("❌ Error: No config file specified.")
        print("💡 Hint: Use -c or --config to specify a config file. Example: -c configs/sample.yaml")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Extract project name from config filename if not specified
        if 'project_name' not in config:
            # Get the filename without extension
            config_filename = os.path.basename(config_path)
            config_name = os.path.splitext(config_filename)[0]
            config['project_name'] = config_name
            print(f"ℹ️ Using config filename '{config_name}' as project name")
        
        return config
    except FileNotFoundError:
        print(f"❌ Error: Config file not found: {config_path}")
        print(f"💡 Hint: Make sure the config file exists. Example: configs/sample.yaml")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config file: {e}")
        sys.exit(1)

def reset_scenarios(config, dry_run=False):
    """Remove the has_video property from all scenario YAML files."""
    project_name = config.get("project_name")
    
    print(f"\n🚀 Starting scenario reset for project: {project_name}")
    
    # Get the scenarios directory
    output_dir = os.path.join(PROJECT_DIR, "output", project_name)
    scenarios_dir = os.path.join(output_dir, config.get("directories", {}).get("scenarios", "scenarios"))
    
    # Create the directory if it doesn't exist
    os.makedirs(scenarios_dir, exist_ok=True)
    
    # Find all YAML files in the scenarios directory
    scenario_files = [f for f in os.listdir(scenarios_dir) if f.endswith('.yaml')]
    
    if not scenario_files:
        print(f"⚠️ No scenario files found in {scenarios_dir}")
        return
    
    # Track how many files were reset
    reset_count = 0
    total_count = len(scenario_files)
    
    for filename in scenario_files:
        filepath = os.path.join(scenarios_dir, filename)
        
        try:
            # Load the YAML file
            with open(filepath, 'r', encoding='utf-8') as f:
                scenario = yaml.safe_load(f)
            
            # Check if the has_video property exists
            if 'has_video' in scenario:
                print(f"🔄 Resetting: {filename}")
                
                if not dry_run:
                    # Remove the has_video property
                    scenario.pop('has_video')
                    
                    # Save the modified YAML file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        yaml.dump(scenario, f, default_flow_style=False, sort_keys=False)
                    
                    reset_count += 1
            else:
                # File doesn't have the property, so it's already "reset"
                reset_count += 1
        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
    
    if not dry_run:
        print(f"\n✅ Reset complete: {reset_count} of {total_count} files were reset")
    else:
        print(f"\n🔍 Dry run: Would reset {reset_count} of {total_count} files")

def hard_clean(config, dry_run=False):
    """Remove all generated content for the specified project."""
    project_name = config.get("project_name")
    
    print(f"\n🚀 Starting hard clean for project: {project_name}")
    
    # Define the directories to clean
    output_dir = os.path.join(PROJECT_DIR, "output", project_name)
    scenarios_dir = os.path.join(output_dir, config.get("directories", {}).get("scenarios", "scenarios"))
    voice_lines_dir = os.path.join(output_dir, config.get("directories", {}).get("voice_lines", "voice_lines"))
    videos_dir = os.path.join(output_dir, config.get("directories", {}).get("output_videos", "videos"))
    
    # List of directories to clean
    dirs_to_clean = [
        scenarios_dir,
        voice_lines_dir,
        videos_dir
    ]
    
    # Print what we're going to do
    print(f"\n🧹 Hard clean for project: {project_name}")
    for d in dirs_to_clean:
        print(f"  🗑️ {d}")
    
    if not dry_run:
        # Remove and recreate each directory
        for d in dirs_to_clean:
            if os.path.exists(d):
                shutil.rmtree(d)
                print(f"  ✅ Removed: {d}")
            os.makedirs(d, exist_ok=True)
            print(f"  📁 Created empty directory: {d}")
        
        print(f"\n✅ Hard clean complete for project: {project_name}")
    else:
        print(f"\n🔍 Dry run: Would remove and recreate the above directories")

def clean_all_output():
    """Remove the entire output directory and recreate it empty."""
    output_dir = os.path.join(PROJECT_DIR, "output")
    
    print(f"\n🚀 Cleaning ALL output directories")
    
    if os.path.exists(output_dir):
        print(f"🗑️ Removing: {output_dir}")
        shutil.rmtree(output_dir)
        print(f"✅ Removed: {output_dir}")
    
    # Recreate the empty output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"📁 Created empty directory: {output_dir}")
    
    print(f"\n✅ All output directories cleaned")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Reset or clean DeepVideo2 generated content")
    
    parser.add_argument("-c", "--config", help="Path to the config file")
    parser.add_argument("-d", "--hard", action="store_true", help="Hard clean (remove all generated content)")
    parser.add_argument("-a", "--all", action="store_true", help="Clean all output directories (ignores config)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    return parser.parse_args()

def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Check if we should clean all output directories
    if args.all:
        clean_all_output()
        return
    
    # Require config file if not using --all
    if not args.config:
        print("❌ Error: No config file specified.")
        print("💡 Hint: Use -c or --config to specify a config file, or use -a to clean all output.")
        return 1
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Error loading config: {str(e)}")
        return 1
    
    project_name = config.get("project_name")
    
    if args.hard:
        # Hard clean - remove all generated content for this project
        hard_clean(config, args.dry_run)
    else:
        # Regular clean - just reset the has_video property
        reset_scenarios(config, args.dry_run)
    
    return 0

if __name__ == "__main__":
    main()
