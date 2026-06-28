"""Generate simple template preview images"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Template colors (from templates)
TEMPLATES = {
    'professional': {
        'bg': '#FFFFFF',
        'primary': '#003366',
        'accent': '#0070C0'
    },
    'educational': {
        'bg': '#FDF5E6',
        'primary': '#E67E22',
        'accent': '#F1C40F'
    },
    'minimalist': {
        'bg': '#FFFFFF',
        'primary': '#000000',
        'accent': '#646464'
    },
    'creative': {
        'bg': '#ECF0F1',
        'primary': '#E74C3C',
        'accent': '#9B59B6'
    },
    'modern_tech': {
        'bg': '#14141E',
        'primary': '#00FFFF',
        'accent': '#39FF14'
    }
}

def create_preview(name, colors, output_path):
    """Create simple template preview"""
    width, height = 400, 300
    
    # Create image
    img = Image.new('RGB', (width, height), colors['bg'])
    draw = ImageDraw.Draw(img)
    
    # Draw header bar
    draw.rectangle([0, 0, width, 60], fill=colors['primary'])
    
    # Draw accent line
    draw.rectangle([0, 60, width, 65], fill=colors['accent'])
    
    # Draw content boxes
    draw.rectangle([20, 90, width-20, 150], fill=colors['primary'])
    draw.rectangle([20, 170, width//2-10, 270], fill=colors['accent'])
    draw.rectangle([width//2+10, 170, width-20, 270], fill=colors['primary'])
    
    # Save
    img.save(output_path)
    print(f"✅ Created: {output_path}")

# Create directory
output_dir = Path('static/images/templates')
output_dir.mkdir(parents=True, exist_ok=True)

# Generate previews
for template_id, colors in TEMPLATES.items():
    output_path = output_dir / f"{template_id}.png"
    create_preview(template_id, colors, output_path)

print("\n✅ All template previews created!")

"""Generate simple logo"""

from PIL import Image, ImageDraw, ImageFont

def create_logo():
    size = 200
    img = Image.new('RGB', (size, size), '#2563EB')
    draw = ImageDraw.Draw(img)
    
    # Draw simple "VS" text
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    text = "VS"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    # Save
    output_path = Path('static/images/logo.png')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"✅ Logo created: {output_path}")

create_logo()