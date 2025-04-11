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

## Project Structure

```
deepvideo2/
├── configs/               # Configuration files for different projects
├── lib/
│   ├── fonts/             # Regular text fonts
│   ├── fonts_emoji/       # Emoji fonts (Noto Color Emoji recommended)
│   ├── music/             # Background music files
│   └── videos/            # Background video files
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
└── register_fonts.py      # Tool to register fonts with ImageMagick
```

## Usage

### Configuration

Create a configuration file in the `configs/` directory (e.g., `configs/motivation.yaml`):

```yaml
# Project Information
project_name: "motivation"

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

# Prompt Configuration
prompts:
  # Topics and scenario generation prompts
  # ...
```

### Complete Pipeline

To run the entire pipeline (generate scenarios, voice lines, and videos):

```
python make.py -c configs/your_config.yaml -n 5 -q 0.5
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-n, --num`: Target number of scenarios/videos to have (default: 1)
- `-q, --quality`: Quality factor (1.0 = full quality, 0.5 = half resolution, default: 1.0)

The master script will:
1. Check how many scenarios already exist
2. Generate only the number needed to reach your target
3. Create voice lines for all scenarios
4. Generate videos for all unprocessed scenarios

### Individual Steps

You can also run each step individually:

#### 1. Generate Scenarios

```
python make_scenarios.py -c configs/your_config.yaml -n 3
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-n, --num`: Number of scenarios to generate (default: 1)

#### 2. Generate Voice Lines

```
python make_voice_lines.py -c configs/your_config.yaml
```

Options:
- `-c, --config`: Path to the configuration file (required)

#### 3. Generate Videos

```
python make_videos.py -c configs/your_config.yaml -n -1 -q 0.5
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-n, --num`: Number of videos to generate (-1 for all unprocessed scenarios, default: -1)
- `-q, --quality`: Quality factor (1.0 = full quality, 0.5 = half resolution, default: 1.0)

### Cleaning and Resetting

To reset the processed status of scenarios or clean generated content:

```
python clean.py -c configs/your_config.yaml [-h]
```

Options:
- `-c, --config`: Path to the configuration file (required)
- `-h, --hard`: Perform a hard clean (delete all generated content)

## Scenario File Format

Scenario files use YAML format with the following structure:

```yaml
music: music_file.mp3
video: background_video.mp4
has_video: false  # Set to true when processed
slides:
  - duration_seconds: 2
    text: First slide text
    emotion: happiness
  - duration_seconds: 3
    text: Second slide with emoji 🎉
    emotion: surprise
  - duration_seconds: 2
    text: Final slide
    emotion: neutral
```

- `music`: Background music file (located in lib/music/)
- `video`: Background video file (located in lib/videos/)
- `has_video`: Flag indicating whether this scenario has been processed
- `slides`: List of slides with text, emotion, and duration
  - `duration_seconds`: How long to display this slide
  - `text`: The text to display
  - `emotion`: The emotion for this slide (happiness, sadness, surprise, etc.)

## Troubleshooting

### Font Issues

If text isn't rendering with the correct font:

1. Ensure fonts are properly registered with ImageMagick:
   ```
   python register_fonts.py
   ```

2. Check the console output for font loading errors

3. For Windows users: Make sure ImageMagick is correctly installed and the path is set in the environment variables

### Video Generation Issues

If video generation fails:

1. Check that all required files (music, video) exist in the correct directories
2. Verify the YAML scenario file format is correct
3. Look for error messages in the console output
4. Make sure the config file path is correct and accessible

## License

MIT License

Copyright (c) 2025 @sanyabeast (Ukraine)

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

## Author

Created by [@sanyabeast](https://github.com/sanyabeast) from Ukraine, 2025.

## Credits

- LM Studio for providing the local LLM capabilities
- MoviePy for video editing capabilities
- ImageMagick for text rendering
- Pillow (PIL) for image processing
- Emoji library for emoji handling
- YAML for configuration parsing
- Librosa and SoundFile for audio normalization
