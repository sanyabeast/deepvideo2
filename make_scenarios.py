import lmstudio as lms
from pydantic import BaseModel
import random
import yaml
import os
import re
import argparse

# ─────────────────────────────────────────────────────
# 🎲 CONFIGURATION
# ─────────────────────────────────────────────────────
seed = random.randint(0, 1000000)
default_model_name = "meta-llama-3.1-8b-instruct"
emotions = [
    "happiness",
    "sadness",
    "disgust",
    "fear",
    "surprise",
    "anger",
    "neutral"
]

# ─────────────────────────────────────────────────────
# 📦 MODELS
# ─────────────────────────────────────────────────────
class ScenarioSlide(BaseModel):
    text: str
    emotion: str
    duration_seconds: int

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
def to_snake_case(text: str) -> str:
    text = re.sub(r'[^\w\s]', '', text).lower()
    return re.sub(r'\s+', '_', text)

def get_existing_topics():
    """Get a list of existing topics from scenario files."""
    scenarios_dir = "scenarios"
    existing_topics = []
    
    if not os.path.exists(scenarios_dir):
        return existing_topics
    
    for filename in os.listdir(scenarios_dir):
        if filename.endswith('.yaml'):
            filepath = os.path.join(scenarios_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    scenario = yaml.safe_load(f)
                    if scenario and 'topic' in scenario:
                        existing_topics.append(scenario['topic'])
            except Exception as e:
                print(f"⚠️ Error reading {filename}: {str(e)}")
    
    return existing_topics

def get_available_music(limit=6):
    music_dir = os.path.join("lib", "music")
    all_music = [f for f in os.listdir(music_dir) if os.path.isfile(os.path.join(music_dir, f))]
    # Randomly select a subset if we have more than the limit
    if len(all_music) > limit:
        return random.sample(all_music, limit)
    return all_music

def get_available_videos(limit=6):
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
    print_header(f"Generating fresh motivational topics (seed: {seed})")
    
    if existing_topics and len(existing_topics) > 0:
        print_subheader(f"🔍 Avoiding {len(existing_topics)} existing topics")
    
    chat = lms.Chat()
    
    prompt = """
You are a creative and insightful motivational content strategist for short-form video platforms (TikTok, Reels, YouTube Shorts).

Generate a list of 5 **fresh and unconventional motivational video topics**. Avoid cliché, overused ideas like "overcoming fear" or "imposter syndrome". Be unique, thought-provoking, and modern.

Each topic should:
- Be specific and catchy
- Appeal to younger audiences (Gen Z, Millennials)
- Spark curiosity or emotion
- Be suitable for short, powerful videos
- Use only plain ENGLISH words and phrases.
- Do NOT include emojis, icons, or non-standard symbols.
- Do NOT use non-English languages or phrases.
"""

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
    
    # Get available media files (limited to 6 each)
    available_music = get_available_music(6)
    available_videos = get_available_videos(6)
    
    print_subheader("🎵 Available music files:")
    for i, music in enumerate(available_music, 1):
        print(f"  {i}. {music}")
    
    print_subheader("🎬 Available video files:")
    for i, video in enumerate(available_videos, 1):
        print(f"  {i}. {video}")

    chat = lms.Chat()
    chat.add_user_message(f"""
You are a short-form video copywriter crafting motivational videos for TikTok, Reels, and YouTube Shorts.

🎯 Your task:
Create a **micro-story split into short slides** (like Instagram story frames) for the topic: "{topic}"

📏 Constraints:
- Total video duration: **8-16 seconds max**
- Each slide: **very short sentence or phrase**, 3–8 words
- Each slide duration: **1 to 4 seconds** (max)
- Max 8 slides
- Each slide MUST be assigned ONE of these specific emotions: {", ".join(emotions)}

📢 Style:
- Ultra-punchy and emotionally charged
- Hooks the viewer in slide 1
- Builds emotional or motivational momentum
- Uses rhythm, repetition, shock, or questions
- Ends strong with a bold punchline or insight
- Use everyday, casual Gen Z language
- Use only plain ENGLISH for all text.
- Do NOT include emojis, emoticons, icons, or non-standard symbols.
- Do NOT include non-English words, slang from other languages, or cultural references that may require translation.

🎵 Available music files (select one that fits the mood):
{", ".join(available_music)}

🎬 Available video files (select one that fits the theme):
{", ".join(available_videos)}

📦 Format your response as JSON:
{{
  "topic": "...",
  "slides": [
    {{ "text": "Slide 1", "emotion": "one of the emotions from the list", "duration_seconds": 2 }},
    {{ "text": "Slide 2", "emotion": "one of the emotions from the list", "duration_seconds": 3 }},
    ...
  ],
  "music": "Selected music filename from the list",
  "video": "Selected video filename from the list"
}}
""")

    prediction = model.respond(chat, response_format=ScenarioDescription)
    scenario = prediction.parsed

    print_subheader("🎬 Slides:")
    for idx, slide in enumerate(scenario["slides"], 1):
        print(f"  {idx}. \"{slide['text']}\" - {slide['emotion']} ({slide['duration_seconds']}s)")
    
    print_subheader("🎵 Selected music:")
    print(f"  {scenario['music']}")
    
    print_subheader("🎬 Selected video:")
    print(f"  {scenario['video']}")

    return scenario

def save_yaml(filename: str, data: dict):
    output_dir = "scenarios"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)

    print_subheader(f"✅ Scenario saved as: {filepath}")

# ─────────────────────────────────────────────────────
# 🚀 MAIN ENTRY
# ─────────────────────────────────────────────────────
def main():
    global seed
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate motivational video scenarios')
    parser.add_argument('-n', '--iterations', type=int, default=1, 
                        help='Number of scenarios to generate (default: 1)')
    parser.add_argument('-m', '--model', type=str, default=default_model_name,
                        help=f'Model name to use (default: {default_model_name})')
    args = parser.parse_args()
    
    # Initialize the model with the specified model name
    model_name = args.model
    model = lms.llm(model_name, config={
        "seed": seed,
    })
    
    print(f"\n✨ Using model: {model_name}")
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

if __name__ == "__main__":
    main()
