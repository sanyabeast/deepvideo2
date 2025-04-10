import lmstudio as lms
from pydantic import BaseModel
import random
import yaml
import os
import re

# ─────────────────────────────────────────────────────
# 🎲 CONFIGURATION
# ─────────────────────────────────────────────────────
seed = random.randint(0, 1000000)
model_name = "gemma-3-12b-it"

model = lms.llm(model_name, config={
    "seed": seed,
})

# ─────────────────────────────────────────────────────
# 📦 MODELS
# ─────────────────────────────────────────────────────
class ScenarioSlide(BaseModel):
    text: str
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

def get_available_music():
    music_dir = os.path.join("lib", "music")
    return [f for f in os.listdir(music_dir) if os.path.isfile(os.path.join(music_dir, f))]

def get_available_videos():
    videos_dir = os.path.join("lib", "videos")
    return [f for f in os.listdir(videos_dir) if os.path.isfile(os.path.join(videos_dir, f))]

def print_header(title: str):
    print(f"\n{'='*50}")
    print(f"🧠  {title}")
    print(f"{'='*50}")

def print_subheader(title: str):
    print(f"\n👉 {title}")

# ─────────────────────────────────────────────────────
# 🧠 LLM PROMPTS
# ─────────────────────────────────────────────────────
def get_topics() -> TopicsList:
    print_header(f"Generating fresh motivational topics (seed: {seed})")

    chat = lms.Chat()
    chat.add_user_message("""
You are a creative and insightful motivational content strategist for short-form video platforms (TikTok, Reels, YouTube Shorts).

Generate a list of 5 **fresh and unconventional motivational video topics**. Avoid cliché, overused ideas like "overcoming fear" or "imposter syndrome". Be unique, thought-provoking, and modern.

Each topic should:
- Be specific and catchy
- Appeal to younger audiences (Gen Z, Millennials)
- Spark curiosity or emotion
- Be suitable for short, powerful videos

Output a JSON like:
{
  "topics": ["...", "...", "...", "...", "..."]
}
""")

    prediction = model.respond(chat, response_format=TopicsList)
    topics = prediction.parsed["topics"]

    print_subheader("📋 Topics generated:")
    for i, t in enumerate(topics, 1):
        print(f"  {i}. {t}")
    
    return topics

def get_scenario(topic):
    print_header(f"Creating short-form video scenario for:\n📌 {topic}")
    
    # Get available media files
    available_music = get_available_music()
    available_videos = get_available_videos()
    
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
- Total video duration: **5–15 seconds max**
- Each slide: **very short sentence or phrase**, 3–8 words
- Each slide duration: **1 to 4 seconds** (max)
- Max 5 slides

📢 Style:
- Ultra-punchy and emotionally charged
- Hooks the viewer in slide 1
- Builds emotional or motivational momentum
- Uses rhythm, repetition, shock, or questions
- Ends strong with a bold punchline or insight
- Use everyday, casual Gen Z language

🎵 Available music files (select one that fits the mood):
{", ".join(available_music)}

🎬 Available video files (select one that fits the theme):
{", ".join(available_videos)}

📦 Format your response as JSON:
{{
  "topic": "...",
  "slides": [
    {{ "text": "Slide 1", "duration_seconds": 2 }},
    {{ "text": "Slide 2", "duration_seconds": 3 }},
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
        print(f"  {idx}. \"{slide["text"]}\" ({slide["duration_seconds"]}s)")
    
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
    print(f"\n✨ Using model: {model_name}")
    print(f"🔑 Random seed: {seed}")

    topics = get_topics()
    selected_topic = random.choice(topics)
    
    print_subheader(f"🎯 Selected topic: {selected_topic}")

    scenario = get_scenario(selected_topic)

    snake_topic = to_snake_case(selected_topic)
    filename = f"{seed}_{snake_topic[:128]}.yaml"
    save_yaml(filename, scenario)

    print("\n🎉 All done!")

if __name__ == "__main__":
    main()
