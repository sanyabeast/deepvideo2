# Zonos TTS Server Injection

## What is this?

This folder contains code that helps DeepVideo2 talk to the Zonos Text-to-Speech (TTS) server. It's like a translator between DeepVideo2 and Zonos, allowing our program to create voice lines with different emotions.

## How to Set It Up

Setting this up is like adding a special ingredient to a recipe. You need to:

1. **Copy the HTTP Server**: Take the `http_server.py` file and place it inside your Zonos app folder.

2. **Update the Zonos App**: Find the `gradio_interface.py` file in your Zonos app and add our special code to it.

### Step-by-Step Instructions

#### 1. Copy the File
Copy `http_server.py` from this folder to your Zonos app folder.

#### 2. Update the Zonos App
Open the `gradio_interface.py` file in your Zonos app and make these two changes:

**First**: Add this import at the top of the file (with the other imports):
```python
from http_server import InjectedServer
```

**Second**: Find the `build_interface()` function and add this line just before the `return demo` statement:
```python
injected_server = InjectedServer(custom_hook)
```

## How It Works (In Simple Terms)

Imagine you have two people who speak different languages trying to talk to each other:

1. DeepVideo2 wants to say "Create a voice line with a happy emotion"
2. Our HTTP server acts as a translator
3. The translator tells Zonos what DeepVideo2 wants
4. Zonos creates the voice and gives it back to the translator
5. The translator gives the voice back to DeepVideo2

This way, DeepVideo2 can create voice lines with different emotions without having to know how to speak directly to Zonos.

## Testing It

After setting everything up:

1. Start your Zonos app
2. The HTTP server will automatically start listening on port 5001
3. DeepVideo2 will be able to send requests to `http://localhost:5001/generate`

If everything is working correctly, you'll see messages in your Zonos console when DeepVideo2 requests a new voice line.

## Need Help?

If you run into any problems, check that:
- The `http_server.py` file is in the right place
- You've added both code snippets to `gradio_interface.py`
- The Zonos app is running before you try to generate voice lines with DeepVideo2
