import os
import re
import shutil
import argparse
import random
import sys
import yaml
from pathlib import Path
import numpy as np
import librosa
import soundfile as sf

# Import the TTS provider system
from tts_providers import get_tts_provider

# Import configuration utilities
from utils.config_utils import load_config

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

# Global variables
CONFIG = None
TTS_PROVIDER = None
VOICE_SAMPLES = None
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

def normalize_path(path):
    """Normalize path to use forward slashes consistently."""
    return str(Path(path)).replace('\\', '/')

def generate_voice_line(text, output_path, emotion, voice_sample):
    """Generate voice line using the configured TTS provider."""
    # Preprocess text for better TTS compatibility (now handled by the provider)
    original_text = text
    processed_text = TTS_PROVIDER.preprocess_text(text)
    
    # Log if text was modified
    if processed_text != original_text:
        log(f"Preprocessed text: \"{original_text}\" → \"{processed_text}\"", "🔄")
    
    log("Sending request to TTS server...", "🔄")
    return TTS_PROVIDER.generate_voice_line(text, output_path, emotion, voice_sample)

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
        log(f"Error normalizing {input_path}: {str(e)}", "⚠️")
        return False, 0, 0

def trim_silence_from_end(input_path, output_path=None, max_silence_sec=1.0, threshold_db=-50):
    """
    Trim silence from the end of an audio file, keeping up to max_silence_sec seconds of silence.
    
    Args:
        input_path: Path to the input audio file
        output_path: Path to save the trimmed audio (if None, overwrites input)
        max_silence_sec: Maximum silence to keep at the end in seconds (default: 1.0)
        threshold_db: Threshold in dB below which audio is considered silence (default: -50)
    
    Returns:
        Tuple of (success, original_duration, new_duration)
    """
    try:
        # Load the audio file
        y, sr = librosa.load(input_path, sr=None)
        
        # Get the original duration for logging
        original_duration = librosa.get_duration(y=y, sr=sr)
        
        # Convert threshold from dB to amplitude
        threshold_amp = 10 ** (threshold_db / 20)
        
        # Find the last non-silent sample
        # Start from the end and move backwards
        last_idx = len(y) - 1
        while last_idx >= 0 and abs(y[last_idx]) < threshold_amp:
            last_idx -= 1
        
        # If the entire file is silent, keep a small portion
        if last_idx < 0:
            log(f"Audio file appears to be entirely silent: {input_path}", "⚠️")
            # Keep just a small portion of silence
            new_y = y[:int(sr * 0.5)]  # 0.5 seconds
        else:
            # Add the desired amount of silence after the last non-silent sample
            silence_samples = int(sr * max_silence_sec)
            end_idx = min(last_idx + silence_samples, len(y))
            new_y = y[:end_idx]
        
        # Determine output path
        if output_path is None:
            output_path = input_path
        
        # Export the trimmed audio
        sf.write(output_path, new_y, sr)
        
        # Calculate new duration
        new_duration = librosa.get_duration(y=new_y, sr=sr)
        
        return True, original_duration, new_duration
    except Exception as e:
        log(f"Error trimming silence from {input_path}: {str(e)}", "⚠️")
        return False, 0, 0

