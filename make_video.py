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

def create_text_clip(text, duration, start_time, video_size):
    """Create a text clip with the given text and duration."""
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
        txt=text,
        fontsize=font_size,
        color='white',
        font=font_path,
        align='center',
        method='caption',
        size=(video_size[0] * 0.8, None)  # Width is 80% of video width
    )
    
    # Add a black outline/stroke to make text more readable
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
        
        # Calculate total duration needed
        total_duration = sum(slide['duration_seconds'] for slide in scenario['slides'])
        
        # If video is shorter than needed, loop it
        if video_clip.duration < total_duration:
            video_clip = video_clip.loop(duration=total_duration)
        else:
            # Otherwise trim it to the needed duration
            video_clip = video_clip.subclip(0, total_duration)
        
        # If audio is shorter than needed, loop it
        if audio_clip.duration < total_duration:
            audio_clip = audio_clip.loop(duration=total_duration)
        else:
            # Otherwise trim it to the needed duration
            audio_clip = audio_clip.subclip(0, total_duration)
        
        # Add audio to video
        video_clip = video_clip.set_audio(audio_clip)
        
        # For vertical videos (9:16 aspect ratio for TikTok/Reels)
        if vertical:
            print("🔄 Creating vertical (9:16) video for TikTok/Reels...")
            
            # Define target dimensions (9:16 aspect ratio)
            target_width = 720
            target_height = 1280
            
            # Create a black background clip with vertical dimensions
            bg_clip = ColorClip(size=(target_width, target_height), color=(0, 0, 0))
            bg_clip = bg_clip.set_duration(total_duration)
            
            # Resize the video to fit within the vertical frame
            # We'll resize it to maintain aspect ratio but fit within the vertical frame
            original_width, original_height = video_clip.size
            
            # Calculate new dimensions to maintain aspect ratio
            if original_width / original_height > target_width / target_height:
                # Video is wider than target ratio, resize based on height
                new_height = target_height
                new_width = int(original_width * (new_height / original_height))
            else:
                # Video is taller than target ratio, resize based on width
                new_width = target_width
                new_height = int(original_height * (new_width / original_width))
            
            # Resize the video
            video_clip = video_clip.resize(height=new_height)
            
            # Center the video on the background
            x_pos = (target_width - video_clip.size[0]) / 2
            video_clip = video_clip.set_position((x_pos, 0))
            
            # Create text clips for each slide
            text_clips = []
            current_time = 0
            
            for slide in scenario['slides']:
                duration = slide['duration_seconds']
                text = slide['text']
                
                # Create text clips sized for vertical format
                text_clip = create_text_clip(text, duration, current_time, (target_width, target_height))
                text_clips.append(text_clip)
                
                current_time += duration
            
            # Combine background, video, and text overlays
            final_clip = CompositeVideoClip([bg_clip, video_clip] + text_clips, size=(target_width, target_height))
        else:
            # Standard horizontal video
            # Create text clips for each slide
            text_clips = []
            current_time = 0
            
            for slide in scenario['slides']:
                duration = slide['duration_seconds']
                text = slide['text']
                
                text_clip = create_text_clip(text, duration, current_time, video_clip.size)
                text_clips.append(text_clip)
                
                current_time += duration
            
            # Combine video with text overlays
            final_clip = CompositeVideoClip([video_clip] + text_clips)
        
        # Write the result to a file
        print(f"🔄 Rendering video to {output_path}...")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium'
        )
        
        # Mark the scenario as processed
        scenario['has_video'] = True
        with open(scenario_path, 'w', encoding='utf-8') as file:
            yaml.dump(scenario, file, default_flow_style=False)
        
        print(f"✅ Video created successfully: {output_path}")
        print(f"✅ Scenario marked as processed: {scenario_path}")
        
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
