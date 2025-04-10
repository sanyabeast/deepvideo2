#!/usr/bin/env python
"""
Reset script for DeepVideo2 project.
This script removes the 'has_video' property from all scenario YAML files,
allowing them to be reprocessed by the make_video.py script.
"""

import os
import yaml
import argparse

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Reset scenario files by removing the has_video property.')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    return parser.parse_args()

def reset_scenarios(dry_run=False):
    """Remove the has_video property from all scenario YAML files."""
    # Get the path to the scenarios directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenarios_dir = os.path.join(script_dir, 'scenarios')
    
    if not os.path.exists(scenarios_dir):
        print(f"❌ Scenarios directory not found: {scenarios_dir}")
        return
    
    # Get all YAML files in the scenarios directory
    scenario_files = [f for f in os.listdir(scenarios_dir) if f.endswith('.yaml')]
    
    if not scenario_files:
        print("❌ No scenario files found.")
        return
    
    print(f"🔍 Found {len(scenario_files)} scenario files.")
    
    # Count of modified files
    modified_count = 0
    
    # Process each scenario file
    for filename in scenario_files:
        filepath = os.path.join(scenarios_dir, filename)
        
        # Load the YAML file
        with open(filepath, 'r', encoding='utf-8') as file:
            scenario = yaml.safe_load(file)
        
        # Check if the file has the has_video property
        if 'has_video' in scenario:
            if dry_run:
                print(f"🔄 Would remove has_video property from: {filename}")
            else:
                # Remove the has_video property
                del scenario['has_video']
                
                # Save the modified YAML file
                with open(filepath, 'w', encoding='utf-8') as file:
                    yaml.dump(scenario, file, default_flow_style=False)
                
                print(f"✅ Removed has_video property from: {filename}")
            
            modified_count += 1
    
    # Print summary
    if dry_run:
        print(f"🔍 Dry run completed. Would modify {modified_count} of {len(scenario_files)} files.")
    else:
        print(f"🎉 Reset completed. Modified {modified_count} of {len(scenario_files)} files.")

def main():
    """Main function."""
    args = parse_args()
    reset_scenarios(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
