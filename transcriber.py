import whisper
import os
import ssl
import time
import static_ffmpeg
from typing import Optional

# Disable SSL verification for the model download
ssl._create_default_https_context = ssl._create_unverified_context

def load_whisper_model(model_name: str = "base"):
    """
    Load the Whisper model with proper initialization.
    
    Args:
        model_name (str): Name of the Whisper model to load (default: "base")
        
    Returns:
        whisper.Whisper: Loaded Whisper model
    """
    try:
        # Initialize static_ffmpeg for audio processing
        static_ffmpeg.add_paths()
        
        # Create models directory if it doesn't exist
        os.makedirs("./models", exist_ok=True)
        
        print(f"Loading Whisper {model_name} model...")
        
        # Load the model with retry logic
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                model = whisper.load_model(model_name, download_root="./models")
                print("Whisper model loaded successfully")
                return model
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    print(f"Failed to load Whisper model after {max_retries} attempts: {str(e)}")
                    raise
                print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
    except Exception as e:
        print(f"Error loading Whisper model: {str(e)}")
        raise

def transcribe_audio(audio_path: str, model_name: str = "base") -> Optional[str]:
    """
    Transcribe an audio file using Whisper.
    
    Args:
        audio_path (str): Path to the audio file
        model_name (str): Name of the Whisper model to use (default: "base")
        
    Returns:
        str: Transcribed text, or None if there was an error
    """
    try:
        # Verify the audio file exists
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return None
            
        # Load the Whisper model
        model = load_whisper_model(model_name)
        
        # Transcribe the audio
        print(f"Transcribing audio: {audio_path}")
        result = model.transcribe(audio_path, fp16=False)  # Disable FP16 for better compatibility
        
        # Clean up the audio file after successful transcription
        try:
            os.remove(audio_path)
            print(f"Removed audio file: {audio_path}")
        except Exception as e:
            print(f"Warning: Could not remove audio file: {str(e)}")
        
        return result["text"]
        
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return None
