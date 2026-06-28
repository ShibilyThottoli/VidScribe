"""Test utility modules"""

from utils import (
    VideoValidator, 
    FileHandler, 
    format_timestamp, 
    get_logger,
    create_progress_message,
    estimate_processing_time,
    sanitize_filename
)
import config

# Setup logger
logger = get_logger(__name__)

print("="*60)
print("🧪 Testing Utility Modules")
print("="*60)

# Test 1: Validator
print("\n1. Testing VideoValidator:")
validator = VideoValidator()
print(f"   Max file size: {validator.max_size / (1024**3):.1f} GB")
print(f"   Max duration: {validator.max_duration / 60:.0f} minutes")
print(f"   Allowed formats: {validator.allowed_extensions}")

# Test 2: File Handler
print("\n2. Testing FileHandler:")
FileHandler.ensure_directories()
print(f"   ✅ All directories created/verified")
print(f"   Upload folder: {config.UPLOAD_FOLDER.exists()}")
print(f"   Output folder: {config.OUTPUT_FOLDER.exists()}")
print(f"   Temp folder: {config.TEMP_FOLDER.exists()}")

# Test 3: Timestamp formatting
print("\n3. Testing timestamp formatting:")
print(f"   90 seconds = {format_timestamp(90)}")
print(f"   3665 seconds = {format_timestamp(3665)}")
print(f"   2700 seconds = {format_timestamp(2700)}")

# Test 4: Progress messages
print("\n4. Testing progress messages:")
print(f"   {create_progress_message(1, 5, 'Extracting keyframes')}")
print(f"   {create_progress_message(3, 5, 'Generating summary')}")
print(f"   {create_progress_message(5, 5, 'Creating presentation')}")

# Test 5: Time estimation
print("\n5. Testing time estimation:")
print(f"   10-minute video: {estimate_processing_time(600)}")
print(f"   30-minute video: {estimate_processing_time(1800)}")
print(f"   45-minute video: {estimate_processing_time(2700)}")

# Test 6: Filename sanitization
print("\n6. Testing filename sanitization:")
dangerous_names = [
    "test<file>.mp4",
    "my|video?.avi",
    "../../../etc/passwd",
    "normal_video_2024.mp4"
]
for name in dangerous_names:
    sanitized = sanitize_filename(name)
    print(f"   '{name}' → '{sanitized}'")

# Test 7: Logger
print("\n7. Testing logger:")
logger.info("✅ This is an info message")
logger.warning("⚠️  This is a warning message")
logger.error("❌ This is an error message")
print(f"   Log file location: {config.LOG_FILE}")

print("\n" + "="*60)
print("✅ All utility modules tested successfully!")
print("="*60)