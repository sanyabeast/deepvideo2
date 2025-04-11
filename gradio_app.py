#!/usr/bin/env python3
"""
DeepVideo2 Gradio Interface
A simple web UI for the DeepVideo2 video generation system
"""

import os
import sys
import glob
import gradio as gr
import yaml
import subprocess
import time
from pathlib import Path

# Import DeepVideo2 modules
import make_scenarios
import make_voice_lines
import make_videos
import name_videos
import clean

def get_config_files():
    """Get a list of available configuration files"""
    configs = glob.glob("configs/*.yaml")
    return [os.path.basename(c) for c in configs]

def get_project_name(config_file):
    """Extract project name from config file name"""
    return os.path.splitext(config_file)[0]

def load_config(config_file):
    """Load a configuration file"""
    config_path = os.path.join("configs", config_file)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        return {"error": str(e)}

def run_command(cmd, progress=None):
    """Run a command and capture its output"""
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    output = []
    for line in iter(process.stdout.readline, ""):
        output.append(line)
        if progress:
            progress(line)
            
    process.stdout.close()
    return_code = process.wait()
    
    if return_code:
        output.append(f"Command failed with return code {return_code}")
    
    return "\n".join(output)

def generate_scenarios(config_file, num_scenarios, progress=gr.Progress()):
    """Generate scenarios using the selected configuration"""
    project = get_project_name(config_file)
    config_path = os.path.join("configs", config_file)
    
    progress(0, desc="Starting scenario generation...")
    cmd = [sys.executable, "make_scenarios.py", "-c", config_path, "-n", str(num_scenarios)]
    
    result = run_command(cmd, lambda x: progress(0.5, desc=x))
    
    # Check if scenarios were created
    scenarios_dir = os.path.join("output", project, "scenarios")
    if os.path.exists(scenarios_dir):
        scenarios = glob.glob(os.path.join(scenarios_dir, "*.yaml"))
        progress(1.0, desc=f"Created {len(scenarios)} scenarios")
        return f"Generated {len(scenarios)} scenarios for project '{project}'\n\n{result}"
    else:
        return f"Failed to generate scenarios for project '{project}'\n\n{result}"

def generate_voice_lines(config_file, progress=gr.Progress()):
    """Generate voice lines for all scenarios"""
    project = get_project_name(config_file)
    config_path = os.path.join("configs", config_file)
    
    progress(0, desc="Starting voice line generation...")
    cmd = [sys.executable, "make_voice_lines.py", "-c", config_path]
    
    result = run_command(cmd, lambda x: progress(0.5, desc=x))
    
    # Check if voice lines were created
    voice_lines_dir = os.path.join("output", project, "voice_lines")
    if os.path.exists(voice_lines_dir):
        voice_lines = glob.glob(os.path.join(voice_lines_dir, "*.wav"))
        progress(1.0, desc=f"Created {len(voice_lines)} voice lines")
        return f"Generated {len(voice_lines)} voice lines for project '{project}'\n\n{result}"
    else:
        return f"Failed to generate voice lines for project '{project}'\n\n{result}"

def generate_videos(config_file, vertical, quality, progress=gr.Progress()):
    """Generate videos for all scenarios"""
    project = get_project_name(config_file)
    config_path = os.path.join("configs", config_file)
    
    progress(0, desc="Starting video generation...")
    cmd = [sys.executable, "make_videos.py", "-c", config_path]
    
    if vertical:
        cmd.append("-v")
    else:
        cmd.append("-h")
        
    cmd.extend(["-q", str(quality)])
    
    result = run_command(cmd, lambda x: progress(0.5, desc=x))
    
    # Check if videos were created
    videos_dir = os.path.join("output", project, "videos")
    if os.path.exists(videos_dir):
        videos = glob.glob(os.path.join(videos_dir, "*.mp4"))
        progress(1.0, desc=f"Created {len(videos)} videos")
        return f"Generated {len(videos)} videos for project '{project}'\n\n{result}"
    else:
        return f"Failed to generate videos for project '{project}'\n\n{result}"

