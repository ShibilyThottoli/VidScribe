"""Test core modules"""

print("Testing Core Modules...\n")

# Test 1: Keyframe Extractor
try:
    from core.keyframe_extractor import KeyframeExtractor
    extractor = KeyframeExtractor()
    print("✅ KeyframeExtractor imported successfully")
    print(f"   Motion threshold: {extractor.motion_threshold}")
    print(f"   Max keyframes: {extractor.max_keyframes}")
except Exception as e:
    print(f"❌ KeyframeExtractor error: {e}")

# Test 2: Audio Processor
try:
    from core.audio_processor import AudioProcessor
    processor = AudioProcessor()
    print("\n✅ AudioProcessor imported successfully")
    print(f"   Whisper model: {processor.model_name}")
except Exception as e:
    print(f"❌ AudioProcessor error: {e}")

print("\n" + "="*60)
print("Core modules ready!")