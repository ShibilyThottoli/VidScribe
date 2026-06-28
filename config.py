"""Configuration settings for Video Summarizer"""

from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables FIRST
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / '.env')

# ============================================================================
# DIRECTORIES
# ============================================================================
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
OUTPUT_FOLDER = BASE_DIR / "outputs"
TEMP_FOLDER = BASE_DIR / "temp"

# Create directories if they don't exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# ============================================================================
# VIDEO UPLOAD SETTINGS
# ============================================================================
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'mpeg', 'mpg'}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB in bytes
MAX_VIDEO_DURATION = 45 * 60  # 45 minutes in seconds

# ============================================================================
# KEYFRAME EXTRACTION SETTINGS (OpenCV)
# ============================================================================
MOTION_THRESHOLD = 30  # Motion detection sensitivity (lower = more sensitive)
HISTOGRAM_THRESHOLD = 0.7  # Scene change detection (lower = more sensitive)
MIN_FRAME_INTERVAL = 30  # Minimum frames between keyframes (1 sec at 30fps)
MAX_KEYFRAMES = 10  # Maximum number of keyframes to extract

# Tesseract OCR Settings (for text extraction from keyframes)
TESSERACT_CMD = "/opt/homebrew/bin/tesseract"  # Path to Tesseract executable
# Common paths:
#   macOS (Homebrew - Intel): /usr/local/bin/tesseract
#   macOS (Homebrew - Apple Silicon): /opt/homebrew/bin/tesseract
#   Windows: C:\Program Files\Tesseract-OCR\tesseract.exe
#   Linux: /usr/bin/tesseract

# ============================================================================
# AUDIO PROCESSING SETTINGS (Whisper)
# ============================================================================
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large
# "base" is good balance of speed and accuracy for 45-min videos
WHISPER_LANGUAGE = "en"  # None = auto-detect language

# Groq Whisper API (Cloud-based transcription - much faster!)
USE_GROQ_WHISPER = True  # True = use Groq API (fast), False = local Whisper (slow)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # Set via .env file

# ============================================================================
# GEMINI API SETTINGS
# ============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # Set via .env file

# Load all API keys for rotation (primary + numbered keys)
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY", ""),
    os.getenv("GEMINI_API_KEY_1", ""),
    os.getenv("GEMINI_API_KEY_2", ""),
    os.getenv("GEMINI_API_KEY_3", ""),
    os.getenv("GEMINI_API_KEY_4", ""),
    os.getenv("GEMINI_API_KEY_5", ""),
]
# Filter out empty keys
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

GEMINI_MODEL = "gemini-2.5-flash"  # Free tier model with video support  gemma-3-27b,gemini-2.5-flash-live
GEMINI_TEMPERATURE = 0.7  # Creativity level (0.0 = focused, 1.0 = creative)
GEMINI_MAX_TOKENS = 2048  # Maximum tokens for summary generation

# Video Analysis Settings
USE_GEMINI_VIDEO = False  # True = Gemini analyzes full video (1 API call)
                          # False = Traditional pipeline (keyframes + Whisper)
                          # Recommended: False for better control and cost

# ============================================================================
# OUTPUT FORMAT SETTINGS
# ============================================================================
# Supported output formats
OUTPUT_FORMATS = ['ppt', 'pdf', 'summary']  # summary = text only (displayed in UI)

# Summary Settings
SUMMARY_MAX_LENGTH = 500  # Maximum words in summary text
SUMMARY_STYLE = "concise"  # Options: concise, detailed, bullet_points

# PowerPoint Settings
PPT_SLIDES_COUNT = 15  # Number of content slides (excluding title)
PPT_INCLUDE_TIMESTAMPS = True  # Show timestamps on slides
PPT_INCLUDE_KEYFRAMES = True  # Include keyframe images in slides
PPT_TITLE = "Video Summary"  # Default presentation title
PPT_SUBTITLE = "AI Video Summary"
# PDF Settings
PDF_INCLUDE_IMAGES = True  # Include keyframe images in PDF
PDF_PAGE_SIZE = "A4"  # A4 or Letter
PDF_FONT_SIZE = 12  # Base font size

