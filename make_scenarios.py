import lmstudio as lms
from pydantic import BaseModel
import random
import yaml
import os
import re
import argparse
import sys

# Import configuration utilities
from utils.config_utils import load_config

# Get the absolute path of the project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

# ─────────────────────────────────────────────────────
# 🎲 CONFIGURATION
# ─────────────────────────────────────────────────────

# Global variables
CONFIG = None
seed = None
default_model_name = None
emotions = None

# ─────────────────────────────────────────────────────
# 📦 MODELS
# ─────────────────────────────────────────────────────
class ScenarioSlide(BaseModel):
    text: str
    emotion: str
    has_emoji: bool
    emoji: str
    duration_seconds: int
    background_image_description: str = ""

class ScenarioDescription(BaseModel):
    topic: str
    slides: list[ScenarioSlide]
    music: str
    video: str

class TopicsList(BaseModel):
    topics: list[str]

# ─────────────────────────────────────────────────────
# 🐍 UTILITIES
# ─────────────────────────────────────────────────────
def to_snake_case(text: str):
    """Convert text to snake case for filenames."""
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text).lower()
    # Replace spaces with underscores
    return re.sub(r'\s+', '_', text)

def clean_text(text: str):
    """Clean text to remove special characters and non-English symbols.
    
    This function removes:
    - Unicode special characters
    - Emojis
    - Non-English letters
    - Special symbols
    
    It preserves:
    - English letters (a-z, A-Z)
    - Numbers (0-9)
    - Basic punctuation (,.?!-'":+=)
    - Spaces
    
    It also normalizes all quotes to single quotes for consistency.
    """
    # Replace ellipsis and other common special characters with their simple equivalents
    text = text.replace('\u2026', '...').replace('\u2019', "'").replace('\u201c', "'").replace('\u201d', "'")
    
    # Normalize all double quotes to single quotes
    text = text.replace('"', "'")
    
    # Keep only allowed characters: English letters, numbers, basic punctuation, and spaces
    cleaned_text = re.sub(r'[^\w\s,.?!\'"\-:+=]', '', text)
    
    # Replace multiple spaces with a single space
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    # Trim leading/trailing whitespace
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

def extract_emojis(text: str):
    """Extract emojis from text."""
    emojis = []
    for char in text:
        if char.isprintable() and not char.isascii():
            emojis.append(char)
    return emojis

