import os
import yaml
import requests
import re
import shutil
import argparse
import random
from pathlib import Path
import numpy as np
import librosa
import soundfile as sf

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─────────────────────────────────────────────────────
# 🎲 CONFIGURATION
# ─────────────────────────────────────────────────────
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

# Global variables
CONFIG = None
ZONOS_TTS_SERVER = None
VOICE_SAMPLES = None
SPEECH_RATE = None
SCENARIOS_DIR = None
OUTPUT_DIR = None

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
    project_name = CONFIG.get("project_name", "DeepVideo2")
    output_dir_path = os.path.join(PROJECT_DIR, "output", project_name, OUTPUT_DIR)
    if os.path.exists(output_dir_path):
        shutil.rmtree(output_dir_path)
        print("🧹 Cleaned output directory")
    ensure_dir_exists(output_dir_path)

def get_scenario_files():
    """Get all scenario YAML files."""
    scenario_files = []
    project_name = CONFIG.get("project_name", "DeepVideo2")
    scenarios_path = os.path.join(PROJECT_DIR, "output", project_name, SCENARIOS_DIR)
    
    # Ensure scenarios directory exists
    if not os.path.exists(scenarios_path):
        print(f"⚠️ Scenarios directory not found: {scenarios_path}")
        return scenario_files
    
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

def generate_voice_line(text, output_path, emotion, voice_sample):
    """Generate voice line using Zonos TTS server."""
    # Normalize the output path to use forward slashes
    normalized_output_path = normalize_path(output_path)
    
    params = {
        'text': text,
        'path': normalized_output_path,
        'voice': voice_sample,
        'emotion': emotion.capitalize(),  # Capitalize emotion for the API
        'rate': SPEECH_RATE
    }
    
    try:
        print(f"  🔄 Sending request to TTS server...")
        response = requests.get(ZONOS_TTS_SERVER, params=params)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️ Error generating voice line: {response.text}")
            return False
    except Exception as e:
        print(f"⚠️ Exception when calling TTS API: {str(e)}")
        return False

def normalize_audio(input_path, output_path=None, target_db=-20.0):
    """
    Normalize audio file to a target dB level.
    
    Args:
        input_path: Path to the input audio file
        output_path: Path to save the normalized audio (if None, overwrites input)
        target_db: Target dB level (default: -20.0)
    
    Returns:
        Tuple of (success, original_duration, new_duration)
    """
    try:
        # Load the audio file
        y, sr = librosa.load(input_path, sr=None)
        
        # Get the original duration for logging
        original_duration = librosa.get_duration(y=y, sr=sr)
        
        # Calculate current RMS energy
        rms = np.sqrt(np.mean(y**2))
        current_db = 20 * np.log10(rms)
        
        # Calculate the gain needed
        gain = 10 ** ((target_db - current_db) / 20)
        
        # Apply gain to normalize
        y_normalized = y * gain
        
        # Ensure we don't clip
        max_val = np.max(np.abs(y_normalized))
        if max_val > 1.0:
            y_normalized = y_normalized / max_val * 0.99
        
        # Determine output path
        if output_path is None:
            output_path = input_path
        
        # Export the normalized audio
        sf.write(output_path, y_normalized, sr)
        
        # Calculate new duration (should be the same)
        new_duration = librosa.get_duration(y=y_normalized, sr=sr)
        
        return True, original_duration, new_duration
    except Exception as e:
        print(f"⚠️ Error normalizing {input_path}: {str(e)}")
        return False, 0, 0