# ============================================================================
# PPT TEMPLATE SETTINGS
# ============================================================================
PPT_TEMPLATES = {
    'professional': {
        'name': 'Professional',
        'description': 'Clean corporate style with navy blue theme',
        'preview': 'professional.png'
    },
    'educational': {
        'name': 'Educational',
        'description': 'Friendly learning style with warm colors',
        'preview': 'educational.png'
    },
    'minimalist': {
        'name': 'Minimalist',
        'description': 'Simple black & white with lots of whitespace',
        'preview': 'minimalist.png'
    },
    'creative': {
        'name': 'Creative',
        'description': 'Vibrant gradients and bold typography',
        'preview': 'creative.png'
    },
    'modern_tech': {
        'name': 'Modern Tech',
        'description': 'Dark mode with neon accents',
        'preview': 'modern_tech.png'
    }
}

DEFAULT_TEMPLATE = 'educational'  # Default template if none selected


# ============================================================================
# PROCESSING SETTINGS
# ============================================================================
# Content Selection (for focused presentations)
SELECT_KEY_VISUALS = False  # Disabled to save API calls - only include most relevant keyframes
VISUAL_SELECTION_METHOD = "gemini"  # Options: gemini, diversity, time_based

# Cleanup Settings
AUTO_DELETE_UPLOADS = True  # Delete uploaded videos after processing
AUTO_DELETE_TEMP = False  # DISABLED - Keep temp files so keyframes can be auto-saved
KEEP_OUTPUTS_HOURS = 24  # Keep generated files for 24 hours

# ============================================================================
# LOGGING SETTINGS
# ============================================================================
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = BASE_DIR / "logs" / "app.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create logs directory
LOG_FILE.parent.mkdir(exist_ok=True)

# ============================================================================
# FLASK SETTINGS
# ============================================================================
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5001
FLASK_DEBUG = True  # Set to False in production

# ============================================================================
# FEATURE FLAGS
# ============================================================================
ENABLE_PDF_GENERATION = True  # Enable/disable PDF output
ENABLE_ASYNC_PROCESSING = False  # Use Celery for async (for production)
ENABLE_PROGRESS_TRACKING = True  # Show real-time progress

# ============================================================================
# VALIDATION MESSAGES
# ============================================================================
ERROR_MESSAGES = {
    'no_file': 'No video file provided',
    'invalid_format': f'Invalid file format. Allowed: {", ".join(ALLOWED_EXTENSIONS)}',
    'file_too_large': f'File size exceeds {MAX_FILE_SIZE / (1024**3):.1f}GB limit',
    'video_too_long': f'Video duration exceeds {MAX_VIDEO_DURATION // 60} minutes limit',
    'processing_error': 'An error occurred during processing',
    'api_key_missing': 'Gemini API key not configured'
}

# ============================================================================
# API RATE LIMITS (Gemini Free Tier)
# ============================================================================
GEMINI_RATE_LIMIT_RPM = 15  # Requests per minute
GEMINI_RATE_LIMIT_TOKENS = 1_000_000  # Tokens per day
ESTIMATED_TOKENS_PER_VIDEO = 150_000  # For 45-min video
MAX_VIDEOS_PER_DAY = GEMINI_RATE_LIMIT_TOKENS // ESTIMATED_TOKENS_PER_VIDEO  # ~6 videos

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_upload_path(filename: str) -> Path:
    """Get full path for uploaded file"""
    return UPLOAD_FOLDER / filename

def get_output_path(filename: str, format: str = 'pptx') -> Path:
    """Get full path for output file"""
    return OUTPUT_FOLDER / f"{filename}.{format}"

def get_temp_path(filename: str) -> Path:
    """Get full path for temporary file"""
    return TEMP_FOLDER / filename

def validate_api_key() -> bool:
    """Check if Gemini API key is configured"""
    return bool(GEMINI_API_KEY and GEMINI_API_KEY != "")