def get_existing_topics():
    """Get a list of existing topics from scenario files."""
    existing_topics = []
    
    # Check if scenarios directory exists
    scenarios_dir = os.path.join(PROJECT_DIR, "output", CONFIG.get("project_name"), CONFIG["directories"]["scenarios"])
    if not os.path.exists(scenarios_dir):
        return existing_topics
    
    # Iterate through all YAML files in the scenarios directory
    for filename in os.listdir(scenarios_dir):
        if filename.endswith('.yaml'):
            filepath = os.path.join(scenarios_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    scenario = yaml.safe_load(f)
                    if scenario and 'topic' in scenario:
                        existing_topics.append(scenario['topic'])
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return existing_topics

def get_available_music(limit=None):
    """Get a list of available music files."""
    if limit is None:
        # Get the limit from config, default to 16 if not specified
        limit = CONFIG.get("media_options", {}).get("music_files_count", 16)
    
    music_dir = os.path.join("lib", "music")
    all_music = [f for f in os.listdir(music_dir) if os.path.isfile(os.path.join(music_dir, f))]
    # Randomly select a subset if we have more than the limit
    if len(all_music) > limit:
        return random.sample(all_music, limit)
    return all_music

def get_available_videos(limit=None):
    """Get a list of available video files."""
    if limit is None:
        # Get the limit from config, default to 16 if not specified
        limit = CONFIG.get("media_options", {}).get("video_files_count", 16)
    
    videos_dir = os.path.join("lib", "videos")
    all_videos = [f for f in os.listdir(videos_dir) if os.path.isfile(os.path.join(videos_dir, f))]
    # Randomly select a subset if we have more than the limit
    if len(all_videos) > limit:
        return random.sample(all_videos, limit)
    return all_videos

def print_header(title: str):
    print(f"\n{'='*50}")
    print(f"🧠  {title}")
    print(f"{'='*50}")

def print_subheader(title: str):
    print(f"\n👉 {title}")

# ─────────────────────────────────────────────────────
# 🧠 LLM PROMPTS
# ─────────────────────────────────────────────────────
def get_topics(model, existing_topics=None) -> TopicsList:
    print_header(f"Generating fresh topics (seed: {seed})")
    
    if existing_topics and len(existing_topics) > 0:
        print_subheader(f"🔍 Avoiding {len(existing_topics)} existing topics")
    
    chat = lms.Chat()
    
    # Get prompt components from config
    role = CONFIG["prompts"]["topics"]["role"]
    instruction = CONFIG["prompts"]["topics"]["instruction"]
    requirements = CONFIG["prompts"]["topics"]["requirements"]
    
    # Build the prompt
    prompt = f"""
        {role}

        {instruction}

        Each topic should:
        """
    
    # Add requirements from config
    for req in requirements:
        prompt += f"- {req}\n"

    # Add existing topics to avoid if any
    if existing_topics and len(existing_topics) > 0:
        # Always randomize the list of topics to avoid prompt getting too large
        # and to ensure we're not always showing the same examples
        max_examples = 32  # Maximum number of examples to include in the prompt
        
        if len(existing_topics) > max_examples:
            # If we have more than max_examples, randomly select max_examples
            examples = random.sample(existing_topics, max_examples)
            print_subheader(f"🔍 Showing {max_examples} random examples out of {len(existing_topics)} existing topics")
        else:
            # If we have fewer than max_examples, use all of them but in random order
            examples = random.sample(existing_topics, len(existing_topics))
        
        prompt += f"""
            IMPORTANT: Avoid creating topics similar to these existing ones:
            {chr(10).join(['- ' + topic for topic in examples])}

            Make sure your topics are COMPLETELY DIFFERENT from the above.
            """

    prompt += """
        Output a JSON like:
        {
        "topics": ["...", "...", "...", "...", "..."]
        }
        """

    chat.add_user_message(prompt)

    prediction = model.respond(chat, response_format=TopicsList)
    topics = prediction.parsed["topics"]

    print_subheader("📋 Topics generated:")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t}")
    
    return topics

