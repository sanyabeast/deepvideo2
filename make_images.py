#!/usr/bin/env python3
"""
DeepVideo2 Image Generator

This script generates images for each slide in a scenario using the Stable Diffusion A1111 HTTP API.
It works similarly to make_voice_lines.py, taking a config file as a parameter and saving images 
under output/{project-name}/images/{scenario_name}{slide_id}.png.

Usage:
    python make_images.py -c CONFIG_FILE [-s STEPS] [-n NUM_SCENARIOS] [-f]

Options:
    -c, --config CONFIG_FILE    Path to the configuration file
    -s, --steps STEPS           Number of steps for image generation (default: 24)
    -n, --num NUM_SCENARIOS     Number of scenarios to process (default: -1, all)
    -f, --force                 Force regeneration of all images
"""

import os
import yaml
import requests
import re
import shutil
import argparse
import random
import sys
import base64
from pathlib import Path

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─────────────────────────────────────────────────────
# 🎲 CONFIGURATION
# ─────────────────────────────────────────────────────
def log(message, emoji=None):
    """Standardized logging function with consistent emoji spacing.
    
    Args:
        message: The message to log
        emoji: Optional emoji to prefix the message
    """
    if emoji:
        # Ensure there's a space after the emoji
        print(f"{emoji} {message}")
    else:
        print(message)

def load_config(config_path=None):
    """Load configuration from YAML file."""
    if config_path is None:
        log("Error: No config file specified.", "❌")
        log("Hint: Use -c or --config to specify a config file. Example: -c configs/sample.yaml", "💡")
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
            log(f"Using config filename '{config_name}' as project name", "ℹ️")
        
        return config
    except FileNotFoundError:
        log(f"Error: Config file not found: {config_path}", "❌")
        log(f"Hint: Make sure the config file exists. Example: configs/sample.yaml", "💡")
        sys.exit(1)
    except yaml.YAMLError as e:
        log(f"Error parsing config file: {e}", "❌")
        sys.exit(1)

# Global variables
CONFIG = None
SD_API_URL = None
SD_CHECKPOINT = None
STEPS = None
SCENARIOS_DIR = None
IMAGES_DIR = None

# ─────────────────────────────────────────────────────
# 🐍 UTILITIES
# ─────────────────────────────────────────────────────
def ensure_dir_exists(directory):
    """Create directory if it doesn't exist."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def clean_output_directory():
    """Remove all files from the output directory."""
    project_name = CONFIG.get("project_name", "DeepVideo2")
    output_dir_path = os.path.join(PROJECT_DIR, "output", project_name, IMAGES_DIR)
    if os.path.exists(output_dir_path):
        shutil.rmtree(output_dir_path)
        log("Cleaned output directory", "🧹")
    ensure_dir_exists(output_dir_path)

def get_scenario_files():
    """Get all scenario YAML files."""
    scenario_files = []
    project_name = CONFIG.get("project_name", "DeepVideo2")
    scenarios_path = os.path.join(PROJECT_DIR, "output", project_name, SCENARIOS_DIR)
    
    # Ensure scenarios directory exists
    if not os.path.exists(scenarios_path):
        log(f"Scenarios directory not found: {scenarios_path}", "⚠️")
        return scenario_files
    
    for filename in os.listdir(scenarios_path):
        if filename.endswith('.yaml'):
            scenario_files.append(os.path.join(scenarios_path, filename))
    return scenario_files

def load_scenario(file_path):
    """Load scenario from YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def set_stable_diffusion_checkpoint():
    """Set the Stable Diffusion checkpoint model."""
    log(f"Setting Stable Diffusion checkpoint to: {SD_CHECKPOINT}", "🔄")
    
    try:
        response = requests.post(
            f"{SD_API_URL}/options",
            json={"sd_model_checkpoint": SD_CHECKPOINT},
            timeout=30
        )
        
        if response.status_code == 200:
            log("Checkpoint set successfully", "✅")
            return True
        else:
            log(f"Failed to set checkpoint: {response.status_code} - {response.text}", "❌")
            return False
    except Exception as e:
        log(f"Error setting checkpoint: {str(e)}", "❌")
        return False