def process_scenario(scenario_file, force_regenerate=False, normalize_audio_setting=None, target_db=None):
    """Process a single scenario file and generate voice lines for all slides."""
    # Extract scenario name from filename
    filename = os.path.basename(scenario_file)
    scenario_name = os.path.splitext(filename)[0]
    
    # Load scenario data
    scenario = load_scenario(scenario_file)
    
    print(f"\n{'='*50}")
    print(f"🎤 Generating voice lines for: {scenario['topic']}")
    print(f"{'='*50}")
    
    # Select a random voice sample for this scenario
    voice_sample = random.choice(VOICE_SAMPLES)
    voice_name = os.path.basename(voice_sample)
    print(f"🎙️ Selected voice: {voice_name}")
    
    # Get normalization settings from config
    if normalize_audio_setting is None:
        normalization_enabled = CONFIG.get("voice", {}).get("normalization", {}).get("enabled", False)
    else:
        normalization_enabled = normalize_audio_setting
    
    if target_db is None:
        target_db = CONFIG.get("voice", {}).get("normalization", {}).get("target_db", -20.0)
    
    if normalization_enabled:
        print(f"🔊 Audio normalization enabled (target: {target_db} dB)")
    
    # Create project-specific output directory
    project_name = CONFIG.get("project_name", "DeepVideo2")
    output_dir_path = os.path.join(PROJECT_DIR, "output", project_name, OUTPUT_DIR)
    ensure_dir_exists(output_dir_path)
    
    # Process each slide
    for i, slide in enumerate(scenario['slides']):
        # Create output filename
        slide_id = f"slide_{i+1:02d}"
        output_filename = f"{scenario_name}_{slide_id}.wav"
        
        # Create absolute output path
        output_path = os.path.join(output_dir_path, output_filename)
        
        # Check if the file already exists and skip if not forcing regeneration
        if os.path.exists(output_path) and not force_regenerate:
            print(f"  ⏩ Skipping slide {i+1}: File already exists")
            continue
        
        # Get slide text and emotion
        text = slide['text']
        emotion = slide['emotion']
        
        print(f"  🔊 Slide {i+1}: \"{text}\" - {emotion}")
        
        # Generate voice line with the selected voice sample
        if generate_voice_line(text, output_path, emotion, voice_sample):
            print(f"  ✅ Generated: {output_filename}")
            
            # Normalize audio if enabled
            if normalization_enabled and os.path.exists(output_path):
                print(f"  🔄 Normalizing audio to {target_db} dB...")
                success, original_duration, new_duration = normalize_audio(
                    output_path, None, target_db
                )
                if success:
                    print(f"  ✅ Normalized: {output_filename} ({original_duration:.2f}s → {new_duration:.2f}s)")
                else:
                    print(f"  ⚠️ Failed to normalize: {output_filename}")
        else:
            print(f"  ❌ Failed to generate: {output_filename}")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate voice lines for scenarios')
    parser.add_argument('-c', '--config', type=str, required=True,
                        help='Path to the configuration file')
    parser.add_argument('--clean', action='store_true', 
                        help='Remove all existing voice lines before generation')
    parser.add_argument('--force', action='store_true',
                        help='Force regeneration of voice lines even if they already exist')
    parser.add_argument('--normalize', action='store_true',
                        help='Force audio normalization even if disabled in config')
    parser.add_argument('--no-normalize', action='store_true',
                        help='Disable audio normalization even if enabled in config')
    parser.add_argument('--target-db', type=float,
                        help='Target dB level for audio normalization (overrides config)')
    return parser.parse_args()

def main():
    """Main function to process all scenarios."""
    args = parse_arguments()
    
    # Load configuration from specified file
    global CONFIG, ZONOS_TTS_SERVER, VOICE_SAMPLES, SPEECH_RATE, SCENARIOS_DIR, OUTPUT_DIR
    CONFIG = load_config(args.config)
    
    # Voice generation settings
    ZONOS_TTS_SERVER = CONFIG["voice"]["zonos_tts_server"]
    VOICE_SAMPLES = CONFIG["voice"]["voice_samples"]
    SPEECH_RATE = CONFIG["voice"]["speech_rate"]
    
    # Directory settings
    SCENARIOS_DIR = CONFIG["directories"]["scenarios"]
    OUTPUT_DIR = CONFIG["directories"]["voice_lines"]
    
    # Get project name
    project_name = CONFIG.get("project_name", "DeepVideo2")
    print(f"\n🚀 Starting {project_name} voice line generation...")
    
    # Clean output directory if requested
    output_dir_path = os.path.join(PROJECT_DIR, "output", project_name, OUTPUT_DIR)
    if args.clean:
        clean_output_directory()
    else:
        ensure_dir_exists(output_dir_path)
    
    # Get all scenario files
    scenario_files = get_scenario_files()
    print(f"📂 Found {len(scenario_files)} scenario files")
    
    # Process each scenario
    for scenario_file in scenario_files:
        normalize_audio_setting = None
        target_db = None
        if args.normalize:
            normalize_audio_setting = True
        elif args.no_normalize:
            normalize_audio_setting = False
        if args.target_db:
            target_db = args.target_db
        process_scenario(scenario_file, args.force, normalize_audio_setting, target_db)
    
    print("\n🎉 Voice line generation complete!")

if __name__ == "__main__":
    main()