def process_scenario(scenario_file, force_regenerate=False, normalize_audio_setting=None, target_db=None):
    """Process a single scenario file and generate voice lines for all slides."""
    # Extract scenario name from filename
    filename = os.path.basename(scenario_file)
    scenario_name = os.path.splitext(filename)[0]
    
    # Load scenario data
    scenario = load_scenario(scenario_file)
    
    log("\n" + "="*50)
    log(f"Generating voice lines for: {scenario['topic']}")
    log("="*50)
    
    # Handle voice selection based on provider
    voice_config = CONFIG.get("voice", {})
    provider_name = voice_config.get("provider", "zonos")
    
    if provider_name == "zonos":
        # For Zonos, select a random voice sample
        if not VOICE_SAMPLES:
            log("Error: No voice samples configured for Zonos provider", "❌")
            return
        voice_sample = random.choice(VOICE_SAMPLES)
        voice_name = os.path.basename(voice_sample)
        log(f"Selected voice: {voice_name}", "🎤️")
    elif provider_name == "orpheus":
        # For Orpheus, select a random voice preset
        voice_presets = voice_config.get("orpheus_settings", {}).get("voice_presets", [])
        if not voice_presets:
            log("Warning: No voice presets configured for Orpheus provider, using default", "⚠️")
            voice_sample = None
        else:
            voice_sample = random.choice(voice_presets)
            log(f"Selected voice preset: {voice_sample}", "🎤️")
    else:
        # Default case
        voice_sample = None
        log(f"Using default voice for provider: {provider_name}", "🎤️")
    
    # Get postprocessing settings from config
    postprocessing = CONFIG.get("voice", {}).get("postprocessing", {})
    
    # Get normalization settings
    if normalize_audio_setting is None:
        normalization_enabled = postprocessing.get("normalization", {}).get("enabled", False)
    else:
        normalization_enabled = normalize_audio_setting
    
    if target_db is None:
        target_db = postprocessing.get("normalization", {}).get("target_db", -20.0)
    
    if normalization_enabled:
        log(f"Audio normalization enabled (target: {target_db} dB)", "🔊")
    
    # Get silence trimming settings
    silence_trimming = postprocessing.get("silence_trimming", {})
    silence_trimming_enabled = silence_trimming.get("enabled", True)
    max_silence_sec = silence_trimming.get("max_silence_sec", 1.0)
    threshold_db = silence_trimming.get("threshold_db", -50)
    
    if silence_trimming_enabled:
        log(f"Silence trimming enabled (max: {max_silence_sec}s, threshold: {threshold_db} dB)", "✂️")
    
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
            log(f"Skipping slide {i+1}: File already exists", "⏩")
            continue
        
        # Get slide text and emotion
        text = slide['text']
        emotion = slide['emotion']
        
        log(f"Slide {i+1}: \"{text}\" - {emotion}", "🔊")
        
        # Generate voice line with the selected voice sample
        if generate_voice_line(text, output_path, emotion, voice_sample):
            log(f"Generated: {output_filename}", "✅")
            
            # Normalize audio if enabled
            if normalization_enabled and os.path.exists(output_path):
                log(f"Normalizing audio to {target_db} dB...", "🔄")
                success, original_duration, new_duration = normalize_audio(
                    output_path, None, target_db
                )
                if success:
                    log(f"Normalized: {output_filename} ({original_duration:.2f}s → {new_duration:.2f}s)", "✅")
                else:
                    log(f"Failed to normalize: {output_filename}", "⚠️")
                
                # Trim silence from the end if enabled
                if silence_trimming_enabled and os.path.exists(output_path):
                    log(f"Trimming silence from the end (max: {max_silence_sec}s)...", "✂️")
                    success, original_duration, new_duration = trim_silence_from_end(
                        output_path, None, max_silence_sec, threshold_db
                    )
                    if success:
                        log(f"Trimmed silence: {output_filename} ({original_duration:.2f}s → {new_duration:.2f}s)", "✅")
                    else:
                        log(f"Failed to trim silence: {output_filename}", "⚠️")
        else:
            log(f"Failed to generate: {output_filename}", "❌")

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

def process_config(config: dict, args) -> None:
    """Process voice lines for a single configuration."""
    global CONFIG, TTS_PROVIDER, VOICE_SAMPLES, SCENARIOS_DIR, OUTPUT_DIR
    
    CONFIG = config
    
    # Get voice configuration
    voice_config = CONFIG.get('voice', {})
    provider_name = voice_config.get('provider', 'zonos')
    
    # Set up voice samples based on provider
    if provider_name == 'zonos':
        VOICE_SAMPLES = voice_config.get('zonos_settings', {}).get('voice_samples', [])
    elif provider_name == 'orpheus':
        # For Orpheus, voice presets are handled internally by the provider
        VOICE_SAMPLES = []
    else:
        VOICE_SAMPLES = []
    
    # Initialize the TTS provider if not already initialized or if provider changed
    if TTS_PROVIDER is None or TTS_PROVIDER.__class__.__name__ != f"{provider_name.capitalize()}Provider":
        try:
            TTS_PROVIDER = get_tts_provider(voice_config)
            log(f"Initialized TTS provider: {TTS_PROVIDER.__class__.__name__}", "🔊")
        except ValueError as e:
            log(f"Error initializing TTS provider: {str(e)}", "❌")
            return
    
    # Get directory paths
    SCENARIOS_DIR = CONFIG.get('directories', {}).get('scenarios', 'scenarios')
    OUTPUT_DIR = CONFIG.get('directories', {}).get('voice_lines', 'voice_lines')
    
    # Get project name
    project_name = CONFIG.get("project_name")
    
    # Print startup message
    log(f"Starting {project_name} voice line generation...", "🚀")
    log(f"Using TTS provider: {provider_name.upper()}", "🎤")
    
    # Clean output directory if requested
    output_dir_path = os.path.join(PROJECT_DIR, "output", project_name, OUTPUT_DIR)
    if args.clean:
        clean_output_directory()
    else:
        ensure_dir_exists(output_dir_path)
    
    # Get all scenario files
    scenario_files = get_scenario_files()
    log(f"Found {len(scenario_files)} scenario files", "📂")
    
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

def main():
    """Main function to process all scenarios."""
    global CONFIG, TTS_PROVIDER, VOICE_SAMPLES, SCENARIOS_DIR, OUTPUT_DIR
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration(s)
    configs = load_config(args.config)
    
    # Handle both single config and multiple configs cases
    if not isinstance(configs, list):
        configs = [configs]
    
    # Initialize globals
    TTS_PROVIDER = None
    
    # Process each config
    for config in configs:
        process_config(config, args)
    
    log("All voice line generation complete!", "🎉")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("Process interrupted by user (Ctrl+C)", "⚠️")
        log("Exiting gracefully...", "🛑")
        sys.exit(130)  # Standard exit code for SIGINT