def generate_image(prompt, negative_prompt="", steps=24):
    """Generate an image using Stable Diffusion A1111 API.
    
    Args:
        prompt: The text prompt for image generation
        negative_prompt: Optional negative prompt to guide what not to generate
        steps: Number of steps for generation
        
    Returns:
        Base64 encoded image data or None if generation failed
    """
    log(f"Generating image with prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}", "🎨")
    
    try:
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": 1024,
            "height": 1024,
            "tiling": False,
            "steps": steps,
            "sampler_name": CONFIG["images"].get("sampler_name", "DPM++ SDE"),
            "scheduler": CONFIG["images"].get("scheduler", "Karras")
        }
        
        response = requests.post(
            f"{SD_API_URL}/txt2img",
            json=payload,
            timeout=120  # Longer timeout for image generation
        )
        
        if response.status_code == 200:
            result = response.json()
            if "images" in result and len(result["images"]) > 0:
                return result["images"][0]
            else:
                log("No images returned in response", "⚠️")
                return None
        else:
            log(f"Failed to generate image: {response.status_code} - {response.text}", "❌")
            return None
    except Exception as e:
        log(f"Error generating image: {str(e)}", "❌")
        return None

def save_image(image_data, output_path):
    """Save base64 encoded image data to a file.
    
    Args:
        image_data: Base64 encoded image data
        output_path: Path to save the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
        log(f"Image saved to: {output_path}", "💾")
        return True
    except Exception as e:
        log(f"Error saving image: {str(e)}", "❌")
        return False

def process_scenario(scenario_file, force_regenerate=False, steps=None):
    """Process a single scenario file and generate images for all slides.
    
    Args:
        scenario_file: Path to the scenario file
        force_regenerate: Whether to regenerate existing images
        steps: Number of steps for image generation (overrides config)
    
    Returns:
        Number of images generated
    """
    # Extract scenario name from filename
    filename = os.path.basename(scenario_file)
    scenario_name = os.path.splitext(filename)[0]
    
    # Load scenario data
    scenario = load_scenario(scenario_file)
    
    log("\n" + "="*50)
    log(f"Generating images for: {scenario['topic']}")
    log("="*50)
    
    # Get project name and create output directory
    project_name = CONFIG.get("project_name", "DeepVideo2")
    output_dir = os.path.join(PROJECT_DIR, "output", project_name, IMAGES_DIR)
    ensure_dir_exists(output_dir)
    
    # Use steps from args if provided, otherwise from config
    steps_to_use = steps if steps is not None else STEPS
    
    # Get default negative prompt from config if available
    default_negative_prompt = ""
    if CONFIG and "images" in CONFIG and "default_negative_prompt" in CONFIG["images"]:
        default_negative_prompt = CONFIG["images"]["default_negative_prompt"]
    
    # Process each slide
    images_generated = 0
    for i, slide in enumerate(scenario["slides"]):
        # Skip slides without background_image_description
        if not slide.get("background_image_description"):
            log(f"Slide {i+1}: No background image description, skipping", "⚠️")
            continue
        
        # Create output path for this slide's image
        output_filename = f"{scenario_name}_slide_{i+1}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        # Skip if image already exists and not forcing regeneration
        if os.path.exists(output_path) and not force_regenerate:
            log(f"Slide {i+1}: Image already exists, skipping", "ℹ️")
            continue
        
        # Get the prompt from the slide
        prompt = slide["background_image_description"]
        
        # Generate the image
        image_data = generate_image(prompt, default_negative_prompt, steps_to_use)
        
        if image_data:
            # Save the image
            if save_image(image_data, output_path):
                images_generated += 1
                log(f"Slide {i+1}: Image generated successfully", "✅")
            else:
                log(f"Slide {i+1}: Failed to save image", "❌")
        else:
            log(f"Slide {i+1}: Failed to generate image", "❌")
    
    log(f"Generated {images_generated} images for scenario: {scenario_name}", "🎉")
    return images_generated

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate images for scenarios')
    parser.add_argument('-c', '--config', required=True, help='Path to the configuration file')
    parser.add_argument('-s', '--steps', type=int, help='Number of steps for image generation')
    parser.add_argument('-n', '--num', type=int, default=-1, help='Number of scenarios to process (default: -1, all)')
    parser.add_argument('-f', '--force', action='store_true', help='Force regeneration of all images')
    return parser.parse_args()

def main():
    """Main function to process all scenarios."""
    global CONFIG, SD_API_URL, SD_CHECKPOINT, STEPS, SCENARIOS_DIR, IMAGES_DIR
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    CONFIG = load_config(args.config)
    
    # Set up global variables from config
    # Use default values if 'images' section is not found
    if "images" not in CONFIG:
        log("Warning: 'images' section not found in config file, using default values", "⚠️")
        CONFIG["images"] = {
            "sd_api_url": "http://127.0.0.1:6969/sdapi/v1",
            "checkpoint": "sdxl.1.0-realvis-v50-lightning-baked-vae.safetensors",
            "steps": 24,
            "sampler_name": "DPM++ SDE",
            "scheduler": "Karras",
            "default_negative_prompt": "text, watermark, signature, blurry, distorted, low resolution, poorly drawn, bad anatomy, deformed, disfigured, out of frame, cropped"
        }
    
    # Set API URL (default to localhost:6969 if not specified)
    SD_API_URL = CONFIG["images"].get("sd_api_url", "http://127.0.0.1:6969/sdapi/v1")
    
    # Remove trailing slash if present
    if SD_API_URL.endswith('/'):
        SD_API_URL = SD_API_URL[:-1]
    
    # Set checkpoint (default to sdxl.1.0-realvis-v50-lightning-baked-vae.safetensors if not specified)
    SD_CHECKPOINT = CONFIG["images"].get("checkpoint", "sdxl.1.0-realvis-v50-lightning-baked-vae.safetensors")
    
    # Set steps (CLI args take priority over config)
    config_steps = CONFIG["images"].get("steps", 24)
    STEPS = args.steps if args.steps is not None else config_steps
    
    # Set directories
    if "directories" not in CONFIG:
        log("Warning: 'directories' section not found in config file, using default values", "⚠️")
        CONFIG["directories"] = {
            "scenarios": "scenarios",
            "images": "images"
        }
    elif "images" not in CONFIG["directories"]:
        log("Warning: 'images' directory not specified in config, using default 'images'", "⚠️")
        CONFIG["directories"]["images"] = "images"
    
    SCENARIOS_DIR = CONFIG["directories"]["scenarios"]
    IMAGES_DIR = CONFIG["directories"]["images"]
    
    # Log configuration
    log("\n" + "="*50)
    log("DeepVideo2 Image Generator")
    log("="*50)
    log(f"Project: {CONFIG.get('project_name', 'DeepVideo2')}", "📁")
    log(f"SD API URL: {SD_API_URL}", "🌐")
    log(f"Checkpoint: {SD_CHECKPOINT}", "🧠")
    log(f"Steps: {STEPS}", "🔢")
    log(f"Force regenerate: {args.force}", "🔄")
    
    # Set the Stable Diffusion checkpoint
    if not set_stable_diffusion_checkpoint():
        log("Failed to set Stable Diffusion checkpoint. Make sure the A1111 API is running.", "❌")
        sys.exit(1)
    
    # Get all scenario files
    scenario_files = get_scenario_files()
    
    if not scenario_files:
        log("No scenario files found", "⚠️")
        sys.exit(0)
    
    log(f"Found {len(scenario_files)} scenario files", "📊")
    
    # Process scenarios
    total_images_generated = 0
    scenarios_processed = 0
    
    # Determine how many scenarios to process
    max_scenarios = args.num if args.num >= 0 else len(scenario_files)
    
    for scenario_file in scenario_files:
        if max_scenarios > 0 and scenarios_processed >= max_scenarios:
            break
        
        images_generated = process_scenario(scenario_file, args.force, args.steps)
        total_images_generated += images_generated
        scenarios_processed += 1
        
        log(f"Progress: {scenarios_processed}/{max_scenarios if max_scenarios < len(scenario_files) else len(scenario_files)} scenarios processed", "📊")
    
    log("\n" + "="*50)
    log(f"Total: {total_images_generated} images generated for {scenarios_processed} scenarios", "🎉")
    log("="*50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\nProcess interrupted by user (Ctrl+C)", "⚠️")
        log("Exiting gracefully...", "🛑")
        sys.exit(130)  # Standard exit code for SIGINT
