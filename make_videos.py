import os
import sys
import random
import yaml
import argparse
import re
import glob
from datetime import datetime
import difflib
import platform
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip, CompositeAudioClip
from moviepy.config import change_settings
import emoji
from PIL import ImageFont, Image, ImageDraw
import numpy as np

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─────────────────────────────────────────────────────
# 🎲 CONFIGURATION
# ─────────────────────────────────────────────────────
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

# Global variables
CONFIG = None
SCRIPT_DIR = None
SCENARIOS_DIR = None
VIDEOS_DIR = None
MUSIC_DIR = None
VOICE_LINES_DIR = None
OUTPUT_DIR = None
FONTS_DIR = None
EMOJI_FONTS_DIR = None

# ─────────────────────────────────────────────────────
# 📂 DIRECTORIES
# ─────────────────────────────────────────────────────
def update_directories():
    """Update directory paths based on the loaded configuration."""
    global SCRIPT_DIR, SCENARIOS_DIR, VIDEOS_DIR, MUSIC_DIR, VOICE_LINES_DIR, OUTPUT_DIR, FONTS_DIR, EMOJI_FONTS_DIR
    
    # Get project name
    project_name = CONFIG.get("project_name", "DeepVideo2")
    
    # Set script directory
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Input directories (static resources)
    VIDEOS_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["videos_dir"])
    MUSIC_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["music_dir"])
    FONTS_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["fonts_dir"])
    EMOJI_FONTS_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["emoji_fonts_dir"])
    
    # Output directories (project-specific)
    SCENARIOS_DIR = os.path.join(SCRIPT_DIR, "output", project_name, CONFIG["directories"]["scenarios"])
    VOICE_LINES_DIR = os.path.join(SCRIPT_DIR, "output", project_name, CONFIG["directories"]["voice_lines"])
    OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output", project_name, CONFIG["directories"]["output_videos"])
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────
# 🔤 FONT HANDLING
# ─────────────────────────────────────────────────────
# Define emoji-compatible fonts based on the operating system
EMOJI_FONTS = {
    'windows': [
        'Segoe UI Emoji',
        'Segoe UI Symbol',
        'Arial Unicode MS'
    ],
    'darwin': [  # macOS
        'Apple Color Emoji',
        'Arial Unicode MS'
    ],
    'linux': [
        'Noto Color Emoji',
        'DejaVu Sans',
        'FreeSans'
    ]
}

def get_system_emoji_font():
    """Get the best emoji font for the current operating system."""
    system = platform.system().lower()
    if system == 'windows':
        return EMOJI_FONTS['windows'][0]  # Segoe UI Emoji
    elif system == 'darwin':
        return EMOJI_FONTS['darwin'][0]   # Apple Color Emoji
    else:
        return EMOJI_FONTS['linux'][0]    # Noto Color Emoji

def get_random_font():
    """Get a random font from the fonts directory."""
    font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG["directories"]["fonts_dir"])
    if not os.path.exists(font_dir):
        print(f"⚠️ Font directory not found: {font_dir}")
        return None
    
    font_files = []
    for ext in [".ttf", ".otf"]:
        font_files.extend(glob.glob(os.path.join(font_dir, f"*{ext}")))
    
    if not font_files:
        print("⚠️ No font files found in the fonts directory.")
        return None
    
    # Return a random font from the directory
    random_font = random.choice(font_files)
    print(f"🔤 Selected random font: {os.path.basename(random_font)}")
    return random_font

