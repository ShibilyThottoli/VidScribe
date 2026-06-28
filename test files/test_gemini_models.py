"""List available Gemini models"""

import google.generativeai as genai
import config

print("Checking available Gemini models...\n")

try:
    genai.configure(api_key=config.GEMINI_API_KEY)
    
    print("Available models:")
    print("="*60)
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"\n✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:100] if model.description else 'N/A'}...")
            print(f"   Supported: {model.supported_generation_methods}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure your API key is correct in .env file")