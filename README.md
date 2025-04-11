# DeepVideo2

A powerful tool for generating engaging motivational videos from text-based scenarios with custom fonts, emoji support, and dynamic content.

## Overview

DeepVideo2 is a Python-based video generation system that transforms YAML scenario files into polished videos with text overlays, background music, and visual elements. The system handles emoji rendering, custom fonts, and various quality settings to produce professional-looking content with minimal effort.

## Features

- **Text-to-Video Generation**: Convert YAML scenario files into complete videos with text overlays
- **Emoji Support**: Proper rendering of emoji characters in video text
- **Custom Font Integration**: Use custom fonts for text rendering with proper ImageMagick integration
- **Background Music**: Add music tracks to your videos with automatic matching
- **Background Video**: Incorporate video backgrounds with proper sizing and positioning
- **Quality Control**: Adjust output quality for different use cases
- **Vertical/Horizontal Formats**: Support for both 9:16 (vertical) and 16:9 (horizontal) aspect ratios
- **Project-Based Organization**: Organize all generated content by project name
- **Audio Normalization**: Automatically normalize voice lines for consistent audio levels
- **Intelligent Workflow**: Generate only the number of scenarios needed to reach your target
- **Voice Line Generation**: Create voice narration for each slide with emotion control
- **Flexible Configuration**: Use project-specific configuration files in the configs/ directory
- **Automatic Video Naming**: Generate descriptive filenames for background videos based on visual content
- **Configurable Timing**: Set custom intro and outro delays for professional-looking videos

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
├── make_videos.py         # Script to generate videos from scenarios and voice lines
├── clean.py               # Utility to reset or clean generated content
├── name_videos.py         # Script to analyze and name video files based on content
└── register_fonts.py      # Tool to register fonts with ImageMagick
```

## Usage

### Configuration

Create a configuration file in the `configs/` directory (e.g., `configs/motivation.yaml`). The filename (without extension) will be used as the project name:

```yaml
# LLM Configuration
llm:
  default_model: "meta-llama-3.1-8b-instruct"
  seed: 0  # Will be randomized at runtime if not specified

# Voice Generation Configuration
voice:
  zonos_tts_server: "http://localhost:5001/generate"
  voice_samples:
    - "path/to/voice/sample1.mp3"
    - "path/to/voice/sample2.mp3"
  speech_rate: "15"
  normalization:
    target_db: -20.0  # Target dB level for audio normalization
    enabled: true     # Whether to automatically normalize generated voice lines

# Video Generation Configuration
video:
  imagemagick_binary: "path/to/magick.exe"
  background_music_volume: 0.2  # Volume multiplier for background music
  voice_narration_volume: 1.0   # Volume multiplier for voice narration
  use_consistent_font: true     # Use the same font for all slides in a scenario
  intro_delay: 1.0              # Delay in seconds before the first slide appears
  outro_delay: 1.0              # Delay in seconds after the last slide before the video ends

# Media Options
media_options:
  music_files_count: 10  # Number of music files to show in scenario generation
  video_files_count: 10  # Number of video files to show in scenario generation
```

You can use the provided `configs/sample.yaml` as a template.

### Running the Pipeline

The easiest way to run the entire pipeline is to use the master script:

```
python make.py -c configs/your_project.yaml -n 5
```

This will:
1. Check how many scenarios already exist for your project
2. Generate new scenarios if needed to reach the target number
3. Generate voice lines for all scenarios
4. Generate videos for all scenarios

Options:
- `-c, --config`: Path to the configuration file (required)
- `-n, --num`: Target number of videos to generate (default: 1)
- `-q, --quality`: Quality factor for rendering (0.1-1.0, default: 1.0)

### Individual Steps

If you prefer to run each step separately:

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

#### 3. Generate Videos

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
python clean.py -c configs/your_project.yaml -r
```

Options:
- `-c, --config`: Path to the configuration file
- `-r, --reset`: Reset the has_video property in scenario files
- `-d, --hard`: Delete all generated content for the project
- `-a, --all`: Delete ALL output directories (use with caution)

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