def get_emoji_font():
    """Get a font for emoji rendering from the emoji fonts directory."""
    emoji_font_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG["directories"]["emoji_fonts_dir"])
    if not os.path.exists(emoji_font_dir):
        print(f"⚠️ Emoji font directory not found: {emoji_font_dir}")
        return None
    
    # Look for Noto Color Emoji font first
    noto_fonts = glob.glob(os.path.join(emoji_font_dir, "*Noto*Emoji*.ttf"))
    if noto_fonts:
        noto_font = noto_fonts[0]
        print(f"🔤 Found Noto Emoji font: {os.path.basename(noto_font)}")
        return noto_font
    
    # If no Noto font, try any other emoji font
    emoji_fonts = glob.glob(os.path.join(emoji_font_dir, "*.ttf"))
    if emoji_fonts:
        emoji_font = emoji_fonts[0]
        print(f"🔤 Using emoji font: {os.path.basename(emoji_font)}")
        return emoji_font
    
    # If no emoji fonts found, return None
    print("⚠️ No emoji fonts found in the emoji fonts directory.")
    return None

def extract_emojis(text):
    """Extract emoji characters from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+"
    )
    return "".join(emoji_pattern.findall(text))

def remove_emojis(text):
    """Remove emoji characters from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251" 
        "]+"
    )
    return emoji_pattern.sub('', text)

