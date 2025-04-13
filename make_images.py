#!/usr/bin/env python3
"""
DeepVideo2 Image Generator

This script generates images for each slide in a scenario using the ComfyUI API.
It works similarly to make_voice_lines.py, taking a config file as a parameter and saving images 
under output/{project-name}/images/{scenario_name}{slide_id}.png.

Usage:
    python make_images.py -c CONFIG_FILE [-s STEPS] [-n NUM_SCENARIOS] [-f] [-d]

Options:
    -c, --config CONFIG_FILE    Path to the configuration file
    -s, --steps STEPS           Number of steps for image generation (default: 20)
    -n, --num NUM_SCENARIOS     Number of scenarios to process (default: -1, all)
    -f, --force                 Force regeneration of all images
    -d, --debug                 Enable debug logging
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
import json
import uuid
import time
from pathlib import Path
from PIL import Image
import io
import websocket

# Define default workflow with placeholders as a raw multiline string
DEFAULT_WORKFLOW = r'''{
    "6": {
        "inputs": {
            "text": "{PROMPT}",
            "clip": [ "30", 1 ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": { "title": "CLIP Text Encode (Positive Prompt)" }
    },
    "8": {
        "inputs": { "samples": [ "31", 0 ], "vae": [ "30", 2 ] },
        "class_type": "VAEDecode",
        "_meta": { "title": "VAE Decode" }
    },
    "9": {
        "inputs": { "filename_prefix": "flux/image", "images": [ "8", 0 ] },
        "class_type": "SaveImage",
        "_meta": { "title": "Save Image" }
    },
    "27": {
        "inputs": { "width": 1024, "height": 1024, "batch_size": 1 },
        "class_type": "EmptySD3LatentImage",
        "_meta": { "title": "EmptySD3LatentImage" }
    },
    "30": {
        "inputs": { "ckpt_name": "flux.1d-fp8.safetensors" },
        "class_type": "CheckpointLoaderSimple",
        "_meta": { "title": "Load Checkpoint" }
    },
    "31": {
        "inputs": {
            "seed": {SEED},
            "steps": {STEPS},
            "cfg": 1,
            "sampler_name": "euler",
            "scheduler": "simple",
            "denoise": 1,
            "model": [ "30", 0 ],
            "positive": [ "35", 0 ],
            "negative": [ "33", 0 ],
            "latent_image": [ "27", 0 ]
        },
        "class_type": "KSampler",
        "_meta": { "title": "KSampler" }
    },
    "33": {
        "inputs": {
            "text": "{NEGATIVE_PROMPT}",
            "clip": [ "30", 1 ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": { "title": "CLIP Text Encode (Negative Prompt)" }
    },
    "35": {
        "inputs": { "guidance": 3.5, "conditioning": [ "6", 0 ] },
        "class_type": "FluxGuidance",
        "_meta": { "title": "FluxGuidance" }
    }
}'''

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

def debug_log(message, emoji=None):
    """Log message only if DEBUG mode is enabled."""
    if DEBUG:
        log(message, emoji)

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
COMFY_SERVER_ADDRESS = None
COMFY_WORKFLOW = None
STEPS = None
SCENARIOS_DIR = None
IMAGES_DIR = None
CLIENT_ID = str(uuid.uuid4())
DEBUG = False  # Set to True to enable verbose logging

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

def queue_prompt(prompt):
    """Queue a prompt to the ComfyUI server.
    
    Args:
        prompt: The workflow prompt to send
        
    Returns:
        The prompt ID if successful, None otherwise
    """
    try:
        p = {"prompt": prompt, "client_id": CLIENT_ID}
        data = json.dumps(p).encode('utf-8')
        
        if DEBUG:
            debug_log(f"Sending prompt to ComfyUI: {json.dumps(prompt, indent=2)[:200]}...", "📤")
            
        req = requests.post(f"http://{COMFY_SERVER_ADDRESS}/prompt", data=data)
        
        if req.status_code != 200:
            log(f"Error queuing prompt: HTTP {req.status_code} - {req.text}", "❌")
            return None
            
        response_json = req.json()
        if "prompt_id" not in response_json:
            log(f"Error in ComfyUI response: 'prompt_id' missing - {response_json}", "❌")
            return None
            
        return response_json["prompt_id"]
    except json.JSONDecodeError as e:
        log(f"Error parsing ComfyUI response: {str(e)}", "❌")
        return None
    except Exception as e:
        log(f"Error queuing prompt: {str(e)}", "❌")
        return None

def get_images_from_websocket(prompt_id):
    """Get images from the ComfyUI websocket.
    
    Args:
        prompt_id: The prompt ID to get images for
        
    Returns:
        A list of image data if successful, None otherwise
    """
    try:
        debug_log(f"Connecting to websocket at ws://{COMFY_SERVER_ADDRESS}/ws?clientId={CLIENT_ID}", "🔌")
        ws = websocket.WebSocket()
        ws.connect(f"ws://{COMFY_SERVER_ADDRESS}/ws?clientId={CLIENT_ID}")
        
        output_images = []
        current_node = ""
        timeout_counter = 0
        max_timeout = 60  # 1 minute max wait time
        saved_images = []  # Track images saved by SaveImage node
        
        log(f"Generating image...", "⏳")
        while timeout_counter < max_timeout:
            try:
                # Set a timeout for receiving messages
                ws.settimeout(1.0)
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    msg_type = message.get('type', 'unknown')
                    debug_log(f"Received message type: {msg_type}", "📡")
                    
                    if msg_type == 'executing':
                        data = message.get('data', {})
                        debug_log(f"Executing data: {data}", "🔍")
                        if data.get('prompt_id') == prompt_id:
                            if data.get('node') is None:
                                debug_log("Execution completed", "✅")
                                break  # Execution is done
                            else:
                                current_node = data.get('node', '')
                                debug_log(f"Processing node: {current_node}", "🔄")
                    
                    elif msg_type == 'executed':
                        data = message.get('data', {})
                        debug_log(f"Executed data: {data}", "🔍")
                        if data.get('prompt_id') == prompt_id:
                            debug_log("Prompt execution finished", "✅")
                            
                            # Check if this is a SaveImage node with output images
                            if 'output' in data and 'images' in data['output']:
                                for img_info in data['output']['images']:
                                    if 'filename' in img_info and 'subfolder' in img_info:
                                        saved_images.append(img_info)
                                        debug_log(f"SaveImage node saved: {img_info}", "💾")
                    
                    elif msg_type == 'execution_cached':
                        data = message.get('data', {})
                        debug_log(f"Execution cached data: {data}", "🔍")
                        if data.get('prompt_id') == prompt_id:
                            debug_log("Prompt execution cached", "ℹ️")
                    
                    elif msg_type == 'executed_node':
                        data = message.get('data', {})
                        debug_log(f"Executed node data: {data}", "🔍")
                        node_id = data.get('node_id', '')
                        debug_log(f"Node executed: {node_id}", "🔄")
                        
                        # Check if this node has output images
                        if 'output_images' in data:
                            debug_log(f"Node {node_id} has output images", "🖼️")
                            for img_info in data.get('output_images', []):
                                debug_log(f"Image info: {img_info}", "🖼️")
                                
                                # Try to get the image directly
                                if 'filename' in img_info and 'subfolder' in img_info:
                                    img_filename = img_info['filename']
                                    img_subfolder = img_info.get('subfolder', '')
                                    img_url = f"http://{COMFY_SERVER_ADDRESS}/view?filename={img_filename}&subfolder={img_subfolder}"
                                    debug_log(f"Trying to download image from URL: {img_url}", "🔗")
                                    
                                    try:
                                        img_response = requests.get(img_url)
                                        if img_response.status_code == 200:
                                            debug_log(f"Successfully downloaded image from URL", "✅")
                                            output_images.append(img_response.content)
                                    except Exception as e:
                                        debug_log(f"Failed to download image: {str(e)}", "⚠️")
                else:
                    # Binary data (image)
                    debug_log(f"Received binary data from node {current_node}, length: {len(out)}", "📷")
                    # Store binary data, skip first 8 bytes (header)
                    output_images.append(out[8:])
                    debug_log(f"Added binary data to output_images, now have {len(output_images)} images", "📷")
            except websocket.WebSocketTimeoutException:
                timeout_counter += 1
                debug_log(f"Websocket timeout {timeout_counter}/{max_timeout}", "⏱️")
                continue
            except Exception as e:
                debug_log(f"Error in websocket receive loop: {str(e)}", "⚠️")
                timeout_counter += 1
                continue
        
        ws.close()
        debug_log(f"Websocket closed, received {len(output_images)} binary messages", "🔌")
        
        # If we have binary data from websocket, use that
        if output_images:
            debug_log(f"Successfully received {len(output_images)} images from websocket", "🎉")
            return output_images
        
        # If we have saved images info, download them
        if saved_images:
            debug_log(f"Downloading {len(saved_images)} saved images", "🔍")
            downloaded_images = []
            
            for img_info in saved_images:
                img_filename = img_info['filename']
                img_subfolder = img_info.get('subfolder', '')
                img_url = f"http://{COMFY_SERVER_ADDRESS}/view?filename={img_filename}&subfolder={img_subfolder}"
                debug_log(f"Downloading saved image: {img_url}", "🔗")
                
                try:
                    img_response = requests.get(img_url)
                    if img_response.status_code == 200:
                        debug_log(f"Successfully downloaded saved image", "✅")
                        downloaded_images.append(img_response.content)
                except Exception as e:
                    debug_log(f"Failed to download saved image: {str(e)}", "⚠️")
            
            if downloaded_images:
                return downloaded_images
        
        # If no images from websocket or saved images, try to get them from history
        try:
            debug_log("Trying to get images from history", "🔍")
            history_url = f"http://{COMFY_SERVER_ADDRESS}/history/{prompt_id}"
            response = requests.get(history_url)
            if response.status_code == 200:
                history_data = response.json()
                debug_log(f"History data: {json.dumps(history_data)[:500]}...", "🔍")
                
                # Look for nodes with output images
                for node_id, node_output in history_data.get("outputs", {}).items():
                    debug_log(f"Checking node {node_id} output", "🔍")
                    if "images" in node_output:
                        debug_log(f"Node {node_id} has images: {node_output['images']}", "🖼️")
                        for img_data in node_output["images"]:
                            if "filename" in img_data and "subfolder" in img_data:
                                img_filename = img_data["filename"]
                                img_subfolder = img_data.get("subfolder", "")
                                img_url = f"http://{COMFY_SERVER_ADDRESS}/view?filename={img_filename}&subfolder={img_subfolder}"
                                debug_log(f"Found image URL: {img_url}", "🔗")
                                
                                # Download the image
                                img_response = requests.get(img_url)
                                if img_response.status_code == 200:
                                    debug_log("Successfully downloaded image from history", "✅")
                                    return [img_response.content]
        except Exception as e:
            debug_log(f"Failed to get images from history: {str(e)}", "⚠️")
        
        # As a last resort, try to get the most recent image from the output directory
        try:
            debug_log("Trying to get the most recent image from output directory", "🔍")
            output_dir_url = f"http://{COMFY_SERVER_ADDRESS}/view_metadata/folders"
            folders_response = requests.get(output_dir_url)
            if folders_response.status_code == 200:
                folders = folders_response.json()
                debug_log(f"Found folders: {folders}", "📁")
                
                # Look for images in each folder
                for folder in folders:
                    folder_url = f"http://{COMFY_SERVER_ADDRESS}/view_metadata/images?folder={folder}"
                    images_response = requests.get(folder_url)
                    if images_response.status_code == 200:
                        images = images_response.json()
                        if images:
                            # Sort by creation time (most recent first)
                            images.sort(key=lambda x: x.get("date_created", 0), reverse=True)
                            most_recent = images[0]
                            debug_log(f"Most recent image: {most_recent}", "🖼️")
                            
                            img_url = f"http://{COMFY_SERVER_ADDRESS}/view?filename={most_recent['filename']}&subfolder={folder}"
                            debug_log(f"Trying to download most recent image: {img_url}", "🔗")
                            
                            img_response = requests.get(img_url)
                            if img_response.status_code == 200:
                                debug_log("Successfully downloaded most recent image", "✅")
                                return [img_response.content]
        except Exception as e:
            debug_log(f"Failed to get most recent image: {str(e)}", "⚠️")
        
        log("No images returned from ComfyUI", "⚠️")
        return None
            
    except Exception as e:
        log(f"Error getting images from websocket: {str(e)}", "❌")
        return None

def generate_image(prompt_text, negative_prompt="", steps=20):
    """Generate an image using ComfyUI API.
    
    Args:
        prompt_text: The text prompt for image generation
        negative_prompt: Optional negative prompt to guide what not to generate
        steps: Number of steps for generation
        
    Returns:
        Image data if successful, None otherwise
    """
    log(f"Generating image with prompt: {prompt_text[:50]}{'...' if len(prompt_text) > 50 else ''}", "🎨")
    
    try:
        # Create a copy of the workflow template
        workflow_str = DEFAULT_WORKFLOW
        
        # Generate a random seed
        random_seed = random.randint(1, 2147483647)
        debug_log(f"Using random seed: {random_seed}", "🎲")
        
        # Properly escape the prompts for JSON
        prompt_text_escaped = json.dumps(prompt_text)[1:-1]  # Remove the outer quotes
        negative_prompt_escaped = json.dumps(negative_prompt)[1:-1]  # Remove the outer quotes
        
        # Replace placeholders in the workflow string
        replacements = {
            "{PROMPT}": prompt_text_escaped,
            "{NEGATIVE_PROMPT}": negative_prompt_escaped,
            "{SEED}": str(random_seed),
            "{STEPS}": str(steps)
        }
        
        for placeholder, value in replacements.items():
            workflow_str = workflow_str.replace(placeholder, value)
        
        # Parse the updated workflow string back to JSON
        try:
            workflow = json.loads(workflow_str)
        except json.JSONDecodeError as e:
            log(f"Error parsing workflow JSON: {str(e)}", "❌")
            debug_log(f"Workflow string: {workflow_str}", "📄")
            return None
        
        # Queue the prompt
        prompt_id = queue_prompt(workflow)
        if not prompt_id:
            log("Failed to queue prompt", "❌")
            return None
        
        debug_log(f"Prompt queued with ID: {prompt_id}", "✅")
        
        # Get images from websocket
        images = get_images_from_websocket(prompt_id)
        if not images:
            log("Failed to get images from ComfyUI", "❌")
            return None
        
        log("Image generated successfully", "✅")
        return images
        
    except Exception as e:
        log(f"Error generating image: {str(e)}", "❌")
        return None

def save_image(image_data, output_path):
    """Save image data to a file.
    
    Args:
        image_data: Raw image data
        output_path: Path to save the image
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert the binary data to an image
        image = Image.open(io.BytesIO(image_data))
        image.save(output_path)
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
            if save_image(image_data[0], output_path):
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
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug logging')
    return parser.parse_args()

