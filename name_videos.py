#!/usr/bin/env python3
"""
Usage:
    python name_videos.py [-m MODEL] [-f FRAMES] [--min MIN_LENGTH] [--max MAX_LENGTH] [-r]

This script processes videos in the lib/videos folder by:
1. Extracting frames from each video
2. Getting descriptions for each frame using an LLM
3. Generating a summary name for the video based on the frame descriptions
4. Optionally renaming the video file with the generated name
"""

import argparse
import os
import sys
import shutil
import tempfile
from pathlib import Path
import lmstudio as lms
from pydantic import BaseModel
import mimetypes
from moviepy.editor import VideoFileClip
import numpy as np
from PIL import Image
import yaml

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
VIDEOS_DIR = os.path.join(PROJECT_DIR, "lib", "videos")
TEMP_DIR = os.path.join(PROJECT_DIR, "temp")


class FrameDescription(BaseModel):
    """Model for frame description response from LLM."""
    description: str


class VideoSummary(BaseModel):
    """Model for video summary response from LLM."""
    suggested_filename: str


def is_video_file(file_path):
    """Check if a file is a video based on its MIME type."""
    mime, _ = mimetypes.guess_type(file_path)
    return mime is not None and mime.startswith("video")


def extract_frames(video_path, num_frames=4):
    """Extract frames from a video file."""
    print(f"🎬 Extracting {num_frames} frames from: {os.path.basename(video_path)}")
    
    # Create a temporary directory for this video's frames
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    frames_dir = os.path.join(TEMP_DIR, video_name)
    os.makedirs(frames_dir, exist_ok=True)
    
    # Load the video
    clip = VideoFileClip(video_path)
    
    # Calculate frame positions (evenly spaced)
    duration = clip.duration
    frame_times = [duration * i / (num_frames + 1) for i in range(1, num_frames + 1)]
    
    frame_paths = []
    for i, time in enumerate(frame_times):
        # Get the frame at the specified time
        frame = clip.get_frame(time)
        
        # Convert to PIL Image and save
        img = Image.fromarray(frame)
        frame_path = os.path.join(frames_dir, f"frame_{i+1:02d}.jpg")
        img.save(frame_path, quality=95)
        frame_paths.append(frame_path)
        print(f"  📸 Extracted frame at {time:.2f}s: {os.path.basename(frame_path)}")
    
    # Close the video clip
    clip.close()
    
    return frame_paths


def get_frame_descriptions(model, frame_paths):
    """Get descriptions for each frame using the LLM."""
    descriptions = []
    
    for i, frame_path in enumerate(frame_paths, start=1):
        print(f"  🔍 Analyzing frame {i}/{len(frame_paths)}: {os.path.basename(frame_path)}")
        
        try:
            # Prepare the image for the LLM
            image_handle = lms.prepare_image(frame_path)
            chat = lms.Chat()
            
            # Create the prompt for the LLM
            prompt = """
Describe this image in detail. Focus on:
- The main subject or scene
- Key visual elements
- Colors, lighting, and atmosphere
- Any notable actions or events shown

Provide a comprehensive description in 2-3 sentences.
"""
            
            # Get the description from the LLM
            chat.add_user_message(prompt, images=[image_handle])
            prediction = model.respond(chat, response_format=FrameDescription)
            
            # Extract the description
            description = prediction.parsed["description"].strip()
            descriptions.append(description)
            print(f"  ✅ Got description for frame {i}")
            
        except Exception as e:
            print(f"  ❌ Error analyzing frame {i}: {str(e)}")
            descriptions.append(f"Error: {str(e)}")
    
    return descriptions


