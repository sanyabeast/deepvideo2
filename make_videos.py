import os
import sys
import yaml
import random
import difflib
import re
import glob
import platform
from datetime import datetime
import argparse
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip, CompositeAudioClip, ImageClip
from moviepy.config import change_settings
import emoji
from PIL import ImageFont, Image, ImageDraw
import numpy as np
from pilmoji import Pilmoji
import cv2

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
SCRIPT_DIR = None
SCENARIOS_DIR = None
VIDEOS_DIR = None
MUSIC_DIR = None
VOICE_LINES_DIR = None
OUTPUT_DIR = None
IMAGES_DIR = None
FONTS_DIR = None
EMOJI_FONTS_DIR = None

# ─────────────────────────────────────────────────────
# 📂 DIRECTORIES
# ─────────────────────────────────────────────────────
def update_directories():
    """Update directory paths based on the loaded configuration."""
    global SCRIPT_DIR, SCENARIOS_DIR, VIDEOS_DIR, MUSIC_DIR, VOICE_LINES_DIR, OUTPUT_DIR, IMAGES_DIR, FONTS_DIR, EMOJI_FONTS_DIR
    
    # Get project name
    project_name = CONFIG.get("project_name", "DeepVideo2")
    
    # Input directories (shared across projects)
    SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
    VIDEOS_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["videos_dir"])
    MUSIC_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["music_dir"])
    FONTS_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["fonts_dir"])
    EMOJI_FONTS_DIR = os.path.join(SCRIPT_DIR, CONFIG["directories"]["emoji_fonts_dir"])
    
    # Output directories (project-specific)
    SCENARIOS_DIR = os.path.join(SCRIPT_DIR, "output", project_name, CONFIG["directories"]["scenarios"])
    VOICE_LINES_DIR = os.path.join(SCRIPT_DIR, "output", project_name, CONFIG["directories"]["voice_lines"])
    OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output", project_name, CONFIG["directories"]["output_videos"])
    
    # Images directory (might not be in CONFIG["directories"])
    if "images" in CONFIG["directories"]:
        images_dir = CONFIG["directories"]["images"]
    else:
        images_dir = "images"  # Default value
        log(f"'images' not found in config directories, using default: {images_dir}", "⚠️")
    
    IMAGES_DIR = os.path.join(SCRIPT_DIR, "output", project_name, images_dir)
    
    # Create output directories if they don't exist
    os.makedirs(SCENARIOS_DIR, exist_ok=True)
    os.makedirs(VOICE_LINES_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    log(f"Project: {project_name}", "📂")
    log(f"Scenarios directory: {SCENARIOS_DIR}", "📂")
    log(f"Voice lines directory: {VOICE_LINES_DIR}", "📂")
    log(f"Output videos directory: {OUTPUT_DIR}", "📂")
    log(f"Images directory: {IMAGES_DIR}", "📂")

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
        log(f"Font directory not found: {font_dir}", "⚠️")
        return None
    
    font_files = []
    for ext in [".ttf", ".otf"]:
        font_files.extend(glob.glob(os.path.join(font_dir, f"*{ext}")))
    
    if not font_files:
        log("No font files found in the fonts directory.", "⚠️")
        return None
    
    # Return a random font from the directory
    random_font = random.choice(font_files)
    log(f"Selected random font: {os.path.basename(random_font)}", "🔤")
    return random_font

def get_emoji_font():
    """Get a font for emoji rendering."""
    # Use emoji font path from config if available, otherwise use default
    if CONFIG and "video" in CONFIG and "emoji" in CONFIG["video"] and "font" in CONFIG["video"]["emoji"]:
        emoji_font_path = os.path.join(PROJECT_DIR, CONFIG["video"]["emoji"]["font"])
        log(f"Using emoji font from config: {CONFIG['video']['emoji']['font']}", "🔤")
    else:
        # Fallback to default path
        emoji_font_path = os.path.join(PROJECT_DIR, "lib", "noto_sans_emoji.ttf")
        log(f"Using default emoji font: lib/noto_sans_emoji.ttf", "🔤")
    
    if not os.path.exists(emoji_font_path):
        log(f"Emoji font not found at: {emoji_font_path}", "⚠️")
        return None
    
    log(f"Emoji font path: {emoji_font_path}", "🔤")
    return emoji_font_path

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
        log(f"Scenarios directory not found: {SCENARIOS_DIR}", "❌")
        return []
    
    # Get all YAML files in the scenarios directory
    scenario_files = [os.path.join(SCENARIOS_DIR, f) for f in os.listdir(SCENARIOS_DIR) if f.endswith('.yaml')]
    
    # Filter out scenarios that have already been processed
    unprocessed_scenarios = []
    for scenario_path in scenario_files:
        try:
            with open(scenario_path, 'r', encoding='utf-8') as f:
                scenario = yaml.safe_load(f)
                
                # Get the output video path
                scenario_name = os.path.splitext(os.path.basename(scenario_path))[0]
                output_path = os.path.join(OUTPUT_DIR, f"{scenario_name}.mp4")
                
                # Check if the video file already exists
                if not os.path.exists(output_path):
                    unprocessed_scenarios.append(scenario_path)
        except Exception as e:
            log(f"Error reading {os.path.basename(scenario_path)}: {str(e)}", "⚠️")
    
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
        log(f"Using approximate match for '{target}': '{matches[0]}'", "⚠️")
        return matches[0]
    
    # If still no match found, return the first option as a fallback
    log(f"No close match found for '{target}'. Using first available option.", "⚠️")
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
                return parts[0] + '\n' + separator + parts[1]
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

def create_text_clip(text, duration, start_time, video_size, quality=1.0, font=None, slide_emoji=None):
    """Create a text clip with the given text and duration."""
    # Format text for better display
    formatted_text = format_text_for_display(text)
    
    # Check if emoji rendering is enabled in config (default to true if not specified)
    emoji_enabled = True
    if CONFIG and "video" in CONFIG and "emoji" in CONFIG["video"] and "enabled" in CONFIG["video"]["emoji"]:
        emoji_enabled = bool(CONFIG["video"]["emoji"]["enabled"])
    
    # If emoji rendering is disabled, clear the slide emoji
    if not emoji_enabled:
        slide_emoji = None
        log("Emoji rendering is disabled in config", "🚫")
    
    # Extract and remove emojis from the text itself (only if emoji rendering is enabled)
    if emoji_enabled:
        emojis = extract_emojis(formatted_text)
        text_without_emojis = remove_emojis(formatted_text)
    else:
        emojis = None
        text_without_emojis = formatted_text
    
    # Get font paths
    if font is None:
        regular_font_path = get_random_font()
    else:
        regular_font_path = font
    
    emoji_font_path = get_emoji_font() if emoji_enabled else None
    
    if not regular_font_path:
        log("Using default font for regular text.", "⚠️")
        regular_font = None
    else:
        log(f"Using font for regular text: {os.path.basename(regular_font_path)}", "🔤")
        # Instead of using the path, use just the font name without extension
        font_name = os.path.splitext(os.path.basename(regular_font_path))[0]
        log(f"Font name for MoviePy: {font_name}", "🔤")
        regular_font = font_name
    
    # Scale font sizes based on quality
    base_font_size = 90
    main_font_size = int(base_font_size * quality)
    
    # Scale stroke width based on quality
    base_stroke_width = 3
    stroke_width = max(1, int(base_stroke_width * quality))
    
    # Debug font loading
    log(f"Font path: {regular_font_path}", "📝")
    
    # Test if the font can be loaded by PIL
    try:
        test_font = ImageFont.truetype(regular_font_path, main_font_size)
        log(f"Font loaded successfully by PIL: {test_font.getname()}", "✅")
    except Exception as e:
        log(f"PIL couldn't load font: {str(e)}", "⚠️")
    
    # Create the main text clip (without emojis)
    try:
        # For MoviePy on Windows, try using just the font name
        main_txt_clip = TextClip(
            txt=text_without_emojis,
            fontsize=main_font_size,
            color='white',
            font=regular_font,
            align='center',
            method='label',  # Changed from 'caption' to 'label' to respect line breaks
            size=(video_size[0] * 0.8, None),
            stroke_color='black',
            stroke_width=stroke_width
        )
        log("Successfully created text clip with specified font", "✅")
    except Exception as e:
        log(f"Error using font name: {str(e)}. Trying with full path.", "⚠️")
        try:
            # If font name doesn't work, try with full path
            main_txt_clip = TextClip(
                txt=text_without_emojis,
                fontsize=main_font_size,
                color='white',
                font=regular_font_path,  # Try with full path
                align='center',
                method='label',  # Changed from 'caption' to 'label' to respect line breaks
                size=(video_size[0] * 0.8, None),
                stroke_color='black',
                stroke_width=stroke_width
            )
            log("Successfully created text clip with font path", "✅")
        except Exception as e:
            log(f"Error using font path: {str(e)}. Falling back to default.", "⚠️")
            # If all else fails, use default font
            main_txt_clip = TextClip(
                txt=text_without_emojis,
                fontsize=main_font_size,
                color='white',
                font=None,
                align='center',
                method='label',  # Changed from 'caption' to 'label' to respect line breaks
                size=(video_size[0] * 0.8, None),
                stroke_color='black',
                stroke_width=stroke_width
            )
    
    # Set position and timing for main text
    main_txt_clip = main_txt_clip.set_position('center')
    main_txt_clip = main_txt_clip.set_start(start_time)
    main_txt_clip = main_txt_clip.set_duration(duration)
    
    # Create a list to hold all text clips
    text_clips = [main_txt_clip]
    
    # If emoji rendering is disabled, return only the main text clip
    if not emoji_enabled:
        return text_clips
    
    # Get emoji scale factor from config (default to 1.5 if not specified)
    emoji_scale = 1.5
    if CONFIG and "video" in CONFIG and "emoji" in CONFIG["video"] and "scale" in CONFIG["video"]["emoji"]:
        emoji_scale = float(CONFIG["video"]["emoji"]["scale"])
        log(f"Using emoji scale from config: {emoji_scale}", "🔍")
    
    # Get emoji rotation settings from config
    rotation_enabled = False
    min_angle = -30
    max_angle = 30
    
    if CONFIG and "video" in CONFIG and "emoji" in CONFIG["video"] and "rotation" in CONFIG["video"]["emoji"]:
        rotation_config = CONFIG["video"]["emoji"]["rotation"]
        if isinstance(rotation_config, dict):
            if "enabled" in rotation_config:
                rotation_enabled = bool(rotation_config["enabled"])
            if "min_angle" in rotation_config:
                min_angle = float(rotation_config["min_angle"])
            if "max_angle" in rotation_config:
                max_angle = float(rotation_config["max_angle"])
    
    log(f"Emoji rotation: {'enabled' if rotation_enabled else 'disabled'} (range: {min_angle}° to {max_angle}°)", "🔄")
    
    # If there's a slide emoji and we have an emoji font, create a separate emoji clip using Pilmoji
    if slide_emoji and emoji_font_path:
        log(f"Rendering slide emoji: '{slide_emoji}'", "🔤")
        log(f"Using emoji font: {os.path.basename(emoji_font_path)}", "🔤")
        
        # Apply emoji scale factor to the base size (increased by 50% at scale 1.0)
        base_emoji_size = 150  # Increased from 100 to 150 (50% larger)
        emoji_font_size = int(base_emoji_size * quality * emoji_scale)
        log(f"Emoji font size: {emoji_font_size} (scale: {emoji_scale})", "📏")
        
        # Generate random rotation angle if enabled
        rotation_angle = None
        if rotation_enabled:
            rotation_angle = random.uniform(min_angle, max_angle)
            log(f"Random rotation angle: {rotation_angle:.1f}°", "🔄")
        
        # Create emoji image using Pilmoji
        emoji_image = create_emoji_image(slide_emoji, emoji_font_path, emoji_font_size, rotation_angle)
        
        if emoji_image is not None:
            # Create an ImageClip from the emoji image
            slide_emoji_clip = ImageClip(emoji_image, transparent=True)
            
            # Randomly choose top or bottom position (50/50 chance)
            position_type = random.choice(['top', 'bottom'])
            slide_emoji_clip = slide_emoji_clip.set_position(get_random_position(position_type, video_size))
            slide_emoji_clip = slide_emoji_clip.set_start(start_time)
            slide_emoji_clip = slide_emoji_clip.set_duration(duration)
            
            # Add to text clips list
            text_clips.append(slide_emoji_clip)
        else:
            log(f"Failed to create emoji image for '{slide_emoji}'", "⚠️")
    
    # If there are emojis in the text itself and we have an emoji font, create a separate emoji clip
    if emojis and emoji_font_path:
        log(f"Rendering text emojis: '{emojis}'", "🔤")
        log(f"Using emoji font: {os.path.basename(emoji_font_path)}", "🔤")
        
        # Apply emoji scale factor to the base size (increased by 50% at scale 1.0)
        base_emoji_size = 120  # Increased from 80 to 120 (50% larger)
        emoji_font_size = int(base_emoji_size * quality * emoji_scale)
        
        # Generate random rotation angle if enabled
        rotation_angle = None
        if rotation_enabled:
            rotation_angle = random.uniform(min_angle, max_angle)
            log(f"Random rotation angle for text emoji: {rotation_angle:.1f}°", "🔄")
        
        # Create emoji image using Pilmoji
        emoji_image = create_emoji_image(emojis, emoji_font_path, emoji_font_size, rotation_angle)
        
        if emoji_image is not None:
            # Create an ImageClip from the emoji image
            emoji_txt_clip = ImageClip(emoji_image, transparent=True)
            
            # Randomly choose position at top-right or bottom-right
            position_type = random.choice(['top', 'bottom'])
            if position_type == 'top':
                # Position at top-right
                emoji_txt_clip = emoji_txt_clip.set_position((video_size[0] * 0.75, video_size[1] * 0.2))
            else:
                # Position at bottom-right
                emoji_txt_clip = emoji_txt_clip.set_position((video_size[0] * 0.75, video_size[1] * 0.8))
            
            emoji_txt_clip = emoji_txt_clip.set_start(start_time)
            emoji_txt_clip = emoji_txt_clip.set_duration(duration)
            
            # Add to text clips list
            text_clips.append(emoji_txt_clip)
        else:
            log(f"Failed to create emoji image for '{emojis}'", "⚠️")
    
    # Return all clips as a list
    return text_clips

def create_emoji_image(emoji_text, font_path, font_size, rotation_angle=None):
    """Create an image with colorful emoji using Pilmoji.
    
    Args:
        emoji_text: The emoji text to render (can be Unicode escape sequence like "\U0001F603")
        font_path: Path to the emoji font file
        font_size: Font size for the emoji
        rotation_angle: Optional angle in degrees to rotate the emoji
        
    Returns:
        numpy array of the rendered emoji image with transparency
    """
    if not emoji_text or not font_path:
        log(f"Cannot create emoji image: {'No emoji text' if not emoji_text else 'No font path'}", "⚠️")
        return None
    
    try:
        log(f"Creating emoji image for: '{emoji_text}' (type: {type(emoji_text).__name__})", "🔍")
        
        # Convert Unicode escape sequences to actual emoji characters if needed
        # This handles cases where emoji is stored as "\U0001F603" in YAML
        if isinstance(emoji_text, str) and ('\\U' in emoji_text or '\\u' in emoji_text):
            try:
                decoded_emoji = emoji_text.encode().decode('unicode_escape')
                log(f"Decoded Unicode escape sequence: '{emoji_text}' → '{decoded_emoji}'", "🔄")
                emoji_text = decoded_emoji
            except Exception as e:
                log(f"Error decoding Unicode escape sequence: {str(e)}", "⚠️")
        
        # Verify the emoji font exists
        if not os.path.exists(font_path):
            log(f"Emoji font not found: {font_path}", "⚠️")
            return None
            
        log(f"Loading emoji font: {os.path.basename(font_path)}", "🔤")
        emoji_font = ImageFont.truetype(font_path, font_size)
        
        # Create a larger canvas to ensure emoji fits, especially when rotated
        padding_factor = 1.5  # Extra padding for rotation
        canvas_size = (int(font_size * 3 * padding_factor), int(font_size * 3 * padding_factor))
        log(f"Creating canvas of size: {canvas_size}", "🖼️")
        
        # Create a transparent image
        image = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        
        # Use Pilmoji to render the emoji with color
        with Pilmoji(image) as pilmoji:
            # Calculate position to center the emoji
            try:
                text_width, text_height = emoji_font.getsize(emoji_text)
                position = ((canvas_size[0] - text_width) // 2, (canvas_size[1] - text_height) // 2)
                log(f"Emoji size: {text_width}x{text_height}, Position: {position}", "📐")
            except Exception as e:
                log(f"Error calculating text size: {str(e)}", "⚠️")
                position = (canvas_size[0] // 4, canvas_size[1] // 4)
            
            # Draw the emoji with white color
            log(f"Drawing emoji with Pilmoji", "🖌️")
            pilmoji.text(position, emoji_text, (255, 255, 255), emoji_font)
        
        # Apply rotation if specified
        if rotation_angle is not None and rotation_angle != 0:
            log(f"Rotating emoji by {rotation_angle} degrees", "🔄")
            # Use BICUBIC for smoother rotation
            image = image.rotate(rotation_angle, resample=Image.BICUBIC, expand=True)
        
        # Trim transparent edges
        bbox = image.getbbox()
        if bbox:
            log(f"Cropping image to bbox: {bbox}", "✂️")
            image = image.crop(bbox)
            log(f"Final image size: {image.size}", "🖼️")
        else:
            log("No bounding box found (image might be empty)", "⚠️")
        
        # Save a debug copy of the emoji image
        temp_dir = os.path.join(PROJECT_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        debug_path = os.path.join(temp_dir, f"emoji_debug_{hash(emoji_text)}.png")
        image.save(debug_path)
        log(f"Saved emoji image to: {debug_path}", "💾")
        
        # Convert to numpy array for MoviePy
        return np.array(image)
    except Exception as e:
        log(f"Error creating emoji image: {str(e)}", "❌")
        import traceback
        traceback.print_exc()
        return None

def get_random_position(position_type, video_size):
    """Get a random position for an emoji based on the position type.
    
    Args:
        position_type: Either 'top' or 'bottom'
        video_size: Tuple of (width, height) of the video
        
    Returns:
        Tuple of (x, y) position for the emoji
    """
    width, height = video_size
    
    # Define horizontal position range with more center bias (avoid edges)
    # Instead of fixed positions, use a range with padding from edges
    edge_padding = width * 0.25  # 25% padding from edges
    x_pos = random.uniform(edge_padding, width - edge_padding)
    
    # Set vertical position based on position_type with more proximity to text
    if position_type == 'top':
        # Position in top third, but closer to the text (center)
        y_pos = random.uniform(height * 0.15, height * 0.3)
    else:  # bottom
        # Position in bottom third, but closer to the text (center)
        y_pos = random.uniform(height * 0.7, height * 0.85)
    
    position_name = f"{position_type}-{'left' if x_pos < width/3 else 'center' if x_pos < 2*width/3 else 'right'}"
    log(f"Positioning emoji at {position_name}: ({x_pos:.0f}, {y_pos:.0f})", "📍")
    return (x_pos, y_pos)

def generate_video(scenario, scenario_path, vertical=True, quality=1.0, use_voice_lines=True):
    """Generate a video from a scenario."""
    log(f"Topic: {scenario['topic']}", "📌")
    
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
    
    log(f"Using music: {music_file}", "🎵")
    log(f"Using video: {video_file}", "🎬")
    
    # Select a consistent font for this scenario if enabled in config
    use_consistent_font = CONFIG["video"].get("use_consistent_font", True)
    scenario_font = None
    if use_consistent_font:
        scenario_font = get_random_font()
        log(f"Selected consistent font for scenario: {os.path.basename(scenario_font)}", "🔤")
    
    # Load the video and audio clips
    video_clip = VideoFileClip(os.path.join(VIDEOS_DIR, video_file))
    music_clip = AudioFileClip(os.path.join(MUSIC_DIR, music_file))
    
    # Determine video orientation
    if vertical:
        log("Creating vertical (9:16) video for TikTok/Reels...", "🔄")
        target_resolution = (1080, 1920)  # 9:16 aspect ratio
    else:
        log("Creating horizontal (16:9) video...", "🔄")
        target_resolution = (1920, 1080)  # 16:9 aspect ratio
    
    # Apply quality scaling if less than 1.0
    if quality < 1.0:
        log(f"Rendering at {int(quality * 100)}% quality for faster processing", "🔍")
        # Scale the target resolution
        target_resolution = (int(target_resolution[0] * quality), int(target_resolution[1] * quality))
        log(f"Scaled resolution: {target_resolution[0]}x{target_resolution[1]}", "🔍")
    
    # Resize video to target resolution
    video_clip = resize_video(video_clip, target_resolution)
    
    # Create text clips for each slide
    slides = scenario['slides']
    log(f"Creating {len(slides)} slides", "📝")
    
    # Check for voice lines and calculate adjusted durations
    voice_lines_dir = VOICE_LINES_DIR
    
    # Calculate total video duration with adjusted slide durations
    content_duration = 0
    
    # Get intro and outro delays from config (default to 1.0 second for intro and 2.0 seconds for outro if not specified)
    intro_delay = CONFIG["video"].get("intro_delay", 1.0)
    outro_delay = CONFIG["video"].get("outro_delay", 2.0)
    
    # Calculate content duration (without intro/outro delays)
    for i, slide in enumerate(slides):
        # Check if voice line exists for this slide
        slide_id = f"slide_{i+1:02d}"
        voice_line_filename = f"{scenario_name}_{slide_id}.wav"
        voice_line_path = os.path.join(voice_lines_dir, voice_line_filename)
        
        if use_voice_lines and os.path.exists(voice_line_path):
            # Load voice line and set its start time
            try:
                voice_clip = AudioFileClip(voice_line_path)
                # Add a configurable delay after narration to ensure text stays visible
                voice_line_delay = CONFIG["video"].get("voice_line_delay", 0.5)
                slide_duration = voice_clip.duration + voice_line_delay
                log(f"Found voice line for slide {i+1}: {slide_duration:.2f}s (delay: {voice_line_delay:.1f}s)", "🔊")
            except Exception as e:
                log(f"Error reading voice line {voice_line_filename}: {str(e)}", "⚠️")
                slide_duration = slide['duration_seconds']
        else:
            # Use original duration from scenario
            slide_duration = slide['duration_seconds']
            log(f"No voice line for slide {i+1}, using original duration: {slide_duration}s", "📝")
        
        # Add slide duration to content duration
        content_duration += slide_duration
    
    # Calculate total video duration including intro and outro delays
    total_duration = content_duration + intro_delay + outro_delay
    log(f"Content duration: {content_duration:.2f}s", "⏱️")
    log(f"Adding intro delay: {intro_delay:.1f}s", "⏱️")
    log(f"Adding outro delay: {outro_delay:.1f}s", "⏱️")
    log(f"Total video duration: {total_duration:.2f}s", "⏱️")
    
    # Select a random segment from the video if it's longer than needed
    if video_clip.duration > total_duration:
        max_start_time = video_clip.duration - total_duration
        start_time = random.uniform(0, max_start_time)
        log(f"Using video segment starting at {start_time:.2f}s", "🎬")
        video_clip = video_clip.subclip(start_time, start_time + total_duration)
    else:
        # If video is shorter, loop it
        video_clip = video_clip.loop(duration=total_duration)
        log(f"Looping video to reach {total_duration:.2f}s duration", "🔄")
    
    # Select a random segment from the music if it's longer than needed
    if music_clip.duration > total_duration:
        max_start_time = music_clip.duration - total_duration
        start_time = random.uniform(0, max_start_time)
        log(f"Using music segment starting at {start_time:.2f}s", "🎵")
        music_clip = music_clip.subclip(start_time, start_time + total_duration)
    else:
        # If music is shorter, loop it
        music_clip = music_clip.loop(duration=total_duration)
        log(f"Looping music to reach {total_duration:.2f}s duration", "🔄")
    
    # Set volume levels from config
    background_music_volume = CONFIG["video"].get("background_music_volume", 0.5)
    
    # Adjust music volume
    music_clip = music_clip.volumex(background_music_volume)
    log(f"Set background music volume to {background_music_volume:.1f}", "🔊")
    
    # Create a list to hold all clips (video and text)
    all_clips = [video_clip]
    
    # Create a list to hold all audio clips (music and voice lines)
    audio_clips = [music_clip]
    
    # Add text clips and voice lines for each slide
    current_time = intro_delay  # Start after intro delay
    for i, slide in enumerate(slides):
        # Check if voice line exists for this slide
        slide_id = f"slide_{i+1:02d}"
        voice_line_filename = f"{scenario_name}_{slide_id}.wav"
        voice_line_path = os.path.join(voice_lines_dir, voice_line_filename)
        
        if use_voice_lines and os.path.exists(voice_line_path):
            # Load voice line and set its start time
            try:
                voice_clip = AudioFileClip(voice_line_path)
                # Trim 0.05 seconds from the end to prevent clicking artifacts
                if voice_clip.duration > 0.1:  # Only trim if clip is long enough
                    voice_clip = voice_clip.subclip(0, voice_clip.duration - 0.05)
                # Set volume for voice clip
                voice_clip = voice_clip.volumex(CONFIG["video"].get("voice_narration_volume", 1.0))
                # Set the start time for this voice clip
                voice_clip = voice_clip.set_start(current_time)
                # Add voice clip to audio clips list
                audio_clips.append(voice_clip)
                # Add a configurable delay after narration to ensure text stays visible
                voice_line_delay = CONFIG["video"].get("voice_line_delay", 0.5)
                slide_duration = voice_clip.duration + voice_line_delay
                log(f"Using voice line for slide {i+1}: {slide_duration:.2f}s starting at {current_time:.2f}s (delay: {voice_line_delay:.1f}s)", "🔊")
            except Exception as e:
                log(f"Error reading voice line {voice_line_filename}: {str(e)}", "⚠️")
                slide_duration = slide['duration_seconds']
        else:
            # Use original duration from scenario
            slide_duration = slide['duration_seconds']
            log(f"No voice line for slide {i+1}, using original duration: {slide_duration}s", "📝")
        
        # Check if there's a generated image for this slide
        image_filename = f"{scenario_name}_slide_{i+1}.png"
        image_path = os.path.join(IMAGES_DIR, image_filename)
        
        if os.path.exists(image_path):
            try:
                # Load the image
                log(f"Found image for slide {i+1}: {image_filename}", "🖼️")
                image = Image.open(image_path)
                
                # Create an ImageClip from the image
                image_clip = ImageClip(np.array(image))
                
                # Resize the image based on video orientation
                if vertical:
                    # For vertical videos (9:16), resize the image to cover the entire frame
                    # First, get the aspect ratios
                    video_aspect = target_resolution[0] / target_resolution[1]  # width / height
                    image_aspect = image_clip.size[0] / image_clip.size[1]
                    
                    if image_aspect > video_aspect:
                        # Image is wider than the video frame (relative to height)
                        # Resize based on height to ensure full height coverage
                        image_clip = image_clip.resize(height=target_resolution[1])
                        log(f"Resizing image to cover full height: {target_resolution[1]}px", "🔍")
                    else:
                        # Image is taller than the video frame (relative to width)
                        # Resize based on width to ensure full width coverage
                        image_clip = image_clip.resize(width=target_resolution[0])
                        log(f"Resizing image to cover full width: {target_resolution[0]}px", "🔍")
                else:
                    # For horizontal videos (16:9), resize to 100% of the height
                    image_clip = image_clip.resize(height=target_resolution[1])
                    log(f"Resizing image to fit horizontal video height: {target_resolution[1]}px", "🔍")
                
                # Create a background clip that's exactly the size of the video frame
                bg_clip = ColorClip(
                    size=target_resolution,
                    color=(0, 0, 0),
                    duration=slide_duration
                ).set_opacity(0.5).set_start(current_time)
                
                # Add the background clip first
                all_clips.append(bg_clip)
                log(f"Added full-frame black background for image", "🎨")
                
                # Center the image in the frame
                image_clip = image_clip.set_position(('center', 'center'))
                
                # Set the duration and start time
                image_clip = image_clip.set_duration(slide_duration).set_start(current_time)
                
                # Add the image clip to the list of clips
                all_clips.append(image_clip)
                
                log(f"Added image for slide {i+1} with duration {slide_duration:.2f}s starting at {current_time:.2f}s", "🖼️")
            except Exception as e:
                log(f"Error adding image for slide {i+1}: {str(e)}", "⚠️")
                import traceback
                traceback.print_exc()
        
        # Create text clips for this slide using the consistent font if enabled
        text_clips = create_text_clip(slide['text'], slide_duration, current_time, target_resolution, quality, scenario_font, slide.get('emoji'))
        all_clips.extend(text_clips)
        
        # Update current time
        current_time += slide_duration
    
    # Compose the final video
    final_clip = CompositeVideoClip(all_clips, size=target_resolution)
    
    # Combine all audio tracks
    if len(audio_clips) > 1:
        log(f"Combining {len(audio_clips)} audio tracks ({len(audio_clips)-1} voice lines)", "🔊")
        final_audio = CompositeAudioClip(audio_clips)
        final_clip = final_clip.set_audio(final_audio)
    else:
        # Just use the music if no voice lines
        final_clip = final_clip.set_audio(music_clip)
    
    # Create the output filename
    output_filename = os.path.splitext(os.path.basename(scenario_path))[0] + '.mp4'
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Render the video
    log(f"Rendering video to {output_path}...", "🔄")
    final_clip.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
    
    # Close the clips to free up resources
    video_clip.close()
    music_clip.close()
    
    # Close any voice clips
    for clip in audio_clips:
        if clip != music_clip:  # Avoid closing music_clip twice
            clip.close()
    
    final_clip.close()
    
    log(f"Video created successfully: {output_path}", "✅")
    
    return output_path

def process_scenario(scenario_path, vertical=True, force=False, quality=1.0, use_voice_lines=True):
    """Process a scenario file and generate a video.
    
    Args:
        scenario_path: Path to the scenario file
        vertical: Whether to generate a vertical video (9:16 aspect ratio)
        force: Whether to process the scenario even if it has already been processed
        quality: Quality factor for rendering (1.0 = full quality, 0.5 = half resolution)
        use_voice_lines: Whether to use voice lines in the video
    """
    try:
        with open(scenario_path, 'r', encoding='utf-8') as file:
            scenario = yaml.safe_load(file)
        
        log(f"Topic: {scenario['topic']}", "📌")
        
        # Get the output video path
        scenario_name = os.path.splitext(os.path.basename(scenario_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{scenario_name}.mp4")
        
        # Check if the video file already exists
        if not force and os.path.exists(output_path):
            log(f"Video already exists: {output_path}", "⚠️")
            log(f"   Use -f to regenerate it.", "💡")
            return False
        
        # Generate the video
        output_path = generate_video(scenario, scenario_path, vertical, quality, use_voice_lines)
        
        if output_path:
            log(f"Video generation complete: {output_path}", "🎉")
            return True
        else:
            log(f"Failed to generate video for {scenario_path}", "❌")
            return False
    except Exception as e:
        log(f"Error processing scenario {scenario_path}: {str(e)}", "❌")
        return False

def cleanup_temp_files():
    """Remove temporary files created during video generation."""
    log("\nCleaning up temporary files...", "🧹")
    
    # Clean up temporary MP4 files from root directory
    root_mp4_files = glob.glob(os.path.join(PROJECT_DIR, "*.mp4"))
    mp4_count = 0
    for mp4_file in root_mp4_files:
        try:
            os.remove(mp4_file)
            log(f"  Removed MP4: {os.path.basename(mp4_file)}", "✅")
            mp4_count += 1
        except Exception as e:
            log(f"  Failed to remove {os.path.basename(mp4_file)}: {str(e)}", "❌")
    
    # Clean up temporary emoji images from temp directory
    temp_dir = os.path.join(PROJECT_DIR, "temp")
    if os.path.exists(temp_dir):
        emoji_images = glob.glob(os.path.join(temp_dir, "emoji_debug_*.png"))
        emoji_count = 0
        for emoji_image in emoji_images:
            try:
                os.remove(emoji_image)
                emoji_count += 1
            except Exception as e:
                log(f"  Failed to remove {os.path.basename(emoji_image)}: {str(e)}", "❌")
        
        if emoji_count > 0:
            log(f"  Removed {emoji_count} temporary emoji image(s)", "✅")
    
    log(f"Cleanup complete. Removed {mp4_count} MP4 file(s) and {emoji_count} emoji image(s).", "🧹")

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
    parser.add_argument('--skip-voices', action='store_true',
                        help='Skip using voice lines in the videos')
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
    
    log(f"\nStarting {project_name} video generation", "🚀")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Determine if we should generate horizontal videos (vertical is now default)
    vertical = not args.horizontal
    
    if args.scenario:
        # Process a specific scenario
        scenario_path = args.scenario
        if not os.path.exists(scenario_path):
            log(f"Scenario file not found: {scenario_path}", "❌")
            return
        
        # Process the scenario, with force flag if specified
        success = process_scenario(scenario_path, vertical, args.force, args.quality, not args.skip_voices)
        
        if success:
            log(f"Video generation complete: {scenario_path}", "🎉")
    else:
        # Process the specified number of videos
        videos_generated = 0
        max_videos = args.num_videos
        
        # If max_videos is -1, process all unprocessed scenarios
        if max_videos == -1:
            unprocessed_scenarios = find_unprocessed_scenarios()
            if not unprocessed_scenarios:
                log("No unprocessed scenarios available.", "🏁")
                return
            
            log(f"Found {len(unprocessed_scenarios)} unprocessed scenarios", "🎯")
            
            for scenario_path in unprocessed_scenarios:
                log(f"Processing scenario: {os.path.basename(scenario_path)}", "🎯")
                
                # Process the scenario
                success = process_scenario(scenario_path, vertical, quality=args.quality, use_voice_lines=not args.skip_voices)
                
                if success:
                    videos_generated += 1
                    log(f"Progress: {videos_generated}/{len(unprocessed_scenarios)} videos generated", "📊")
            
            if videos_generated > 0:
                log(f"Successfully generated {videos_generated} videos.", "✅")
            else:
                log("No videos were generated.", "❌")
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
                    log("No more unprocessed scenarios available.", "🏁")
                    break
                
                log(f"Selected scenario: {os.path.basename(scenario_path)}", "🎯")
                
                # Process the scenario
                success = process_scenario(scenario_path, vertical, quality=args.quality, use_voice_lines=not args.skip_voices)
                
                if success:
                    videos_generated += 1
                    log(f"Progress: {videos_generated}/{max_videos if max_videos > 0 else 'all'} videos generated", "📊")
            
            if videos_generated > 0:
                log(f"Successfully generated {videos_generated} videos.", "✅")
            else:
                log("No videos were generated.", "❌")

    # Clean up temporary files
    cleanup_temp_files()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\nProcess interrupted by user (Ctrl+C)", "⚠️")
        log("Exiting gracefully...", "🛑")
        sys.exit(130)  # Standard exit code for SIGINT