def get_scenario(model, topic):
    print_header(f"Creating short-form video scenario for:\n📌 {topic}")
    
    # Get available media files with configurable limits from config
    available_music = get_available_music()
    available_videos = get_available_videos()
    
    print_subheader("🎵 Available music files:")
    for i, music in enumerate(available_music, 1):
        print(f"  {i}. {music}")
    
    print_subheader("🎬 Available video files:")
    for i, video in enumerate(available_videos, 1):
        print(f"  {i}. {video}")

    # Get prompt components from config
    role = CONFIG["prompts"]["scenario"]["role"]
    instruction = CONFIG["prompts"]["scenario"]["instruction"].format(topic=topic)
    constraints = CONFIG["prompts"]["scenario"]["constraints"]
    style = CONFIG["prompts"]["scenario"]["style"]
    
    chat = lms.Chat()
    
    # Build the prompt
    prompt = f"""
        {role}

        🎯 Your task:
        {instruction}

        📏 Constraints:
        """
    
    # Add constraints from config
    for constraint in constraints:
        prompt += f"- {constraint}\n"
    
    # Add the emotion constraint which is specific to the code
    prompt += f"- Each slide MUST be assigned ONE of these specific emotions: {', '.join(emotions)}\n"
    
    # Add emoji constraint
    prompt += f"- For some slides (randomly chosen), add a single emoji that reinforces the emotion or message\n"
    prompt += f"- The emoji should be relevant to the slide content and emotion\n"
    prompt += f"- Set has_emoji to true for slides with an emoji, false for others\n"
    prompt += f"- Aim to include emojis in about 30-50% of slides\n"
    
    # Add background image description constraint
    prompt += f"- For EACH slide, provide a field called background_image_description.\n"
    prompt += f"- This should be a **visually rich and concrete description** of the ideal image for the slide background.\n"
    prompt += f"- It must be suitable for high-quality text-to-image generation tools like Stable Diffusion, DALL·E, or Midjourney.\n"
    prompt += f"- Describe the **scene layout**, **environment**, **color palette**, and **lighting** in 10–30 words.\n"
    prompt += f"- Align the description closely with the slide's emotion and content.\n"
    prompt += f"- Use **descriptive adjectives and nouns**, such as: misty forest, neon skyline, ancient ruins, warm sunset.\n"
    prompt += f"- Mention **style or aesthetic** if appropriate, e.g. surrealism, photorealism, cinematic, moody, pastel.\n"
    prompt += f"- DO NOT include any text elements in the image description (e.g., no signs, subtitles, or captions).\n"
    prompt += f"- DO NOT include the word 'image' or 'background' — just the visual scene.\n"
    
    prompt += "\n📢 Style:\n"
    
    # Add style guidelines from config
    for style_point in style:
        prompt += f"- {style_point}\n"
    
    # Add available media options (this is service-specific and stays in the code)
    prompt += f"""
        🎵 Available music files (select one that fits the mood):
        {", ".join(available_music)}

        🎬 Available video files (select one that fits the theme):
        {", ".join(available_videos)}

        📦 Format your response as JSON:
        {{
        "topic": "...",
        "slides": [
            {{ 
            "text": "Slide 1", 
            "emotion": "one of the emotions from the list", 
            "duration_seconds": 2,
            "has_emoji": true or false (randomly decide for each slide),
            "emoji": "a single emoji that reinforces the emotion or message (only if has_emoji is true, otherwise leave empty)",
            "background_image_description": "A brief description of the background image (optional)"
            }},
            {{ 
            "text": "Slide 2", 
            "emotion": "one of the emotions from the list", 
            "duration_seconds": 3,
            "has_emoji": true or false (randomly decide for each slide),
            "emoji": "a single emoji that reinforces the emotion or message (only if has_emoji is true, otherwise leave empty)",
            "background_image_description": "A brief description of the background image (optional)"
            }},
            ...
        ],
        "music": "Selected music filename from the list",
        "video": "Selected video filename from the list"
        }}
        """

    chat.add_user_message(prompt)

    prediction = model.respond(chat, response_format=ScenarioDescription)
    scenario = prediction.parsed
    
    # Clean the text in each slide to remove special characters and non-English symbols
    for slide in scenario["slides"]:
        slide["text"] = clean_text(slide["text"])
        
        # Ensure emoji fields have valid values
        if "has_emoji" not in slide:
            slide["has_emoji"] = False
        
        if "emoji" not in slide or not slide["has_emoji"]:
            slide["emoji"] = ""
        elif slide["has_emoji"]:
            # Keep only a single emoji if multiple were provided
            emojis = extract_emojis(slide["emoji"])
            if emojis:
                slide["emoji"] = emojis[0]  # Keep only the first emoji
            else:
                # If no valid emoji was found, set has_emoji to False
                slide["has_emoji"] = False
                slide["emoji"] = ""

        # Ensure background_image_description field has a valid value
        if "background_image_description" not in slide:
            slide["background_image_description"] = ""

    print_subheader("🎬 Slides:")
    for idx, slide in enumerate(scenario["slides"], 1):
        emoji_display = f" [{slide['emoji']}]" if slide["has_emoji"] else ""
        print(f"  {idx}. \"{slide['text']}\"{emoji_display} - {slide['emotion']} ({slide['duration_seconds']}s)")
        if slide["background_image_description"]:
            print(f"     🖼️ Background: {slide['background_image_description']}")
    
    print_subheader("🎵 Selected music:")
    print(f"  {scenario['music']}")
    
    print_subheader("🎬 Selected video:")
    print(f"  {scenario['video']}")

    return scenario