def generate_video_name(model, descriptions, video_path, min_length=32, max_length=128):
    """Generate a summary name for the video based on frame descriptions."""
    print(f"  📝 Generating name for video based on {len(descriptions)} frame descriptions")
    
    try:
        chat = lms.Chat()
        
        # Create the prompt for the LLM
        prompt = f"""
I have extracted {len(descriptions)} frames from a video and obtained the following descriptions:

{chr(10).join([f"Frame {i+1}: {desc}" for i, desc in enumerate(descriptions)])}

Based on these descriptions, suggest a filename for this video.
Generate a filename using lowercase snake_case format, with a minimum length of {min_length} characters and a maximum of {max_length} characters.
Do not include the file extension in the filename.
Do not use personal names.
The filename should capture the essence of what this video shows.
"""
        
        # Get the summary from the LLM
        chat.add_user_message(prompt)
        prediction = model.respond(chat, response_format=VideoSummary)
        
        # Extract the suggested filename
        suggested_filename = prediction.parsed["suggested_filename"].strip()
        
        # Ensure the filename is within the specified length constraints
        if len(suggested_filename) < min_length:
            suggested_filename = suggested_filename.ljust(min_length, "_")
        if len(suggested_filename) > max_length:
            suggested_filename = suggested_filename[:max_length]
        
        print(f"  ✅ Generated name: {suggested_filename}")
        return suggested_filename
        
    except Exception as e:
        print(f"  ❌ Error generating video name: {str(e)}")
        # Fallback to a simple name based on the original filename
        original_name = os.path.splitext(os.path.basename(video_path))[0]
        return f"unnamed_{original_name}"


def save_metadata(video_path, descriptions, suggested_name):
    """Save metadata about the video analysis to a YAML file."""
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    metadata_dir = os.path.join(TEMP_DIR, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    
    metadata = {
        "original_filename": os.path.basename(video_path),
        "suggested_filename": suggested_name + os.path.splitext(video_path)[1],
        "frame_descriptions": [{"frame": i+1, "description": desc} for i, desc in enumerate(descriptions)]
    }
    
    metadata_path = os.path.join(metadata_dir, f"{video_name}.yaml")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"  💾 Saved metadata to: {os.path.basename(metadata_path)}")
    return metadata_path


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Process videos in lib/videos folder using LLM for naming.")
    parser.add_argument("-m", "--model", default="gemma-3-4b-it", help="Model name to use for image analysis (default: gemma-3-4b-it)")
    parser.add_argument("-f", "--frames", type=int, default=4, help="Number of frames to extract per video (default: 4)")
    parser.add_argument("--min", "--min-length", type=int, default=32, help="Minimum filename length (default: 32)")
    parser.add_argument("--max", "--max-length", type=int, default=128, help="Maximum filename length (default: 128)")
    parser.add_argument("-r", "--rename", action="store_true", help="Rename the original video files (default: false)")
    args = parser.parse_args()
    
    # Check if the videos directory exists
    if not os.path.exists(VIDEOS_DIR):
        print(f"❌ Error: Videos directory not found: {VIDEOS_DIR}")
        print(f"💡 Hint: Create the directory at {VIDEOS_DIR} and add video files to it.")
        sys.exit(1)
    
    # Create temp directory if it doesn't exist
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    # Initialize the LLM
    try:
        model = lms.llm(args.model)
        print(f"🤖 Using model: {args.model}")
    except Exception as e:
        print(f"❌ Error initializing model: {str(e)}")
        sys.exit(1)
    
    # Find all video files in the videos directory
    video_files = [f for f in Path(VIDEOS_DIR).glob("*") if f.is_file() and is_video_file(f)]
    total_videos = len(video_files)
    
    if not video_files:
        print(f"⚠️ No video files found in {VIDEOS_DIR}")
        sys.exit(0)
    
    print(f"🎥 Found {total_videos} video(s). Starting processing...\n")
    
    # Process each video
    for idx, video_path in enumerate(video_files, start=1):
        print(f"\n[{idx}/{total_videos}] Processing video: {video_path.name}")
        
        try:
            # Extract frames from the video
            frame_paths = extract_frames(str(video_path), args.frames)
            
            # Get descriptions for each frame
            descriptions = get_frame_descriptions(model, frame_paths)
            
            # Generate a summary name for the video
            suggested_name = generate_video_name(model, descriptions, str(video_path), 
                                                args.min, args.max)
            
            # Save metadata
            metadata_path = save_metadata(str(video_path), descriptions, suggested_name)
            
            # Rename the video file if requested
            if args.rename:
                new_filename = suggested_name + video_path.suffix.lower()
                new_filepath = video_path.with_name(new_filename)
                
                if new_filepath.exists():
                    print(f"⏭️ Skipped renaming: {new_filename} already exists.")
                else:
                    video_path.rename(new_filepath)
                    print(f"✅ Renamed video to: {new_filename}")
            
            print(f"✅ [{idx}/{total_videos}] Completed processing: {video_path.name}")
            
        except Exception as e:
            print(f"❌ [{idx}/{total_videos}] Error processing {video_path.name}: {str(e)}")
    
    print("\n🎉 All done!")


if __name__ == "__main__":
    main()
