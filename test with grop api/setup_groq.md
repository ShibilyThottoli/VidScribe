# Setup Groq API for Speech-to-Text

## Step 1: Get your Groq API Key

1. Go to [Groq Console](https://console.groq.com/keys)
2. Sign in or create an account
3. Create a new API key
4. Copy the API key

## Step 2: Add API Key to .env file

Add this line to your `.env` file:

```
GROQ_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual API key from Step 1.

## Step 3: Run the test

```bash
python3 test_groq_stt.py
```

## What the test does:

- ✅ Loads the audio.wav file
- ✅ Sends it to Groq's Whisper API for transcription
- ✅ Returns the transcribed text with timestamps
- ✅ Shows detailed segments with timing information

## Supported Audio Formats:

- WAV
- MP3
- M4A
- FLAC
- OGG
- And more...

## Notes:

- The test uses `whisper-large-v3-turbo` model (fast and accurate)
- Groq's Whisper API is very fast (often 10x faster than OpenAI)
- Free tier includes generous limits for testing
