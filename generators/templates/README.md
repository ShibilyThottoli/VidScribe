# PowerPoint Templates

This folder contains PowerPoint template files (`.pptx`) used by VidScrib.

## Required Layout Structure

Your template file must have the following slide layouts:

### Layout 0: Title Slide
- **Placeholder 0**: Title text
- **Placeholder 1**: Subtitle text

### Layout 1: Content Slide (Text Only)
- **Placeholder 0**: Title text
- **Placeholder 1**: Content/bullets text

### Layout 8: Content Slide (With Image)
- **Placeholder 0**: Title text
- **Placeholder 1**: Picture placeholder
- **Placeholder 2**: Content/bullets text

## How to Add a Template

1. Create your PowerPoint template in PowerPoint
2. Set up the required layouts (0, 1, and 8) with placeholders
3. Save as `.pptx` file in this folder
4. Name it descriptively (e.g., `professional.pptx`, `modern.pptx`)
5. VidScrib will automatically detect and use it

## Example Templates

- `professional.pptx` - Clean corporate style
- `modern.pptx` - Modern design with gradients
- `minimalist.pptx` - Simple black and white

## Testing Your Template

Upload a video and select your template. VidScrib will:
- Use Layout 0 for the title slide
- Use Layout 8 for slides with keyframe images
- Use Layout 1 for slides without images
- Fill placeholders automatically with content