def name_background_videos(model_name, frames_count, progress=gr.Progress()):
    """Name background videos using LLM"""
    progress(0, desc="Starting video naming process...")
    cmd = [sys.executable, "name_videos.py"]
    
    if model_name:
        cmd.extend(["-m", model_name])
        
    if frames_count:
        cmd.extend(["-f", str(frames_count)])
    
    result = run_command(cmd, lambda x: progress(0.5, desc=x))
    
    # Check if videos were renamed
    videos_dir = os.path.join("lib", "videos")
    videos = glob.glob(os.path.join(videos_dir, "*.mp4"))
    progress(1.0, desc=f"Processed {len(videos)} videos")
    
    return f"Named {len(videos)} background videos\n\n{result}"

def clean_project(config_file, reset_only, progress=gr.Progress()):
    """Clean or reset a project"""
    project = get_project_name(config_file)
    config_path = os.path.join("configs", config_file)
    
    progress(0, desc=f"{'Resetting' if reset_only else 'Cleaning'} project...")
    cmd = [sys.executable, "clean.py", "-c", config_path]
    
    if reset_only:
        cmd.append("-r")
    else:
        cmd.append("-d")
    
    result = run_command(cmd, lambda x: progress(0.5, desc=x))
    progress(1.0, desc="Operation completed")
    
    return f"{'Reset' if reset_only else 'Cleaned'} project '{project}'\n\n{result}"

def get_project_info(config_file):
    """Get information about the current state of a project"""
    project = get_project_name(config_file)
    
    # Check project directories
    scenarios_dir = os.path.join("output", project, "scenarios")
    voice_lines_dir = os.path.join("output", project, "voice_lines")
    videos_dir = os.path.join("output", project, "videos")
    
    # Count files
    scenarios_count = len(glob.glob(os.path.join(scenarios_dir, "*.yaml"))) if os.path.exists(scenarios_dir) else 0
    voice_lines_count = len(glob.glob(os.path.join(voice_lines_dir, "*.wav"))) if os.path.exists(voice_lines_dir) else 0
    videos_count = len(glob.glob(os.path.join(videos_dir, "*.mp4"))) if os.path.exists(videos_dir) else 0
    
    # Count processed scenarios
    processed_count = 0
    if os.path.exists(scenarios_dir):
        for scenario_file in glob.glob(os.path.join(scenarios_dir, "*.yaml")):
            try:
                with open(scenario_file, "r", encoding="utf-8") as f:
                    scenario = yaml.safe_load(f)
                    if scenario.get("has_video", False):
                        processed_count += 1
            except:
                pass
    
    info = f"""
## Project: {project}

### Current Status:
- Scenarios: {scenarios_count} total
- Voice Lines: {voice_lines_count} total
- Videos: {videos_count} total
- Processed Scenarios: {processed_count} / {scenarios_count if scenarios_count > 0 else 0}

### Directories:
- Scenarios: {scenarios_dir}
- Voice Lines: {voice_lines_dir}
- Videos: {videos_dir}
"""
    
    return info

def list_videos(config_file):
    """List videos for the selected project"""
    project = get_project_name(config_file)
    videos_dir = os.path.join("output", project, "videos")
    
    if not os.path.exists(videos_dir):
        return "No videos found for this project."
    
    videos = glob.glob(os.path.join(videos_dir, "*.mp4"))
    if not videos:
        return "No videos found for this project."
    
    video_list = []
    for video in videos:
        video_name = os.path.basename(video)
        size_mb = os.path.getsize(video) / (1024 * 1024)
        video_list.append(f"- [{video_name}]({video}) ({size_mb:.2f} MB)")
    
    return "## Generated Videos\n\n" + "\n".join(video_list)

def on_config_change(config_file):
    """Handle config file selection change"""
    project_info = get_project_info(config_file)
    videos_list = list_videos(config_file)
    return project_info, videos_list

