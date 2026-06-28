#!/usr/bin/env python3
"""
Utility script to save processed video results for testing
This allows reusing LLM-generated content without API calls
"""

import json
from pathlib import Path
from app import processing_results

def save_results(output_name: str, save_path: str = None):
    """
    Save processing results to a JSON file for reuse
    
    Args:
        output_name: The job ID (output name) from processing
        save_path: Optional path to save file. Defaults to saved_results/{output_name}.json
    """
    
    if output_name not in processing_results:
        print(f"❌ Error: '{output_name}' not found in processing results")
        print(f"Available results: {list(processing_results.keys())}")
        return
    
    # Get the results
    results = processing_results[output_name]
    
    # Default save path
    if save_path is None:
        save_dir = Path(__file__).parent / "saved_results"
        save_dir.mkdir(exist_ok=True)
        save_path = save_dir / f"{output_name}.json"
    else:
        save_path = Path(save_path)
    
    # Save to JSON
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved results to: {save_path}")
    print(f"   - Title: {results.get('title')}")
    print(f"   - Slides: {len(results.get('slides', []))}")
    print(f"   - Template: {results.get('template')}")
    print(f"   - Size: {save_path.stat().st_size} bytes")

def list_saved_results():
    """List all saved result files"""
    save_dir = Path(__file__).parent / "saved_results"
    if not save_dir.exists():
        print("No saved results yet")
        return
    
    files = list(save_dir.glob("*.json"))
    if not files:
        print("No saved results yet")
        return
    
    print(f"\n📁 Saved Results ({len(files)}):")
    for f in files:
        with open(f, 'r') as file:
            data = json.load(file)
            print(f"  • {f.name}")
            print(f"    Title: {data.get('title', 'N/A')}")
            print(f"    Slides: {len(data.get('slides', []))}")
            print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python save_results.py <output_name>  # Save specific result")
        print("  python save_results.py list            # List saved results")
        print()
        print("Example:")
        print("  python save_results.py What_Is_n8n__The_Beginner-Friendly_Automation_Tool_Explained_1_20251215_194234")
        sys.exit(1)
    
    if sys.argv[1] == "list":
        list_saved_results()
    else:
        output_name = sys.argv[1]
        save_results(output_name)
