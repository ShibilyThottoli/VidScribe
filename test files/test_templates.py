"""Test PPT templates"""

from generators.ppt_templates import TEMPLATES

print("="*60)
print("🎨 Testing PPT Templates")
print("="*60)

for template_id, template in TEMPLATES.items():
    print(f"\n✅ {template['name']}")
    print(f"   ID: {template_id}")
    print(f"   Description: {template['description']}")
    print(f"   Colors defined: {len(template['colors'])}")
    print(f"   Fonts defined: {len(template['fonts'])}")
    print(f"   Layouts: {list(template['layout'].keys())}")

print("\n" + "="*60)
print(f"✅ All {len(TEMPLATES)} templates loaded successfully!")
print("="*60)