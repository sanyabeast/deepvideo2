import os
import yaml
import requests
import re
import shutil
import argparse
from pathlib import Path

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─────────────────────────────────────────────────────
# 🎲 CONFIGURATION
# ─────────────────────────────────────────────────────
def load_config():
    """Load configuration from config.yaml file."""
    config_path = os.path.join(PROJECT_DIR, "config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Load configuration
CONFIG = load_config()

# Voice generation settings
ZONOS_TTS_SERVER = CONFIG["voice"]["zonos_tts_server"]
VOICE_SAMPLE = CONFIG["voice"]["voice_sample"]
SPEECH_RATE = CONFIG["voice"]["speech_rate"]

# Directory settings
SCENARIOS_DIR = CONFIG["directories"]["scenarios"]
OUTPUT_DIR = CONFIG["directories"]["voice_lines"]

# ─────────────────────────────────────────────────────
# 🐍 UTILITIES
# ─────────────────────────────────────────────────────
def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    text = re.sub(r'[^\w\s]', '', text).lower()
    return re.sub(r'\s+', '_', text)

def ensure_dir_exists(directory):
    """Create directory if it doesn't exist."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def clean_output_directory():
    """Remove all files from the output directory."""
    output_dir_path = os.path.join(PROJECT_DIR, OUTPUT_DIR)
    if os.path.exists(output_dir_path):
        shutil.rmtree(output_dir_path)
        print("🧹 Cleaned output directory")
    ensure_dir_exists(output_dir_path)

def get_scenario_files():
    """Get all scenario YAML files."""
    scenario_files = []
    scenarios_path = os.path.join(PROJECT_DIR, SCENARIOS_DIR)
    for filename in os.listdir(scenarios_path):
        if filename.endswith('.yaml'):
            scenario_files.append(os.path.join(scenarios_path, filename))
    return scenario_files

def load_scenario(file_path):
    """Load scenario from YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def normalize_path(path):
    """Normalize path to use forward slashes consistently."""
    return str(Path(path)).replace('\\', '/')

def generate_voice_line(text, output_path, emotion):
    """Generate voice line using Zonos TTS server."""
    # Normalize the output path to use forward slashes
    normalized_output_path = normalize_path(output_path)
    
    params = {
        'text': text,
        'path': normalized_output_path,
        'voice': VOICE_SAMPLE,
        'emotion': emotion.capitalize(),  # Capitalize emotion for the API
        'rate': SPEECH_RATE
    }
    
    try:
        response = requests.get(ZONOS_TTS_SERVER, params=params)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️ Error generating voice line: {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Exception when calling TTS API: {str(e)}")
        return False

def process_scenario(scenario_file, force_regenerate=False):
    """Process a single scenario file and generate voice lines for all slides."""
    # Extract scenario name from filename
    filename = os.path.basename(scenario_file)
    scenario_name = os.path.splitext(filename)[0]
    
    # Load scenario data
    scenario = load_scenario(scenario_file)
    
    print(f"\n{'='*50}")
    print(f"🎤 Generating voice lines for: {scenario['topic']}")
    print(f"{'='*50}")
    
    # Process each slide
    for i, slide in enumerate(scenario['slides']):
        # Create output filename
        slide_id = f"slide_{i+1:02d}"
        output_filename = f"{scenario_name}_{slide_id}.wav"
        
        # Create absolute output path
        output_path = os.path.join(PROJECT_DIR, OUTPUT_DIR, output_filename)
        
        # Check if the file already exists and skip if not forcing regeneration
        if os.path.exists(output_path) and not force_regenerate:
            print(f"  ⏩ Skipping slide {i+1}: File already exists")
            continue
        
        # Get slide text and emotion
        text = slide['text']
        emotion = slide['emotion']
        
        print(f"  🔊 Slide {i+1}: \"{text}\" - {emotion}")
        
        # Generate voice line
        if generate_voice_line(text, output_path, emotion):
            print(f"  ✅ Generated: {output_filename}")
        else:
            print(f"  ❌ Failed to generate: {output_filename}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate voice lines for scenarios')
    parser.add_argument('--clean', action='store_true', 
                        help='Remove all existing voice lines before generation')
    parser.add_argument('--force', action='store_true',
                        help='Force regeneration of voice lines even if they already exist')
    return parser.parse_args()

def main():
    """Main function to process all scenarios."""
    args = parse_arguments()
    
    print("\n🎬 Starting voice line generation...")
    
    # Clean output directory if requested
    output_dir_path = os.path.join(PROJECT_DIR, OUTPUT_DIR)
    if args.clean:
        clean_output_directory()
    else:
        ensure_dir_exists(output_dir_path)
    
    # Get all scenario files
    scenario_files = get_scenario_files()
    print(f"📂 Found {len(scenario_files)} scenario files")
    
    # Process each scenario
    for scenario_file in scenario_files:
        process_scenario(scenario_file, args.force)
    
    print("\n🎉 Voice line generation complete!")

if __name__ == "__main__":
    main()