def main():
    """Main function to process all scenarios."""
    global CONFIG, COMFY_SERVER_ADDRESS, COMFY_WORKFLOW, STEPS, SCENARIOS_DIR, IMAGES_DIR, DEBUG
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set debug mode
    DEBUG = args.debug
    
    # Load configuration
    CONFIG = load_config(args.config)
    
    # Set up global variables from config
    # Use default values if 'images' section is not found
    if "images" not in CONFIG:
        log("Warning: 'images' section not found in config file, using default values", "⚠️")
        CONFIG["images"] = {
            "comfy_server_address": "127.0.0.1:8188",
            "steps": 20,
            "default_negative_prompt": "text, watermark, signature, blurry, distorted, low resolution, poorly drawn, bad anatomy, deformed, disfigured, out of frame, cropped",
            "workflow": json.dumps(DEFAULT_WORKFLOW)
        }
    
    # Set ComfyUI server address
    COMFY_SERVER_ADDRESS = CONFIG["images"].get("comfy_server_address", "127.0.0.1:8188")
    
    # Set workflow (default to the one in the config if available)
    if "workflow" in CONFIG["images"]:
        COMFY_WORKFLOW = CONFIG["images"]["workflow"]
    else:
        # Use a default workflow if not specified
        log("Warning: No workflow specified in config, using default workflow", "⚠️")
        COMFY_WORKFLOW = json.dumps(DEFAULT_WORKFLOW)
    
    # Set steps (CLI args take priority over config)
    config_steps = CONFIG["images"].get("steps", 20)
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
    log("DeepVideo2 Image Generator (ComfyUI)")
    log("="*50)
    log(f"Project: {CONFIG.get('project_name', 'DeepVideo2')}", "📁")
    log(f"ComfyUI Server: {COMFY_SERVER_ADDRESS}", "🌐")
    log(f"Steps: {STEPS}", "🔢")
    log(f"Force regenerate: {args.force}", "🔄")
    
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
        log("\nProcess interrupted by user", "⚠️")
        sys.exit(1)
    except Exception as e:
        log(f"An error occurred: {str(e)}", "❌")
        sys.exit(1)
