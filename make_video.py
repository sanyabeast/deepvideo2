import os
import yaml
import random
import argparse
import difflib
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
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'output')

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_random_font():
    """Get a random font from the fonts directory."""
    if not os.path.exists(FONTS_DIR):
        print(f"⚠️ Fonts directory not found: {FONTS_DIR}")
        return None
    
    font_files = [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))]
    if not font_files:
        print("⚠️ No font files found in the fonts directory.")
        return None
    
    random_font = random.choice(font_files)
    return os.path.join(FONTS_DIR, random_font)

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
    matches = difflib.get_close_matches(target, options, n=1, cutoff=0.1)
    
    if matches:
        return matches[0]
    
    # If no match found, return the first option as a fallback
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
    break_points = [
        ': ', '; ', 
        ', ', 
        ' - ', 
        ' but ', ' and ', ' or ', 
        ' because ', ' when ', ' if '
    ]
    
    # Try to find a good break point
    for separator in break_points:
        if separator in text:
            parts = text.split(separator, 1)  # Split only on the first occurrence
            # For conjunctions, keep them with the second part
            if separator.strip() in ['but', 'and', 'or', 'because', 'when', 'if']:
                return parts[0] + '\n' + separator.strip() + parts[1]
            else:
                # For punctuation, keep it with the first part
                return parts[0] + separator.rstrip() + '\n' + parts[1].lstrip()
    
    # If no good break point is found but text is still long, try to break at a space
    # near the middle of the text
    if len(text) > 40:
        words = text.split()
        if len(words) > 3:
            middle_idx = len(words) // 2
            return ' '.join(words[:middle_idx]) + '\n' + ' '.join(words[middle_idx:])
    
    # If all else fails, return the original text
    return text

def create_text_clip(text, duration, start_time, video_size):
    """Create a text clip with the given text and duration."""
    # Format text for better display
    formatted_text = format_text_for_display(text)
    
    # Use a random font from the fonts directory
    font_path = get_random_font()
    font_size = 70
    
    # If no font found, use the default
    if not font_path:
        print("⚠️ Using default font.")
        font_path = None
    else:
        print(f"🔤 Using font: {os.path.basename(font_path)}")
    
    # Create the text clip
    txt_clip = TextClip(
        txt=formatted_text,
        fontsize=font_size,
        color='white',
        font=font_path,
        align='center',
        method='caption',
        size=(video_size[0] * 0.8, None),  # Width is 80% of video width
        stroke_color='black',
        stroke_width=2  # Add outline for better readability
    )
    
    # Set position and timing
    txt_clip = txt_clip.set_position('center')
    txt_clip = txt_clip.set_start(start_time)
    txt_clip = txt_clip.set_duration(duration)
    
    return txt_clip