def create_ui():
    """Create the Gradio interface"""
    with gr.Blocks(title="DeepVideo2 Control Panel") as app:
        gr.Markdown("# DeepVideo2 Control Panel")
        gr.Markdown("Generate engaging motivational videos with custom content and voice narration")
        
        with gr.Row():
            with gr.Column(scale=1):
                # Configuration selection
                config_dropdown = gr.Dropdown(
                    choices=get_config_files(),
                    label="Select Project Configuration",
                    info="Choose a configuration file from the configs directory"
                )
                
                # Tabs for different operations
                with gr.Tabs():
                    with gr.TabItem("Generate Scenarios"):
                        num_scenarios = gr.Slider(
                            minimum=1, 
                            maximum=20, 
                            value=5, 
                            step=1, 
                            label="Number of Scenarios",
                            info="How many new scenarios to generate"
                        )
                        scenarios_btn = gr.Button("Generate Scenarios", variant="primary")
                        scenarios_output = gr.Textbox(label="Output", lines=10)
                        
                    with gr.TabItem("Generate Voice Lines"):
                        voice_lines_btn = gr.Button("Generate Voice Lines", variant="primary")
                        voice_lines_output = gr.Textbox(label="Output", lines=10)
                        
                    with gr.TabItem("Generate Videos"):
                        vertical = gr.Checkbox(
                            label="Vertical Format (9:16)", 
                            value=True,
                            info="Use vertical format (9:16) or horizontal (16:9)"
                        )
                        quality = gr.Slider(
                            minimum=0.25, 
                            maximum=1.0, 
                            value=1.0, 
                            step=0.25, 
                            label="Quality",
                            info="Lower quality for faster rendering (0.25 to 1.0)"
                        )
                        videos_btn = gr.Button("Generate Videos", variant="primary")
                        videos_output = gr.Textbox(label="Output", lines=10)
                        
                    with gr.TabItem("Name Background Videos"):
                        model_name = gr.Textbox(
                            label="LLM Model Name", 
                            value="gemma-3-4b-it",
                            info="Name of the LLM model to use for generating descriptions"
                        )
                        frames_count = gr.Slider(
                            minimum=1, 
                            maximum=10, 
                            value=5, 
                            step=1, 
                            label="Frames per Video",
                            info="Number of frames to extract from each video"
                        )
                        name_videos_btn = gr.Button("Name Background Videos", variant="primary")
                        name_videos_output = gr.Textbox(label="Output", lines=10)
                        
                    with gr.TabItem("Clean Project"):
                        reset_only = gr.Checkbox(
                            label="Reset Only", 
                            value=True,
                            info="Only reset processing status (don't delete files)"
                        )
                        clean_btn = gr.Button("Clean Project", variant="primary")
                        clean_output = gr.Textbox(label="Output", lines=10)
            
            with gr.Column(scale=1):
                # Project information
                project_info = gr.Markdown(label="Project Information")
                videos_list = gr.Markdown(label="Videos")
        
        # Set up event handlers
        config_dropdown.change(on_config_change, inputs=[config_dropdown], outputs=[project_info, videos_list])
        
        scenarios_btn.click(
            generate_scenarios, 
            inputs=[config_dropdown, num_scenarios], 
            outputs=scenarios_output
        ).then(
            on_config_change, 
            inputs=[config_dropdown], 
            outputs=[project_info, videos_list]
        )
        
        voice_lines_btn.click(
            generate_voice_lines, 
            inputs=[config_dropdown], 
            outputs=voice_lines_output
        ).then(
            on_config_change, 
            inputs=[config_dropdown], 
            outputs=[project_info, videos_list]
        )
        
        videos_btn.click(
            generate_videos, 
            inputs=[config_dropdown, vertical, quality], 
            outputs=videos_output
        ).then(
            on_config_change, 
            inputs=[config_dropdown], 
            outputs=[project_info, videos_list]
        )
        
        name_videos_btn.click(
            name_background_videos, 
            inputs=[model_name, frames_count], 
            outputs=name_videos_output
        )
        
        clean_btn.click(
            clean_project, 
            inputs=[config_dropdown, reset_only], 
            outputs=clean_output
        ).then(
            on_config_change, 
            inputs=[config_dropdown], 
            outputs=[project_info, videos_list]
        )
        
        # Initialize with first config if available
        if get_config_files():
            app.load(
                on_config_change, 
                inputs=[config_dropdown], 
                outputs=[project_info, videos_list]
            )
    
    return app

if __name__ == "__main__":
    # Make sure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if running in virtual environment
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("Warning: It's recommended to run this app within the project's virtual environment.")
        print("Activate your venv with: .\\venv\\Scripts\\activate (Windows) or source venv/bin/activate (Linux/Mac)")
    
    # Check if gradio is installed
    try:
        import gradio
    except ImportError:
        print("Error: Gradio is not installed. Please install it with:")
        print("pip install gradio==4.19.1")
        sys.exit(1)
    
    # Create and launch the app
    print("Starting DeepVideo2 Gradio interface...")
    app = create_ui()
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)
    print("DeepVideo2 Gradio interface is running at http://127.0.0.1:7860")
