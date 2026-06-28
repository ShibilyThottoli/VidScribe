"""Test PPT generator with improved layouts"""

from generators import PPTGenerator, get_available_templates
from pathlib import Path
import config

print("="*60)
print("🧪 Testing Improved PPT Generator")
print("="*60)

# Better sample slides with realistic content
slides_data = [
    {
        'number': 1,
        'title': 'Introduction to Machine Learning',
        'content': '''Machine learning is a subset of artificial intelligence
Deep learning uses neural networks with multiple layers
Supervised learning requires labeled training data
Unsupervised learning finds patterns in unlabeled data
Reinforcement learning learns through trial and error'''
    },
    {
        'number': 2,
        'title': 'Neural Network Architecture',
        'content': '''Input layer receives raw data
Hidden layers process and transform information
Output layer produces final predictions
Activation functions introduce non-linearity
Backpropagation adjusts weights during training'''
    },
    {
        'number': 3,
        'title': 'Training Process',
        'content': '''Initialize network with random weights
Feed training data through the network
Calculate error using loss function
Update weights using gradient descent
Repeat until convergence'''
    },
    {
        'number': 4,
        'title': 'Key Takeaways',
        'content': '''Machine learning automates pattern recognition
Neural networks mimic biological brain structure
Training requires large amounts of data
Proper validation prevents overfitting
Continuous learning improves model performance'''
    }
]

# Test with professional template
print("\n📊 Creating professional presentation...")

try:
    generator = PPTGenerator(template_name='professional')
    output_path = config.OUTPUT_FOLDER / "improved_professional.pptx"
    
    generator.create_presentation(
        slides_data,
        str(output_path),
        title="Machine Learning Fundamentals",
        subtitle="A Comprehensive Overview of Neural Networks and Deep Learning"
    )
    
    print(f"✅ Created: {output_path}")
    print("\nOpen the file to see improved:")
    print("  - Better text spacing and margins")
    print("  - Proper bullet point formatting")
    print("  - Professional font sizing")
    print("  - Clean layout with good whitespace")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✅ Test complete! Check the outputs/ folder")
print("="*60)