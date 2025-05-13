# DeepVideo2

A powerful tool for generating engaging motivational videos from text-based scenarios with custom fonts, emoji support, and dynamic content.

## Overview

DeepVideo2 is a Python-based video generation system that transforms YAML scenario files into polished videos with text overlays, background music, and visual elements. The system handles emoji rendering, custom fonts, and various quality settings to produce professional-looking content with minimal effort.

## Features

- **Theme-Based Topic Generation**: Generate topics based on predefined themes in project configs
- **Configuration Validation**: Automatic validation of config files to ensure required placeholders and sections
- **Text-to-Video Generation**: Convert YAML scenario files into complete videos with text overlays
- **Enhanced Emoji Support**: Render colorful emojis with configurable size, rotation, and positioning
- **Custom Font Integration**: Use custom fonts for text rendering with proper ImageMagick integration
- **Background Music**: Add music tracks to your videos with automatic matching
- **Background Video**: Incorporate video backgrounds with proper sizing and positioning
- **Quality Control**: Adjust output quality for different use cases
- **Vertical/Horizontal Formats**: Support for both 9:16 (vertical) and 16:9 (horizontal) aspect ratios
- **Project-Based Organization**: Organize all generated content by project name
- **Audio Normalization**: Automatically normalize voice lines for consistent audio levels
- **Silence Trimming**: Remove excess silence from the end of voice lines for better timing
- **Text Preprocessing**: Clean up text before sending to TTS to improve voice quality
- **Intelligent Workflow**: Generate only the number of scenarios needed to reach your target
- **Voice Line Generation**: Create voice narration for each slide with emotion control
- **Multiple TTS Providers**: Support for both Zonos and Orpheus TTS systems
- **Voice Line Processing**: Trim voice line endings to prevent audio artifacts
- **Flexible Configuration**: Use project-specific configuration files in the configs/ directory
- **Automatic Video Naming**: Generate descriptive filenames for background videos based on visual content
- **Configurable Timing**: Set custom intro and outro delays for professional-looking videos
- **Automatic Cleanup**: Remove temporary files after video generation
- **ComfyUI Image Generation**: Generate background images for scenarios using ComfyUI
- **Intelligent Image Handling**: Resize and position images to properly cover the entire video frame
- **Enhanced Text Visibility**: Semi-transparent background behind text for improved readability

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd deepvideo2
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install ImageMagick (required for text rendering with MoviePy):
   - Windows: Download and install from [ImageMagick website](https://imagemagick.org/script/download.php)
   - macOS: `brew install imagemagick`
   - Linux: `sudo apt-get install imagemagick`

4. Register fonts with ImageMagick (required for custom font support):
   ```
   python register_fonts.py
   ```
   Note: This may require administrator privileges on Windows.

5. Set up Zonos TTS Server (optional, for voice generation):
   - Follow the instructions in `misc/zonos_injection/README.md` to integrate with Zonos

## Project Structure

```
deepvideo2/
├── configs/               # Configuration files for different projects
│   ├── sample.yaml        # Sample configuration file with documentation
│   └── [project].yaml     # Project-specific configuration files
├── lib/
│   ├── fonts/             # Regular text fonts
│   ├── fonts_emoji/       # Emoji fonts (Noto Color Emoji recommended)
│   ├── music/             # Background music files
│   └── videos/            # Background video files
├── misc/
│   └── zonos_injection/   # Integration files for Zonos TTS server
├── output/                # Generated content organized by project
│   └── {project_name}/    # Project-specific output directory
│       ├── scenarios/     # Generated scenario files
│       ├── voice_lines/   # Generated voice lines
│       └── videos/        # Generated videos
├── make.py                # Master script that runs the entire pipeline
├── make_scenarios.py      # Script to generate scenario files
├── make_voice_lines.py    # Script to generate voice lines for scenarios
├── make_images.py         # Script to generate images for scenarios using ComfyUI
├── make_videos.py         # Script to generate videos from scenarios and voice lines
├── clean.py               # Utility to reset or clean generated content
├── name_videos.py         # Script to analyze and name video files based on content
└── register_fonts.py      # Tool to register fonts with ImageMagick
```

## Configuration Options

The configuration file (`configs/sample.yaml` or your custom config) supports the following options:

### Project Configuration

Each project has its own configuration file in the `configs/` directory (e.g., `motivation.yaml`, `spooky.yaml`). These files define:

1. **Themes**: A list of themes used to generate topics
2. **Prompts**:
   - **Topics**: Instructions for generating topics based on themes
   - **Scenario**: Instructions for creating slides based on topics

Example project configuration:

```yaml
themes:
  - urban_folklore
  - liminal_spaces
  - radio_static

prompts:
  topics:
    role: "You are an archivist..."
    instruction: "Based on the theme '{THEME}', generate 5 topics..."
    requirements:
      - "Make topics mysterious"
      - "Use plain English"

  scenario:
    role: "You are a writer..."
    instruction: "Create a story for the topic '{TOPIC}'..."
    constraints:
      - "Total duration: 8-16 seconds"
      - "3-9 words per slide"
```

### Video Configuration

```yaml
video:
  imagemagick_binary: "C:\\path\\to\\ImageMagick\\magick.exe"  # Path to ImageMagick binary
  background_music_volume: 0.2  # Volume multiplier for background music (0.0 to 1.0)
  voice_narration_volume: 1.0   # Volume multiplier for voice narration (0.0 to 1.0)
  use_consistent_font: true     # Use the same font for all slides in a scenario
  intro_delay: 1.0              # Delay in seconds before the first slide appears
  outro_delay: 1.0              # Delay in seconds after the last slide before the video ends
  emoji_enabled: true           # Whether to render emojis in videos
  emoji_font: "lib/noto_sans_emoji.ttf"  # Path to emoji font file (relative to project root)
  emoji_scale: 1.5              # Scale factor for emoji size (1.0 = normal, 1.5 = 50% larger)
  emoji_rotation:
    enabled: true               # Whether to randomly rotate emojis
    min_angle: -30              # Minimum rotation angle in degrees
    max_angle: 30               # Maximum rotation angle in degrees
```

### Voice Configuration

```yaml
voice:
  # TTS provider configuration ("zonos" or "orpheus")
  provider: "orpheus"
  
  # Zonos provider settings
  zonos_settings:
    tts_server: "http://localhost:5001/generate"  # URL of the Zonos TTS server
    speech_rate: "15"  # Speech rate (higher = faster)
    voice_samples:
      - "C:\\path\\to\\voice\\sample1.mp3"  # Path to voice sample files
      - "C:\\path\\to\\voice\\sample2.mp3"
  
  # Orpheus provider settings
  orpheus_settings:
    tts_server: "http://localhost:5005/v1/audio/speech"  # URL of the Orpheus TTS server
    model: "orpheus"  # Model name
    voice_presets: ["leah", "dan", "leo", "jess"]  # Available voice presets
    speed: 1  # Speed factor (0.1 to 1.0, lower is slower)
  
  # Audio post-processing settings
  postprocessing:
    normalization:
      target_db: -20.0  # Target dB level for audio normalization
      enabled: true     # Whether to automatically normalize generated voice lines
    silence_trimming:
      enabled: true     # Whether to trim silence from the end of voice lines
      max_silence_sec: 1.0  # Maximum silence to keep at the end in seconds
      threshold_db: -50  # Threshold in dB below which audio is considered silence
```

### Image Generation Configuration

```yaml
images:
  comfy_server_address: "127.0.0.1:8188"  # ComfyUI server address
  steps: 20                               # Default steps for image generation
  default_negative_prompt: "text, watermark, signature, blurry, distorted, low resolution"  # Default negative prompt
  generation_timeout: 60                  # Maximum wait time in seconds for image generation
  workflow: |                             # ComfyUI workflow JSON with placeholders
    {
      "6": {
        "inputs": {
          "text": "{PROMPT}",
          "clip": [ "30", 1 ]
        },
        "class_type": "CLIPTextEncode",
        "_meta": { "title": "CLIP Text Encode (Positive Prompt)" }
      },
      ...
    }
```

## Image Handling in Videos

DeepVideo2 intelligently handles background images in videos to ensure professional results:

1. **Aspect Ratio Awareness**: Images are resized based on their aspect ratio relative to the video frame:
   - For wider images: Resized based on height to ensure full height coverage
   - For taller images: Resized based on width to ensure full width coverage

2. **Full Frame Coverage**: All images are sized to completely fill the video frame, eliminating empty spaces

3. **Enhanced Text Visibility**: A semi-transparent black background is placed behind text to ensure readability regardless of the background image content

4. **Consistent Positioning**: Images are centered in the frame for visual consistency across slides

5. **Graceful Fallbacks**: Slides without background image descriptions are handled gracefully, with detailed logging to identify which slides are missing images

## Usage

### Setting Up ComfyUI for Image Generation

1. **Install ComfyUI**:
   - Follow the installation instructions at [ComfyUI GitHub repository](https://github.com/comfyanonymous/ComfyUI)

2. **Enable Developer Mode in ComfyUI**:
   - Open ComfyUI in your browser (typically at http://127.0.0.1:8188)
   - Click on the settings icon (gear) in the top-right corner
   - Enable "Developer mode" in the settings panel

3. **Create and Export Your Workflow**:
   - Build your desired image generation workflow in ComfyUI
   - Right-click on the background and select "Export" → "Save API format"
   - Save the JSON file

4. **Add Placeholders to Your Workflow**:
   - Open the exported JSON file in a text editor
   - Replace the prompt text with `{PROMPT}`
   - Replace the negative prompt text with `{NEGATIVE_PROMPT}`
   - Replace the seed value with `{SEED}` (without quotes)
   - Replace the steps value with `{STEPS}` (without quotes)

5. **Add the Workflow to Your Config**:
   - Copy the modified JSON into your project's config file under the `images.workflow` key

### Running the Pipeline

#### 1. Generate Scenarios

```
python make_scenarios.py -c configs/your_project.yaml -n 5
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-n, --iterations`: Number of scenarios to generate (default: 1)
- `-m, --model`: Model name to use (overrides config)

#### 2. Generate Voice Lines

```
python make_voice_lines.py -c configs/your_project.yaml
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-s, --scenario`: Specific scenario file to process (optional)
- `-f, --force`: Force regeneration of existing voice lines (optional)

#### 3. Generate Images

Generate background images for each slide in your scenarios:

```bash
python make_images.py -c configs/your_config.yaml
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-n, --num`: Number of scenarios to process (optional)
- `-s, --steps`: Override steps from config (optional)
- `-f, --force`: Force regeneration of existing images (optional)
- `-d, --debug`: Enable detailed debug logging (optional)

#### 4. Generate Videos

```
python make_videos.py -c configs/your_project.yaml
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-s, --scenario`: Specific scenario file to process (optional)
- `-v, --vertical`: Generate vertical (9:16) video (default)
- `-z, --horizontal`: Generate horizontal (16:9) video
- `-f, --force`: Force regeneration of existing videos (optional)
- `-q, --quality`: Quality factor for rendering (0.1-1.0, default: 1.0)

### Cleaning Up

To clean generated content:

```
python clean.py -c configs/your_project.yaml --videos --voices --images
```

Options:
- `-c, --config`: Path to the configuration file
- `--videos`: Clean generated video files
- `--voices`: Clean generated voice line files
- `--images`: Clean generated image files
- `--scenarios`: Clean generated scenario files
- `--all`: Clean all generated content for the project
- `--all-projects`: Clean all output directories (use with caution)
- `--dry-run`: Show what would be deleted without actually deleting anything

### Naming Background Videos

To automatically generate descriptive filenames for your background videos:

```
python name_videos.py [-m MODEL] [-f FRAMES]
```

This script:
1. Extracts frames from each video in the lib/videos folder
2. Analyzes each frame using an LLM to generate detailed descriptions
3. Creates a descriptive filename based on the visual content and mood
4. Renames the video files with the generated names

Options:
- `-m, --model`: Model name to use (default: gemma-3-4b-it)
- `-f, --frames`: Number of frames to extract per video (default: 5)
- `--min`: Minimum filename length (default: 32)
- `--max`: Maximum filename length (default: 128)

## Troubleshooting

### Voice Lines Not Working

- Make sure the Zonos TTS server is running and accessible at the URL specified in your config
- Check the `misc/zonos_injection/README.md` for setup instructions
- Verify that voice samples exist at the paths specified in your config

### Text Rendering Issues

- Ensure ImageMagick is properly installed and the path is correct in your config
- Run `python register_fonts.py` to register fonts with ImageMagick
- Check that the fonts directory contains valid font files

## License

MIT License

Copyright (c) 2025 DeepVideo2 Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