def generate_video(scenario, scenario_path, vertical=True):
    """Generate a video from a scenario.
    
    Args:
        scenario: The scenario data
        scenario_path: Path to the scenario file
        vertical: Whether to generate a vertical video (9:16 aspect ratio)
    """
    # Extract filename without extension
    base_filename = os.path.basename(scenario_path)
    output_filename = os.path.splitext(base_filename)[0] + ".mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Get all available music and video files
    available_music = os.listdir(MUSIC_DIR)
    available_videos = os.listdir(VIDEOS_DIR)
    
    # Find the best matching music and video files
    music_file = find_best_match(scenario['music'], available_music)
    video_file = find_best_match(scenario['video'], available_videos)
    
    # Get music and video paths
    music_path = os.path.join(MUSIC_DIR, music_file)
    video_path = os.path.join(VIDEOS_DIR, video_file)
    
    print(f"🎵 Using music: {music_file}")
    print(f"🎬 Using video: {video_file}")
    print(f"📝 Creating {len(scenario['slides'])} slides")
    
    try:
        # Load video and audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(music_path)
        
        # Calculate total duration of all slides
        total_duration = sum(slide['duration_seconds'] for slide in scenario['slides'])
        
        # Select random start point for video, ensuring it doesn't go past the end
        max_video_start = max(0, video_clip.duration - total_duration)
        video_start = random.uniform(0, max_video_start) if max_video_start > 0 else 0
        
        # Select random start point for audio, ensuring it doesn't go past the end
        max_audio_start = max(0, audio_clip.duration - total_duration)
        audio_start = random.uniform(0, max_audio_start) if max_audio_start > 0 else 0
        
        print(f"🎬 Using video segment starting at {video_start:.2f}s")
        print(f"🎵 Using audio segment starting at {audio_start:.2f}s")
        
        # Trim video and audio to the selected segments
        video_clip = video_clip.subclip(video_start, video_start + total_duration)
        audio_clip = audio_clip.subclip(audio_start, audio_start + total_duration)
        
        # Set the audio of the video clip
        video_clip = video_clip.set_audio(audio_clip)
        
        # Determine video dimensions based on orientation
        if vertical:
            print("🔄 Creating vertical (9:16) video for TikTok/Reels...")
            # For vertical video (9:16 aspect ratio)
            target_width = 1080
            target_height = 1920
        else:
            # For horizontal video (16:9 aspect ratio)
            target_width = 1920
            target_height = 1080
        
        # Resize and crop video to target dimensions
        # First resize to cover the target dimensions while maintaining aspect ratio
        video_aspect = video_clip.w / video_clip.h
        target_aspect = target_width / target_height
        
        if video_aspect > target_aspect:
            # Video is wider than target, resize based on height
            new_height = target_height
            new_width = int(new_height * video_aspect)
            resized_clip = video_clip.resize(height=new_height)
            # Crop the width to match target width
            x_center = resized_clip.w // 2
            x1 = x_center - (target_width // 2)
            cropped_clip = resized_clip.crop(x1=x1, y1=0, width=target_width, height=target_height)
        else:
            # Video is taller than target, resize based on width
            new_width = target_width
            new_height = int(new_width / video_aspect)
            resized_clip = video_clip.resize(width=new_width)
            # Crop the height to match target height
            y_center = resized_clip.h // 2
            y1 = y_center - (target_height // 2)
            cropped_clip = resized_clip.crop(x1=0, y1=y1, width=target_width, height=target_height)
        
        # Create text clips for each slide
        text_clips = []
        current_time = 0
        
        for slide in scenario['slides']:
            duration = slide['duration_seconds']
            text = slide['text']
            
            # Create text clip
            txt_clip = create_text_clip(text, duration, current_time, (target_width, target_height))
            text_clips.append(txt_clip)
            
            # Update current time
            current_time += duration
        
        # Combine video and text clips
        final_clip = CompositeVideoClip([cropped_clip] + text_clips, size=(target_width, target_height))
        
        # Set the duration of the final clip
        final_clip = final_clip.set_duration(total_duration)
        
        # Write the output file
        print(f"🔄 Rendering video to {output_path}...")
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=30)
        
        print(f"✅ Video created successfully: {output_path}")
        
        # Clean up
        video_clip.close()
        audio_clip.close()
        final_clip.close()
        
        return output_path
    
    except Exception as e:
        print(f"❌ Error generating video: {str(e)}")
        return None

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate videos from scenarios.')
    parser.add_argument('--horizontal', action='store_true', help='Generate horizontal (16:9) videos instead of vertical (9:16)')
    parser.add_argument('--scenario', type=str, help='Path to a specific scenario file to process')
    return parser.parse_args()

def mark_scenario_processed(scenario_path):
    """Mark a scenario as processed."""
    with open(scenario_path, 'r', encoding='utf-8') as f:
        scenario = yaml.safe_load(f)
    
    scenario['has_video'] = True
    with open(scenario_path, 'w', encoding='utf-8') as file:
        yaml.dump(scenario, file, default_flow_style=False)

def main():
    """Main function."""
    args = parse_args()
    
    # Determine if we should generate horizontal videos (vertical is now default)
    vertical = not args.horizontal
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if args.scenario:
        # Process a specific scenario
        scenario_path = args.scenario
        if not os.path.exists(scenario_path):
            print(f"❌ Scenario file not found: {scenario_path}")
            return
        
        # Load the scenario
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario = yaml.safe_load(f)
        
        # Generate the video
        generate_video(scenario, scenario_path, vertical=vertical)
    else:
        # Find a random scenario that hasn't been processed yet
        scenario_path = find_random_scenario()
        if not scenario_path:
            return
        
        # Load the scenario
        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario = yaml.safe_load(f)
        
        # Generate the video
        generate_video(scenario, scenario_path, vertical=vertical)
        
        # Mark the scenario as processed
        mark_scenario_processed(scenario_path)
        
        # Get the output filename
        base_filename = os.path.basename(scenario_path)
        output_filename = os.path.splitext(base_filename)[0] + ".mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        print(f"🎉 Video generation complete: {output_path}")

if __name__ == "__main__":
    main()