def resize_video(clip, target_resolution):
    """Resize a video clip to the target resolution while maintaining aspect ratio."""
    # Get the target dimensions
    target_width, target_height = target_resolution
    
    # Calculate the aspect ratios
    clip_aspect = clip.w / clip.h
    target_aspect = target_width / target_height
    
    # Resize and crop to maintain aspect ratio
    if clip_aspect > target_aspect:
        # Video is wider than target, resize based on height
        new_height = target_height
        new_width = int(new_height * clip_aspect)
        resized_clip = clip.resize(height=new_height)
        # Crop the width to match target width
        x_center = resized_clip.w // 2
        x1 = x_center - (target_width // 2)
        final_clip = resized_clip.crop(x1=x1, y1=0, width=target_width, height=target_height)
    else:
        # Video is taller than target, resize based on width
        new_width = target_width
        new_height = int(new_width / clip_aspect)
        resized_clip = clip.resize(width=new_width)
        # Crop the height to match target height
        y_center = resized_clip.h // 2
        y1 = y_center - (target_height // 2)
        final_clip = resized_clip.crop(x1=0, y1=y1, width=target_width, height=target_height)
    
    return final_clip

def find_unprocessed_scenarios():
    """Find all scenarios that haven't been processed yet."""
    # Check if scenarios directory exists
    if not os.path.exists(SCENARIOS_DIR):
        print(f"❌ Scenarios directory not found: {SCENARIOS_DIR}")
        return []
    
    # Get all YAML files in the scenarios directory
    scenario_files = [os.path.join(SCENARIOS_DIR, f) for f in os.listdir(SCENARIOS_DIR) if f.endswith('.yaml')]
    
    # Filter out scenarios that have already been processed
    unprocessed_scenarios = []
    for scenario_path in scenario_files:
        try:
            with open(scenario_path, 'r', encoding='utf-8') as f:
                scenario = yaml.safe_load(f)
                # Check if the scenario has already been processed
                if not scenario.get('has_video', False):
                    unprocessed_scenarios.append(scenario_path)
        except Exception as e:
            print(f"⚠️ Error reading {os.path.basename(scenario_path)}: {str(e)}")
    
    return unprocessed_scenarios

def find_random_scenario():
    """Find a random scenario that hasn't been processed yet."""
    unprocessed_scenarios = find_unprocessed_scenarios()
    
    if not unprocessed_scenarios:
        return None
    
    # Select a random scenario
    return random.choice(unprocessed_scenarios)

def find_best_match(target, options):
    """Find the best matching file from a list of options using fuzzy matching."""
    if not options:
        return None
    
    # Use difflib to find the closest match
    matches = difflib.get_close_matches(target, options, n=1, cutoff=0.6)
    
    if matches:
        return matches[0]
    
    # If no match found, try a more lenient search
    matches = difflib.get_close_matches(target, options, n=1, cutoff=0.1)
    
    if matches:
        print(f"⚠️ Using approximate match for '{target}': '{matches[0]}'")
        return matches[0]
    
    # If still no match found, return the first option as a fallback
    print(f"⚠️ No close match found for '{target}'. Using first available option.")
    return options[0]

def format_text_for_display(text):
    """Format text for better display by breaking at natural points.
    
    This function breaks long sentences into multiple lines at natural break points
    like commas, colons, semicolons, and certain conjunctions to improve readability.
    """
    # Don't process if text is already short
    if len(text) < 30:
        return text
    
    # Break points in order of priority
    primary_break_points = ['. ', '! ', '? ']  # These will split at all occurrences
    secondary_break_points = [
        ': ', '; ', 
        ', ', 
        ' - ', 
        ' but ', ' and ', ' or ', 
        ' because ', ' when ', ' if '
    ]
    
    # First try to split at all periods, question marks, and exclamation points
    for separator in primary_break_points:
        if separator in text:
            parts = text.split(separator)
            # Add the separator back to each part except the last one
            for i in range(len(parts) - 1):
                parts[i] += separator.rstrip()
            # Join with newlines
            return '\n'.join(parts)
    
    # If no primary break points, try secondary ones (only split at first occurrence)
    for separator in secondary_break_points:
        if separator in text:
            parts = text.split(separator, 1)  # Split only on the first occurrence
            # For conjunctions, keep them with the second part
            if separator.strip() in ['but', 'and', 'or', 'because', 'when', 'if']:
                return parts[0] + '\n' + separator.strip() + parts[1]
            else:
                # For punctuation, keep it with the first part
                return parts[0] + separator.rstrip() + '\n' + parts[1]
    
    # If text is still too long and no break points found, just split in the middle
    words = text.split()
    if len(words) > 5:
        middle_idx = len(words) // 2
        return ' '.join(words[:middle_idx]) + '\n' + ' '.join(words[middle_idx:])
    
    # If all else fails, return the original text
    return text

def create_text_clip(text, duration, start_time, video_size, quality=1.0, font=None):
    """Create a text clip with the given text and duration."""
    # Format text for better display
    formatted_text = format_text_for_display(text)
    
    # Extract and remove emojis
    emojis = extract_emojis(formatted_text)
    text_without_emojis = remove_emojis(formatted_text)
    
    # Get font paths
    if font is None:
        regular_font_path = get_random_font()
    else:
        regular_font_path = font
    
    emoji_font_path = get_emoji_font()
    
    if not regular_font_path:
        print("⚠️ Using default font for regular text.")
        regular_font = None
    else:
        print(f"🔤 Using font for regular text: {os.path.basename(regular_font_path)}")
        # Instead of using the path, use just the font name without extension
        font_name = os.path.splitext(os.path.basename(regular_font_path))[0]
        print(f"🔤 Font name for MoviePy: {font_name}")
        regular_font = font_name
    
    # Scale font sizes based on quality
    base_font_size = 90
    main_font_size = int(base_font_size * quality)
    
    # Scale stroke width based on quality
    base_stroke_width = 3
    stroke_width = max(1, int(base_stroke_width * quality))
    
    # Debug font loading
    print(f"📝 Font path: {regular_font_path}")
    
    # Test if the font can be loaded by PIL
    try:
        test_font = ImageFont.truetype(regular_font_path, main_font_size)
        print(f"✅ Font loaded successfully by PIL: {test_font.getname()}")
    except Exception as e:
        print(f"⚠️ PIL couldn't load font: {str(e)}")
    
    # Create the main text clip (without emojis)
    try:
        # For MoviePy on Windows, try using just the font name
        main_txt_clip = TextClip(
            txt=text_without_emojis,
            fontsize=main_font_size,
            color='white',
            font=regular_font,
            align='center',
            method='caption',
            size=(video_size[0] * 0.8, None),
            stroke_color='black',
            stroke_width=stroke_width
        )
        print("✅ Successfully created text clip with specified font")
    except Exception as e:
        print(f"⚠️ Error using font name: {str(e)}. Trying with full path.")
        try:
            # If font name doesn't work, try with full path
            main_txt_clip = TextClip(
                txt=text_without_emojis,
                fontsize=main_font_size,
                color='white',
                font=regular_font_path,  # Try with full path
                align='center',
                method='caption',
                size=(video_size[0] * 0.8, None),
                stroke_color='black',
                stroke_width=stroke_width
            )
            print("✅ Successfully created text clip with font path")
        except Exception as e:
            print(f"⚠️ Error using font path: {str(e)}. Falling back to default.")
            # If all else fails, use default font
            main_txt_clip = TextClip(
                txt=text_without_emojis,
                fontsize=main_font_size,
                color='white',
                font=None,
                align='center',
                method='caption',
                size=(video_size[0] * 0.8, None),
                stroke_color='black',
                stroke_width=stroke_width
            )
    
    # Set position and timing for main text
    main_txt_clip = main_txt_clip.set_position('center')
    main_txt_clip = main_txt_clip.set_start(start_time)
    main_txt_clip = main_txt_clip.set_duration(duration)
    
    # If there are emojis and we have an emoji font, create a separate emoji clip
    if emojis and emoji_font_path:
        print(f"🔤 Rendering emojis separately: {emojis}")
        print(f"🔤 Using emoji font: {os.path.basename(emoji_font_path)}")
        
        emoji_font_size = int(100 * quality)  # Scale emoji font size
        
        emoji_txt_clip = TextClip(
            txt=emojis,
            fontsize=emoji_font_size,  # Scale emoji font size based on quality
            color='white',
            font=emoji_font_path,
            align='center',
            method='label'
        )
        
        # Position emojis at the bottom of the screen
        emoji_txt_clip = emoji_txt_clip.set_position(('center', video_size[1] * 0.85))
        emoji_txt_clip = emoji_txt_clip.set_start(start_time)
        emoji_txt_clip = emoji_txt_clip.set_duration(duration)
        
        # Return both clips as a list
        return [main_txt_clip, emoji_txt_clip]
    
    # If no emojis or no emoji font, just return the main text clip
    return [main_txt_clip]

def generate_video(scenario, scenario_path, vertical=True, quality=1.0):
    """Generate a video from a scenario."""
    print(f"📌 Topic: {scenario['topic']}")
    
    # Get the scenario name (for finding voice lines)
    scenario_name = os.path.splitext(os.path.basename(scenario_path))[0]
    
    # Get the music and video files from scenario
    requested_music = scenario['music']
    requested_video = scenario['video']
    
    # Get all available music and video files
    available_music = os.listdir(MUSIC_DIR)
    available_videos = os.listdir(VIDEOS_DIR)
    
    # Find the best matching files
    music_file = find_best_match(requested_music, available_music)
    video_file = find_best_match(requested_video, available_videos)
    
    print(f"🎵 Using music: {music_file}")
    print(f"🎬 Using video: {video_file}")
    
    # Select a consistent font for this scenario if enabled in config
    use_consistent_font = CONFIG["video"].get("use_consistent_font", True)
    scenario_font = None
    if use_consistent_font:
        scenario_font = get_random_font()
        print(f"🔤 Selected consistent font for scenario: {os.path.basename(scenario_font)}")
    
    # Load the video and audio clips
    video_clip = VideoFileClip(os.path.join(VIDEOS_DIR, video_file))
    music_clip = AudioFileClip(os.path.join(MUSIC_DIR, music_file))
    
    # Determine video orientation
    if vertical:
        print("🔄 Creating vertical (9:16) video for TikTok/Reels...")
        target_resolution = (1080, 1920)  # 9:16 aspect ratio
    else:
        print("🔄 Creating horizontal (16:9) video...")
        target_resolution = (1920, 1080)  # 16:9 aspect ratio
    
    # Apply quality scaling if less than 1.0
    if quality < 1.0:
        print(f"🔍 Rendering at {int(quality * 100)}% quality for faster processing")
        # Scale the target resolution
        target_resolution = (int(target_resolution[0] * quality), int(target_resolution[1] * quality))
        print(f"🔍 Scaled resolution: {target_resolution[0]}x{target_resolution[1]}")
    
    # Resize video to target resolution
    video_clip = resize_video(video_clip, target_resolution)
    
    # Create text clips for each slide
    slides = scenario['slides']
    print(f"📝 Creating {len(slides)} slides")
    
    # Check for voice lines and calculate adjusted durations
    voice_lines_dir = VOICE_LINES_DIR
    
    # Calculate total video duration with adjusted slide durations
    video_duration = 0
    for i, slide in enumerate(slides):
        # Check if voice line exists for this slide
        slide_id = f"slide_{i+1:02d}"
        voice_line_filename = f"{scenario_name}_{slide_id}.wav"
        voice_line_path = os.path.join(voice_lines_dir, voice_line_filename)
        
        if os.path.exists(voice_line_path):
            # Load voice line and set its start time
            try:
                voice_clip = AudioFileClip(voice_line_path)
                # Set volume for voice clip
                voice_clip = voice_clip.volumex(CONFIG["video"].get("voice_narration_volume", 1.0))
                # Set the start time for this voice clip
                voice_clip = voice_clip.set_start(video_duration)
                # Add voice clip to audio clips list
                audio_clips = [music_clip, voice_clip]
                # Add a small buffer (0.5s) to ensure text stays visible after narration
                slide_duration = voice_clip.duration + 0.5
                print(f"🔊 Found voice line for slide {i+1}: {slide_duration:.2f}s")
            except Exception as e:
                print(f"⚠️ Error reading voice line {voice_line_filename}: {str(e)}")
                slide_duration = slide['duration_seconds']
        else:
            # Use original duration from scenario
            slide_duration = slide['duration_seconds']
            print(f"📝 No voice line for slide {i+1}, using original duration: {slide_duration}s")
        
        # Create text clips for this slide using the consistent font if enabled
        text_clips = create_text_clip(slide['text'], slide_duration, video_duration, target_resolution, quality, scenario_font)
        video_duration += slide_duration
    
    # Select a random segment from the video if it's longer than needed
    if video_clip.duration > video_duration:
        max_start_time = video_clip.duration - video_duration
        start_time = random.uniform(0, max_start_time)
        print(f"🎬 Using video segment starting at {start_time:.2f}s")
        video_clip = video_clip.subclip(start_time, start_time + video_duration)
    else:
        # If video is shorter, loop it
        video_clip = video_clip.loop(duration=video_duration)
    
    # Select a random segment from the music if it's longer than needed
    if music_clip.duration > video_duration:
        max_start_time = music_clip.duration - video_duration
        start_time = random.uniform(0, max_start_time)
        print(f"🎵 Using music segment starting at {start_time:.2f}s")
        music_clip = music_clip.subclip(start_time, start_time + video_duration)
    else:
        # If music is shorter, loop it
        music_clip = music_clip.loop(duration=video_duration)
    
    # Set volume levels from config
    background_music_volume = CONFIG["video"].get("background_music_volume", 0.5)
    
    # Adjust music volume
    music_clip = music_clip.volumex(background_music_volume)
    print(f"🔊 Set background music volume to {background_music_volume:.1f}")
    
    # Create a list to hold all clips (video and text)
    all_clips = [video_clip]
    
    # Create a list to hold all audio clips (music and voice lines)
    audio_clips = [music_clip]
    
    # Add text clips and voice lines for each slide
    current_time = 0
    for i, slide in enumerate(slides):
        # Check if voice line exists for this slide
        slide_id = f"slide_{i+1:02d}"
        voice_line_filename = f"{scenario_name}_{slide_id}.wav"
        voice_line_path = os.path.join(voice_lines_dir, voice_line_filename)
        
        if os.path.exists(voice_line_path):
            # Load voice line and set its start time
            try:
                voice_clip = AudioFileClip(voice_line_path)
                # Set volume for voice clip
                voice_clip = voice_clip.volumex(CONFIG["video"].get("voice_narration_volume", 1.0))
                # Set the start time for this voice clip
                voice_clip = voice_clip.set_start(current_time)
                # Add voice clip to audio clips list
                audio_clips.append(voice_clip)
                # Add a small buffer (0.5s) to ensure text stays visible after narration
                slide_duration = voice_clip.duration + 0.5
                print(f"🔊 Found voice line for slide {i+1}: {slide_duration:.2f}s")
            except Exception as e:
                print(f"⚠️ Error reading voice line {voice_line_filename}: {str(e)}")
                slide_duration = slide['duration_seconds']
        else:
            # Use original duration from scenario
            slide_duration = slide['duration_seconds']
            print(f"📝 No voice line for slide {i+1}, using original duration: {slide_duration}s")
        
        # Create text clips for this slide using the consistent font if enabled
        text_clips = create_text_clip(slide['text'], slide_duration, current_time, target_resolution, quality, scenario_font)
        all_clips.extend(text_clips)
        
        # Update current time
        current_time += slide_duration
    
    # Compose the final video
    final_clip = CompositeVideoClip(all_clips)
    
    # Combine all audio tracks
    if len(audio_clips) > 1:
        print(f"🔊 Combining {len(audio_clips)} audio tracks ({len(audio_clips)-1} voice lines)")
        final_audio = CompositeAudioClip(audio_clips)
        final_clip = final_clip.set_audio(final_audio)
    else:
        # Just use the music if no voice lines
        final_clip = final_clip.set_audio(music_clip)
    
    # Create the output filename
    output_filename = os.path.splitext(os.path.basename(scenario_path))[0] + '.mp4'
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Render the video
    print(f"🔄 Rendering video to {output_path}...")
    final_clip.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
    
    # Close the clips to free up resources
    video_clip.close()
    music_clip.close()
    
    # Close any voice clips
    for clip in audio_clips:
        if clip != music_clip:  # Avoid closing music_clip twice
            clip.close()
    
    final_clip.close()
    
    print(f"✅ Video created successfully: {output_path}")
    
    return output_path

def process_scenario(scenario_path, vertical=True, force=False, quality=1.0):
    """Process a scenario file and generate a video.
    
    Args:
        scenario_path: Path to the scenario file
        vertical: Whether to generate a vertical video (9:16 aspect ratio)
        force: Whether to process the scenario even if it has already been processed
        quality: Quality factor for rendering (1.0 = full quality, 0.5 = half resolution)
    """
    try:
        with open(scenario_path, 'r', encoding='utf-8') as file:
            scenario = yaml.safe_load(file)
        
        print(f"📌 Topic: {scenario['topic']}")
        
        # Check if the scenario has already been processed
        if not force and scenario.get('has_video', False):
            print(f"⚠️ Scenario has already been processed: {scenario_path}")
            print(f"   Use -f to process it anyway.")
            return False
        
        # Generate the video
        output_path = generate_video(scenario, scenario_path, vertical, quality)
        
        if output_path:
            # Mark the scenario as processed
            scenario['has_video'] = True
            with open(scenario_path, 'w', encoding='utf-8') as file:
                yaml.dump(scenario, file, default_flow_style=False)
            print(f"✅ Scenario marked as processed: {scenario_path}")
            print(f"🎉 Video generation complete: {output_path}")
            return True
        else:
            print(f"❌ Failed to generate video for {scenario_path}")
            return False
    except Exception as e:
        print(f"❌ Error processing scenario {scenario_path}: {str(e)}")
        return False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate videos from scenario files.')
    parser.add_argument('-c', '--config', type=str, required=True,
                        help='Path to the configuration file')
    parser.add_argument('-n', '--num-videos', type=int, default=-1, 
                        help='Number of videos to generate. Use -1 (default) to process all available unprocessed scenarios.')
    parser.add_argument('--horizontal', action='store_true', 
                        help='Generate horizontal (16:9) videos instead of vertical (9:16).')
    parser.add_argument('-s', '--scenario', type=str, help='Path to a specific scenario file to process')
    parser.add_argument('-f', '--force', action='store_true',
                        help='Force processing of a scenario even if it has already been processed')
    parser.add_argument('-q', '--quality', type=float, default=1.0,
                        help='Quality factor for rendering (1.0 = full quality, 0.5 = half resolution)')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
    # Load configuration from specified file
    global CONFIG
    CONFIG = load_config(args.config)
    
    # Configure MoviePy to use ImageMagick
    change_settings({"IMAGEMAGICK_BINARY": CONFIG["video"]["imagemagick_binary"]})
    
    # Fix for PIL.Image.ANTIALIAS deprecation
    try:
        import PIL
        if not hasattr(PIL.Image, 'ANTIALIAS'):
            # For newer versions of Pillow, ANTIALIAS is renamed to LANCZOS
            PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
    except (ImportError, AttributeError):
        pass
    
    # Update directory paths
    update_directories()
    
    # Get project name
    project_name = CONFIG.get("project_name")
    
    print(f"\n🚀 Starting {project_name} video generation")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Determine if we should generate horizontal videos (vertical is now default)
    vertical = not args.horizontal
    
    if args.scenario:
        # Process a specific scenario
        scenario_path = args.scenario
        if not os.path.exists(scenario_path):
            print(f"❌ Scenario file not found: {scenario_path}")
            return
        
        # Process the scenario, with force flag if specified
        success = process_scenario(scenario_path, vertical, args.force, args.quality)
        
        if success:
            print(f"🎉 Video generation complete: {scenario_path}")
    else:
        # Process the specified number of videos
        videos_generated = 0
        max_videos = args.num_videos
        
        # If max_videos is -1, process all unprocessed scenarios
        if max_videos == -1:
            unprocessed_scenarios = find_unprocessed_scenarios()
            if not unprocessed_scenarios:
                print("🏁 No unprocessed scenarios available.")
                return
            
            print(f"🎯 Found {len(unprocessed_scenarios)} unprocessed scenarios")
            
            for scenario_path in unprocessed_scenarios:
                print(f"🎯 Processing scenario: {os.path.basename(scenario_path)}")
                
                # Process the scenario
                success = process_scenario(scenario_path, vertical, quality=args.quality)
                
                if success:
                    videos_generated += 1
                    print(f"📊 Progress: {videos_generated}/{len(unprocessed_scenarios)} videos generated")
            
            if videos_generated > 0:
                print(f"✅ Successfully generated {videos_generated} videos.")
            else:
                print("❌ No videos were generated.")
        else:
            # Process a specific number of random scenarios
            while True:
                # Check if we've generated the requested number of videos
                if max_videos > 0 and videos_generated >= max_videos:
                    break
                
                # Find a random scenario that hasn't been processed
                scenario_path = find_random_scenario()
                
                # If no more scenarios to process, break
                if not scenario_path:
                    print("🏁 No more unprocessed scenarios available.")
                    break
                
                print(f"🎯 Selected scenario: {os.path.basename(scenario_path)}")
                
                # Process the scenario
                success = process_scenario(scenario_path, vertical, quality=args.quality)
                
                if success:
                    videos_generated += 1
                    print(f"📊 Progress: {videos_generated}/{max_videos if max_videos > 0 else 'all'} videos generated")
            
            if videos_generated > 0:
                print(f"✅ Successfully generated {videos_generated} videos.")
            else:
                print("❌ No videos were generated.")

if __name__ == "__main__":
    main()
