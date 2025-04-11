# ------------------------------------------------------
# INJECTION
# ------------------------------------------------------
import soundfile as sf 
from http_server import InjectedServer
# ------------------------------------------------------
# END INJECTION
# ------------------------------------------------------


def build_interface(): 
    ...
    # ------------------------------------------------------
    # INJECTION
    # ------------------------------------------------------
    def custom_hook(params):
        print("Hook called with:", params)

        text = params.get("text", "")
        if not text.strip():
            print("No text provided.")
            return

        # Get optional path param
        save_path = params.get("path", "output.wav")

        model_choice = "Zyphra/Zonos-v0.1-transformer"
        language = "en-us"
        speaker_audio = params.get("voice", None)
        prefix_audio = "assets/silence_100ms.wav"

        # Emotions
        emotion = params.get("emotion", "happiness").lower()
        e = [
            1.0 if emotion == "happiness" else 0.0,
            1.0 if emotion == "sadness" else 0.0,
            1.0 if emotion == "disgust" else 0.0,
            1.0 if emotion == "fear" else 0.0,
            1.0 if emotion == "surprise" else 0.0,
            1.0 if emotion == "anger" else 0.0,
            1.0 if emotion == "other" else 0.0,
            1.0 if emotion == "neutral" else 0.0,
        ]

        # Speaking rate
        try:
            speaking_rate = float(params.get("rate", 15.0))
        except ValueError:
            speaking_rate = 15.0

        # 🐛 Debug summary print
        print("\n[🔊 GENERATION SUMMARY]")
        print(f"Text:           {text}")
        print(f"Save path:      {save_path}")
        print(f"Emotion:        {emotion}")
        print(f"Speaker audio:  {speaker_audio or 'None'}")
        print(f"Speaking rate:  {speaking_rate}")
        print(f"Model choice:   {model_choice}")
        print(f"Language code:  {language}")
        print(f"Prefix audio:   {prefix_audio}")
        print(f"-------------------------\n")

        # Generation
        result, seed = generate_audio(
            model_choice,
            text,
            language,
            speaker_audio,
            prefix_audio,
            *e,
            vq_single=0.78,
            fmax=24000,
            pitch_std=45.0,
            speaking_rate=speaking_rate,
            dnsmos_ovrl=4.0,
            speaker_noised=False,
            cfg_scale=2.0,
            min_p=0.15,
            seed=420,
            randomize_seed=True,
            unconditional_keys=["emotion"],
            progress=lambda *_: None  # dummy
        )

        sr, audio_data = result

        try:
            sf.write(save_path, audio_data, sr)
            print(f"✅ Generated audio saved to {save_path} (seed={seed})")
            return True
        except Exception as e:
            print(f"❌ Failed to save audio to {save_path}: {e}")
            return False

    injected_server = InjectedServer(custom_hook)
    # ------------------------------------------------------
    # END OF INJECTION
    # ------------------------------------------------------

    return demo