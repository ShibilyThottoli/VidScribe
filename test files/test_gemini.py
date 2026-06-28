"""Test Gemini processor"""

from core.gemini_processor import GeminiProcessor, test_gemini_connection
import config

print("="*60)
print("🧪 Testing Gemini Integration")
print("="*60)

# Test 1: Connection
print("\n1. Testing API connection...")
if test_gemini_connection():
    print("   ✅ Gemini API connected successfully!")
else:
    print("   ❌ Failed to connect to Gemini API")
    print("   Check your API key in .env file")
    exit(1)

# Test 2: Initialize processor
print("\n2. Initializing Gemini Processor...")
try:
    processor = GeminiProcessor()
    print(f"   ✅ Processor initialized")
    print(f"   Model: {processor.model_name}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 3: Simple text generation
print("\n3. Testing text generation...")
try:
    response = processor.model.generate_content(
        "Explain what video summarization is in one sentence."
    )
    print(f"   ✅ Response: {response.text[:100]}...")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Content sections
print("\n4. Testing content section creation...")
try:
    sample_transcript = """
    Welcome to this tutorial on machine learning. 
    Today we'll cover the basics of neural networks.
    First, let's understand what a neuron is.
    Then we'll look at how neurons connect in layers.
    Finally, we'll see how networks learn from data.
    """
    
    sections = processor.create_content_sections(sample_transcript, num_sections=3)
    print(f"   ✅ Created sections:")
    print(f"      Title: {sections['title']}")
    print(f"      Sections: {len(sections['sections'])}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*60)
print("✅ Gemini integration test complete!")
print("="*60)