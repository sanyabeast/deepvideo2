import os
import yaml
import random
import argparse
import difflib
import platform
import re
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.config import change_settings

# Configure MoviePy to use ImageMagick
# Path to where ImageMagick is installed on the system
change_settings({"IMAGEMAGICK_BINARY": r"C:\Dev\ImageMagick\magick.exe"})

# Fix for PIL.Image.ANTIALIAS deprecation
try:
    import PIL
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        # For newer versions of Pillow, ANTIALIAS is renamed to LANCZOS
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
except (ImportError, AttributeError):
    pass

# ─────────────────────────────────────────────────────
# 📂 DIRECTORIES
# ─────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(SCRIPT_DIR, 'scenarios')
VIDEOS_DIR = os.path.join(SCRIPT_DIR, 'lib', 'videos')
MUSIC_DIR = os.path.join(SCRIPT_DIR, 'lib', 'music')
FONTS_DIR = os.path.join(SCRIPT_DIR, 'lib', 'fonts')
EMOJI_FONTS_DIR = os.path.join(SCRIPT_DIR, 'lib', 'fonts_emoji')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')

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
    if not os.path.exists(FONTS_DIR):
        return None
    
    font_files = [os.path.join(FONTS_DIR, f) for f in os.listdir(FONTS_DIR) if f.endswith(('.ttf', '.otf'))]
    if not font_files:
        return None
    
    # Since there's only one font, just return it directly
    return font_files[0]

def get_emoji_font():
    """Get an emoji font from the emoji fonts directory."""
    if not os.path.exists(EMOJI_FONTS_DIR):
        return None
    
    emoji_font_files = [os.path.join(EMOJI_FONTS_DIR, f) for f in os.listdir(EMOJI_FONTS_DIR) 
                        if f.endswith(('.ttf', '.otf'))]
    
    if not emoji_font_files:
        return None
    
    # Prioritize Noto Color Emoji if available
    for font_file in emoji_font_files:
        if 'noto' in os.path.basename(font_file).lower() and 'emoji' in os.path.basename(font_file).lower():
            print(f"🔤 Found Noto Emoji font: {os.path.basename(font_file)}")
            return font_file
    
    # Otherwise use the first emoji font
    return emoji_font_files[0]

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

def find_random_scenario():
    """Find a random scenario that hasn't been processed yet."""
    # Get all scenario files
    scenario_files = [f for f in os.listdir(SCENARIOS_DIR) if f.endswith('.yaml')]
    
    if not scenario_files:
        print("❌ No scenario files found.")
        return None
    
    # Shuffle the files to get a random order
    random.shuffle(scenario_files)
    
    # Find the first scenario that hasn't been processed
    for filename in scenario_files:
        scenario_path = os.path.join(SCENARIOS_DIR, filename)
        
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario = yaml.safe_load(f)
        
        # Check if the scenario has already been processed
        if not scenario.get('has_video', False):
            print(f"🎯 Selected scenario: {filename}")
            print(f"📌 Topic: {scenario['topic']}")
            return scenario_path
    
    print("❌ All scenarios already have videos.")
    return None

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
        ' (', 
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

