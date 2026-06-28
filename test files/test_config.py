"""Test configuration"""
import config

print("✅ Configuration Test")
print(f"Max File Size: {config.MAX_FILE_SIZE / (1024**3):.1f} GB")
print(f"Max Duration: {config.MAX_VIDEO_DURATION // 60} minutes")
print(f"Allowed Formats: {config.ALLOWED_EXTENSIONS}")
print(f"Gemini Model: {config.GEMINI_MODEL}")
print(f"API Key Configured: {'✅ Yes' if config.validate_api_key() else '❌ No - Set GEMINI_API_KEY in .env'}")
print(f"Templates Available: {list(config.PPT_TEMPLATES.keys())}")
print(f"\nDirectories:")
print(f"  - Upload: {config.UPLOAD_FOLDER}")
print(f"  - Output: {config.OUTPUT_FOLDER}")
print(f"  - Temp: {config.TEMP_FOLDER}")