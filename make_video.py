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
SCENARIOS_DIR = "scenarios"
OUTPUT_DIR = "output"
MUSIC_DIR = os.path.join("lib", "music")
VIDEOS_DIR = os.path.join("lib", "videos")
FONTS_DIR = os.path.join("lib", "fonts")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_random_scenario():
    """Find a random scenario that doesn't have a video yet."""
    scenario_files = [f for f in os.listdir(SCENARIOS_DIR) if f.endswith('.yaml')]
    
    if not scenario_files:
        print("❌ No scenario files found in the scenarios directory.")
        return None
    
    # Shuffle the list to get a random order
    random.shuffle(scenario_files)
    
    # Find the first scenario that doesn't have a video
    for filename in scenario_files:
        filepath = os.path.join(SCENARIOS_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            scenario = yaml.safe_load(file)
            
            # Check if the scenario already has a video
            if not scenario.get('has_video', False):
                print(f"🎯 Selected scenario: {filename}")
                print(f"📌 Topic: {scenario['topic']}")
                return filepath, scenario
    
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
    # Use a font from the fonts directory
    font_path = os.path.join(FONTS_DIR, "OpenSans-Bold.ttf")
    
    # Calculate width as an integer (80% of video width)
    width = int(video_size[0] * 0.8)
    
    # Create text clip with improved parameters for better visibility
    # Using MoviePy 1.0.3 syntax
    txt_clip = TextClip(
        txt=text,  # In 1.0.3, the parameter is 'txt' not 'text'
        font=font_path,
        color='white',
        size=(width, None),  # 80% of video width
        fontsize=70,         # Larger font size for better visibility
        stroke_color='black',
        stroke_width=2       # Add outline for better readability
    )
    
    # Set position to center of screen
    txt_clip = txt_clip.set_position('center').set_duration(duration).set_start(start_time)
    
    return txt_clip

def generate_video(scenario, scenario_path, vertical=False):
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

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Generate videos from scenario files')
    parser.add_argument('-f', '--file', help='Specific scenario file to process (optional)')
    parser.add_argument('-v', '--vertical', action='store_true', help='Generate vertical video (9:16 aspect ratio)')
    args = parser.parse_args()
    
    if args.file:
        # Process a specific file
        scenario_path = args.file
        if not os.path.exists(scenario_path):
            scenario_path = os.path.join(SCENARIOS_DIR, args.file)
            
        if not os.path.exists(scenario_path):
            print(f"❌ File not found: {args.file}")
            return
            
        with open(scenario_path, 'r', encoding='utf-8') as file:
            scenario = yaml.safe_load(file)
            
        if scenario.get('has_video', False):
            print(f"⚠️ This scenario already has a video. Regenerating...")
            
        output_path = generate_video(scenario, scenario_path, vertical=args.vertical)
        if output_path:
            print(f"🎉 Video generation complete: {output_path}")
    else:
        # Find a random scenario that doesn't have a video
        result = find_random_scenario()
        if result:
            scenario_path, scenario = result
            output_path = generate_video(scenario, scenario_path, vertical=args.vertical)
            if output_path:
                print(f"🎉 Video generation complete: {output_path}")

if __name__ == "__main__":
    main()