def create_text_clip(text, duration, start_time, video_size):
    """Create a text clip with the given text and duration."""
    # Format text for better display
    formatted_text = format_text_for_display(text)
    
    # Extract and remove emojis
    emojis = extract_emojis(formatted_text)
    text_without_emojis = remove_emojis(formatted_text)
    
    # Get font paths
    regular_font_path = get_random_font()
    emoji_font_path = get_emoji_font()
    
    if not regular_font_path:
        print("⚠️ Using default font for regular text.")
        regular_font = None
    else:
        print(f"🔤 Using font for regular text: {os.path.basename(regular_font_path)}")
        regular_font = regular_font_path
    
    # Create the main text clip (without emojis)
    main_txt_clip = TextClip(
        txt=text_without_emojis,
        fontsize=90,  # Increased font size for better visibility
        color='white',
        font=regular_font,
        align='center',
        method='caption',
        size=(video_size[0] * 0.8, None),  # Width is 80% of video width
        stroke_color='black',
        stroke_width=3  # Increased stroke width for better visibility
    )
    
    # Set position and timing for main text
    main_txt_clip = main_txt_clip.set_position('center')
    main_txt_clip = main_txt_clip.set_start(start_time)
    main_txt_clip = main_txt_clip.set_duration(duration)
    
    # If there are emojis and we have an emoji font, create a separate emoji clip
    if emojis and emoji_font_path:
        print(f"🔤 Rendering emojis separately: {emojis}")
        print(f"🔤 Using emoji font: {os.path.basename(emoji_font_path)}")
        
        emoji_txt_clip = TextClip(
            txt=emojis,
            fontsize=100,  # Slightly larger for emojis
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
    
    # Load the video and audio clips
    video_clip = VideoFileClip(os.path.join(VIDEOS_DIR, video_file))
    audio_clip = AudioFileClip(os.path.join(MUSIC_DIR, music_file))
    
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
    
    # Get video duration from scenario or calculate from slides
    if 'duration' in scenario:
        video_duration = scenario['duration']
    else:
        # Calculate total duration from slides
        video_duration = sum(slide['duration_seconds'] for slide in scenario['slides'])
    
    # Select a random segment from the video if it's longer than needed
    if video_clip.duration > video_duration:
        max_start_time = video_clip.duration - video_duration
        start_time = random.uniform(0, max_start_time)
        print(f"🎬 Using video segment starting at {start_time:.2f}s")
        video_clip = video_clip.subclip(start_time, start_time + video_duration)
    else:
        # If video is shorter, loop it
        video_clip = video_clip.loop(duration=video_duration)
    
    # Select a random segment from the audio if it's longer than needed
    if audio_clip.duration > video_duration:
        max_start_time = audio_clip.duration - video_duration
        start_time = random.uniform(0, max_start_time)
        print(f"🎵 Using audio segment starting at {start_time:.2f}s")
        audio_clip = audio_clip.subclip(start_time, start_time + video_duration)
    else:
        # If audio is shorter, loop it
        audio_clip = audio_clip.loop(duration=video_duration)
    
    # Set the audio for the video clip
    video_clip = video_clip.set_audio(audio_clip)
    
    # Create text clips for each slide
    slides = scenario['slides']
    print(f"📝 Creating {len(slides)} slides")
    
    # Create a list to hold all clips (video and text)
    all_clips = [video_clip]
    
    # Add text clips for each slide
    current_time = 0
    for slide in slides:
        # Get slide text and duration
        slide_text = slide['text']
        slide_duration = slide['duration_seconds']
        
        # Create text clips for this slide
        text_clips = create_text_clip(slide_text, slide_duration, current_time, target_resolution)
        all_clips.extend(text_clips)
        
        # Update current time
        current_time += slide_duration
    
    # Compose the final video
    final_clip = CompositeVideoClip(all_clips)
    
    # Create the output filename
    output_filename = os.path.splitext(os.path.basename(scenario_path))[0] + '.mp4'
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Render the video
    print(f"🔄 Rendering video to {output_path}...")
    final_clip.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac')
    
    # Close the clips to free up resources
    video_clip.close()
    audio_clip.close()
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
            print(f"   Use --force to process it anyway.")
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
    parser.add_argument('-n', '--num-videos', type=int, default=1, 
                        help='Number of videos to generate. Use -1 to process all available scenarios.')
    parser.add_argument('--horizontal', action='store_true', 
                        help='Generate horizontal (16:9) videos instead of vertical (9:16).')
    parser.add_argument('-s', '--scenario', type=str, help='Path to a specific scenario file to process')
    parser.add_argument('--force', action='store_true',
                        help='Force processing of a scenario even if it has already been processed')
    parser.add_argument('-q', '--quality', type=float, default=1.0,
                        help='Quality factor for rendering (1.0 = full quality, 0.5 = half resolution)')
    return parser.parse_args()

def main():
    """Main function."""
    args = parse_args()
    
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
