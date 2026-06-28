"""Test Groq Speech-to-Text API"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

def transcribe_audio(audio_file_path: str, api_key: str):
    """
    Transcribe audio file using Groq's Whisper API
    
    Args:
        audio_file_path: Path to the audio file (supports wav, mp3, m4a, etc.)
        api_key: Groq API key
    """
    # Import here to avoid error if package not installed
    try:
        from groq import Groq
    except ImportError:
        print("❌ Error: groq package not installed")
        print("Install it with: pip install groq")
        return None
    
    audio_path = Path(audio_file_path)
    
    # Check if file exists
    if not audio_path.exists():
        print(f"❌ Error: Audio file not found at {audio_path}")
        return None
    
    print(f"📁 Audio file: {audio_path}")
    print(f"📊 File size: {audio_path.stat().st_size / 1024:.2f} KB")
    print("\n🎤 Transcribing audio with Groq Whisper...")
    
    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)
        
        # Open and transcribe the audio file
        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio_path.name, file.read()),
                model="whisper-large-v3",  # Groq's Whisper model
                response_format="verbose_json",  # Get detailed response with timestamps
                language="en",  # Optional: specify language (en, es, fr, etc.) or remove for auto-detect
                temperature=0.0  # Lower temperature for more consistent results
            )
        
        print("\n✅ Transcription successful!\n")
        print("=" * 60)
        print("TRANSCRIPTION:")
        print("=" * 60)
        print(transcription.text)
        print("=" * 60)
        
        # Print additional details if available
        if hasattr(transcription, 'duration'):
            print(f"\n⏱️  Duration: {transcription.duration:.2f} seconds")
        if hasattr(transcription, 'language'):
            print(f"🌐 Detected Language: {transcription.language}")
        
        # Print segments with timestamps if available
        if hasattr(transcription, 'segments') and transcription.segments:
            print("\n📝 Segments with timestamps:")
            print("-" * 60)
            for i, segment in enumerate(transcription.segments, 1):
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '')
                print(f"{i}. [{start:.2f}s - {end:.2f}s] {text}")
        
        return transcription
        
    except Exception as e:
        print(f"\n❌ Error during transcription: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 GROQ SPEECH-TO-TEXT API TEST")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("\n❌ Error: GROQ_API_KEY not found in environment variables")
        print("\n📝 To fix this, add your Groq API key to the .env file:")
        print("   GROQ_API_KEY=your_api_key_here")
        print("\n🔑 Get your API key from: https://console.groq.com/keys")
        print("\n" + "=" * 60)
        exit(1)
    
    print(f"\n✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test with audio.wav
    audio_file = "audio.wav"
    
    # Try different possible locations
    possible_paths = [
        Path(audio_file),  # Current directory
        Path(__file__).parent / audio_file,  # Script directory
        Path(__file__).parent / "temp" / audio_file,  # temp folder
        Path(__file__).parent / "test files" / audio_file,  # test files folder
    ]
    
    audio_path = None
    for path in possible_paths:
        if path.exists():
            audio_path = path
            break
    
    if audio_path:
        print(f"\n" + "=" * 60)
        transcribe_audio(str(audio_path), api_key)
        print("\n" + "=" * 60)
        print("✅ Test completed!")
        print("=" * 60)
    else:
        print(f"\n❌ Could not find {audio_file} in any of these locations:")
        for path in possible_paths:
            print(f"   - {path}")
        print("\n💡 A test audio file has been created at: /Users/falahi/VidScrib/audio.wav")
        print("   Run this script again to test with it.")
        print("\n" + "=" * 60)