def save_yaml(filename, data):
    """Save data to a YAML file in the scenarios directory."""
    # Get the project name from the config
    project_name = CONFIG.get("project_name")
    scenarios_dir = os.path.join(PROJECT_DIR, "output", project_name, CONFIG["directories"]["scenarios"])
    os.makedirs(scenarios_dir, exist_ok=True)
    
    # Save the file
    filepath = os.path.join(scenarios_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"👉 ✅ Scenario saved as: {os.path.relpath(filepath, PROJECT_DIR)}")
    return filepath

# ─────────────────────────────────────────────────────
# 🚀 MAIN ENTRY
# ─────────────────────────────────────────────────────
def main():
    global seed, CONFIG, default_model_name, emotions
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate video scenarios')
    parser.add_argument('-c', '--config', type=str, required=True,
                        help='Path to the configuration file')
    parser.add_argument('-n', '--iterations', type=int, default=1, 
                        help='Number of scenarios to generate (default: 1)')
    parser.add_argument('-m', '--model', type=str,
                        help='Model name to use')
    args = parser.parse_args()
    
    # Load configuration
    CONFIG = load_config(args.config)
    
    # Get project name from config
    project_name = CONFIG.get("project_name")
    print(f"DEBUG: Config file: {args.config}")
    print(f"DEBUG: Project name from config: {project_name}")
    
    # Print startup message
    print(f"\n🚀 Starting {project_name} scenario generation")
    
    # Set seed if not specified in config
    seed = CONFIG.get("llm", {}).get("seed", random.randint(0, 1000000))
    if seed == 0:  # If seed is 0, randomize it
        seed = random.randint(0, 1000000)
    
    # Get default model name from config
    default_model_name = CONFIG["llm"]["default_model"]
    
    # Get emotions list from config
    emotions = CONFIG["emotions"]
    
    # If model not specified in command line, use the default from config
    if args.model is None:
        args.model = default_model_name
    
    # Initialize the model with the specified model name
    model_name = args.model
    model = lms.llm(model_name, config={
        "seed": seed,
    })
    
    print(f"✨ Using model: {model_name}")
    print(f"🔑 Random seed: {seed}")
    
    # Get existing topics to avoid duplicates
    existing_topics = get_existing_topics()
    if existing_topics:
        print(f"📚 Found {len(existing_topics)} existing scenarios")
    
    # Run the specified number of iterations
    for i in range(args.iterations):
        if args.iterations > 1:
            print(f"\n🔄 Iteration {i+1}/{args.iterations}")
            # Generate a new seed for each iteration except the first one
            if i > 0:
                seed = random.randint(0, 1000000)
                print(f"🔑 New seed: {seed}")
                # Update model seed for new iteration
                model = lms.llm(model_name, config={
                    "seed": seed,
                })
        
        # Get topics, avoiding existing ones
        topics = get_topics(model, existing_topics)
        selected_topic = random.choice(topics)
        
        print_subheader(f"🎯 Selected topic: {selected_topic}")
        
        scenario = get_scenario(model, selected_topic)
        
        snake_topic = to_snake_case(selected_topic)
        filename = f"{seed}_{snake_topic[:128]}.yaml"
        save_yaml(filename, scenario)
        
        # Add the new topic to existing topics to avoid duplicates in subsequent iterations
        existing_topics.append(selected_topic)
    
    print("\n🎉 All done!")
    
    # Unload the model to free up resources
    model.unload()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user (Ctrl+C)")
        print("🛑 Exiting gracefully...")
        sys.exit(130)  # Standard exit code for SIGINT
