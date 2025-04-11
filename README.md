# DeepVideo2

A powerful tool for generating engaging videos from text-based scenarios with custom fonts, emoji support, and dynamic content.

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
├── lib/
│   ├── fonts/             # Regular text fonts
│   ├── fonts_emoji/       # Emoji fonts (Noto Color Emoji recommended)
│   ├── music/             # Background music files
│   └── videos/            # Background video files
├── output/                # Generated videos are saved here
├── scenarios/             # YAML scenario files
├── make_video.py          # Main video generation script
├── make_scenarios.py      # Helper script to create scenario files
├── register_fonts.py      # Tool to register fonts with ImageMagick
└── reset.py               # Utility to reset processed status of scenarios
```

## Usage

### Generating Videos

To generate a video from a scenario file:

```
python make_video.py -s scenarios/your_scenario.yaml
```

Options:
- `-s, --scenario`: Path to the scenario file
- `-f, --force`: Force processing even if the scenario has already been processed
- `-q, --quality`: Quality factor (1.0 = full quality, 0.5 = half resolution)
- `--horizontal`: Generate horizontal (16:9) videos instead of vertical (9:16)
- `-n, --num-videos`: Number of videos to generate (use -1 for all available scenarios)

### Creating Scenario Files

The `make_scenarios.py` script helps generate scenario files from templates or AI-generated content.

### Font Registration

Register custom fonts with ImageMagick for proper text rendering:

```
python register_fonts.py
```

Options:
- `-p, --path`: Custom path to ImageMagick's type-ghostscript.xml file

## Scenario File Format

Scenario files use YAML format with the following structure:

```yaml
music: music_file.mp3
video: background_video.mp4
topic: Your Video Topic
slides:
  - duration_seconds: 2
    text: First slide text
  - duration_seconds: 3
    text: Second slide with emoji 🎉
  - duration_seconds: 2
    text: Final slide
```

- `music`: Background music file (located in lib/music/)
- `video`: Background video file (located in lib/videos/)
- `topic`: The main topic/title of the video
- `slides`: List of slides with text and duration
  - `duration_seconds`: How long to display this slide
  - `text`: The text to display (supports emoji and markdown-style formatting)

## Font Handling

DeepVideo2 supports custom fonts for text rendering:

1. Place regular fonts (.ttf or .otf) in the `lib/fonts/` directory
2. Place emoji fonts in the `lib/fonts_emoji/` directory (Noto Color Emoji recommended)
3. Run `register_fonts.py` to register these fonts with ImageMagick

The system will:
- Use random fonts from the appropriate directories
- Properly handle emoji rendering
- Apply text styling with appropriate stroke width based on quality settings

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

- MoviePy for video editing capabilities
- ImageMagick for text rendering
- Pillow (PIL) for image processing
- Emoji library for emoji handling
- YAML for configuration parsing
