# Video Summarizer - Gemini Integration

## ✅ Successfully Switched to Gemini Flash!

The application now uses **Google's Gemini 2.0 Flash** model for image captioning instead of OpenAI GPT-4 Vision.

## Changes Made

### 1. Dependencies
- ✅ Removed `openai` package
- ✅ Added `google-generativeai` package  
- ✅ Installed and verified

### 2. Configuration (`config.py`)
```python
# NEW: Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_GEMINI_VISION = True
GEMINI_MODEL = "gemini-2.0-flash-exp"
```

### 3. Caption Generator (`caption_generator.py`)
- Completely rewritten to use Gemini SDK
- Supports Gemini Flash for detailed image captions
- Maintains fallback to basic CV analysis

### 4. Pipeline Integration
- Updated to pass Gemini configuration
- All components properly Connected

## How to Set Your Gemini API Key

### Get Your API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your key

### Option 1: Environment Variable (Recommended)
```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
python3 app.py
```

### Option 2: .env File
Create or edit `.env` file:
```
GEMINI_API_KEY=your-gemini-api-key-here
```

### Option 3: Direct in config.py
Edit line 31 in `config.py`:
```python
GEMINI_API_KEY = "your-gemini-api-key-here"
```

## Testing

Once you set the API key and restart the app, the next video you process will use Gemini Flash for captions instead of the basic "dark frame showing detailed visual content" descriptions.

**Expected behavior:**
- Step 3/5 will show "Initialized Gemini gemini-2.0-flash-exp for captions"
- Captions will be detailed descriptions like "Screenshot of n8n workflow interface showing nodes and connections"

## Benefits of Gemini Flash

✅ **Faster** - Flash model is optimized for speed  
✅ **Better captions** - More accurate visual understanding  
✅ **More cost-effective** - Gemini is generally cheaper than GPT-4 Vision  
✅ **Latest model** - Using Gemini 2.0 Flash experimental

---

**Ready to test!** Just set your API key and upload a video.
