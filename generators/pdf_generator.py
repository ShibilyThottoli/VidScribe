"""PDF report generator"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from pathlib import Path
import logging
from typing import List, Dict
import config

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF reports from video summaries"""
    
    def __init__(self):
        """Initialize PDF generator"""
        self.page_size = A4 if config.PDF_PAGE_SIZE == 'A4' else letter
        logger.info("PDF Generator initialized")
    
    def generate_pdf(self, slides_data: List[Dict], output_path: str,
                     title: str = None, summary: str = None) -> str:
        """
        Generate PDF report
        
        Args:
            slides_data: List of slide data
            output_path: Path to save PDF
            title: Document title
            summary: Overall summary text
            
        Returns:
            Path to created PDF
        """
        logger.info(f"Generating PDF with {len(slides_data)} sections")
        
        # Create PDF document
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(str(output_path), pagesize=self.page_size)
        
        # Container for content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2C3E50',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='#34495E',
            spaceAfter=12,
            spaceBefore=12
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=config.PDF_FONT_SIZE,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
        
        # Add title
        title_text = title or 'Video Summary Report'
        story.append(Paragraph(title_text, title_style))
        story.append(Spacer(1, 0.3 * inch))
        
        # Add summary
        if summary:
            story.append(Paragraph('<b>Summary:</b>', heading_style))
            story.append(Paragraph(summary, body_style))
            story.append(Spacer(1, 0.3 * inch))
        
        # Add content sections
        for slide in slides_data:
            # Section title
            section_title = slide.get('title', 'Section')
            story.append(Paragraph(section_title, heading_style))
            
            # Add image if available
            if config.PDF_INCLUDE_IMAGES and 'keyframe_path' in slide:
                image_path = slide['keyframe_path']
                if image_path and Path(image_path).exists():  # ✅ FIXED - check not None first
                    try:
                        img = Image(image_path, width=4*inch, height=3*inch)
                        story.append(img)
                        story.append(Spacer(1, 0.2 * inch))    
                    except Exception as e:
                        logger.error(f"Error adding image to PDF: {e}")
                else:
                    logger.debug(f"Slide '{slide.get('title', 'Unknown')}': No keyframe image")
            
            # Section content
            content = slide.get('content', '')
            if content:
                story.append(Paragraph(content.replace('\n', '<br/>'), body_style))
            
            story.append(Spacer(1, 0.2 * inch))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF saved to {output_path}")
        
        return output_path