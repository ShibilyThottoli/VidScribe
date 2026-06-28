"""Gemini AI processor with dual-pool key rotation (vision + text)"""

from google import genai
from google.genai import types
from PIL import Image
import logging
from typing import List, Dict, Optional
import time
import re
import config

logger = logging.getLogger(__name__)


class GeminiProcessor:
    """Handle all Gemini AI interactions with dual-pool key rotation"""
    
    def __init__(self, api_keys: List[str] = None, model_name: str = None):
        """
        Initialize Gemini processor with dual-pool architecture
        
        Args:
            api_keys: List of Gemini API keys for rotation
            model_name: Model name (uses config if None)
        """
        self.api_keys = api_keys or config.GEMINI_API_KEYS
        self.model_name = model_name or config.GEMINI_MODEL
        
        if not self.api_keys or len(self.api_keys) == 0:
            raise ValueError("No Gemini API keys configured. Set GEMINI_API_KEYS in .env file")
        
        # Dual-pool indices (independent rotation)
        self.vision_key_index = 0
        self.text_key_index = 0
        
        # Initialize both pools
        self._switch_vision_key()
        self._switch_text_key()
        
        logger.info("=" * 70)
        logger.info("🎯 DUAL-POOL GEMINI PROCESSOR INITIALIZED")
        logger.info("=" * 70)
        logger.info(f"📸 Vision Pool: {len(self.api_keys)} API keys with rotation")
        logger.info(f"📝 Text Pool: {len(self.api_keys)} API keys with rotation")
        logger.info(f"✅ Independent key rotation for rate limit protection")
        logger.info("=" * 70)
    
    def _switch_vision_key(self):
        """Switch to specific vision pool API key"""
        api_key = self.api_keys[self.vision_key_index]
        self.vision_client = genai.Client(api_key=api_key)
        logger.info(f"🔑 Vision Pool: Using key #{self.vision_key_index + 1}/{len(self.api_keys)}")
    
    def _switch_text_key(self):
        """Switch to specific text pool API key"""
        api_key = self.api_keys[self.text_key_index]
        self.text_client = genai.Client(api_key=api_key)
        logger.info(f"🔑 Text Pool: Using key #{self.text_key_index + 1}/{len(self.api_keys)}")
    
    def _rotate_vision_key(self):
        """Rotate to next vision pool API key"""
        self.vision_key_index = (self.vision_key_index + 1) % len(self.api_keys)
        self._switch_vision_key()
        logger.info(f"🔄 Vision Pool: Rotated to next key")
    
    def _rotate_text_key(self):
        """Rotate to next text pool API key"""
        self.text_key_index = (self.text_key_index + 1) % len(self.api_keys)
        self._switch_text_key()
        logger.info(f"🔄 Text Pool: Rotated to next key")
    
    # ========================================================================
    # VISION POOL METHODS
    # ========================================================================
    
    def generate_image_caption(self, image_path: str, custom_prompt: str = None) -> str:
        """
        Generate caption for a single image with retry logic (VISION POOL)
        
        Args:
            image_path: Path to image file
            custom_prompt: Custom prompt (uses default if None)
            
        Returns:
            Generated caption text
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Default prompt
            prompt = custom_prompt or """
            Describe what's happening in this image in 2-3 sentences.
            Focus on:
            - Main subject or topic
            - Key visual elements
            - Important text or diagrams (if any)
            - Context or setting
            
            Be concise and informative.
            """
            
            # Generate caption using vision pool
            response = self.vision_client.models.generate_content(
                model=self.model_name,
                contents=[prompt, img]
            )
            caption = response.text.strip()
            
            return caption
            
        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            raise
    
    def generate_captions_batch(self, image_paths: List[str], 
                                delay: float = 6.5) -> List[Dict[str, str]]:
        """
        Generate captions for multiple images with automatic rate limit handling (VISION POOL)
        
        Args:
            image_paths: List of image file paths
            delay: Delay between API calls (6.5s = ~9 requests/min for free tier)
            
        Returns:
            List of dictionaries with image_path and caption
        """
        captions = []
        total_images = len(image_paths)
        estimated_time = total_images * delay
        
        logger.info(f"Generating captions for {total_images} images...")
        logger.info(f"⏱️  Estimated time: ~{estimated_time / 60:.1f} minutes (with rate limit protection)")
        logger.info(f"🔑 Using {len(self.api_keys)} vision pool keys with rotation")
        logger.info(f"💡 Using {delay}s delay between requests to stay under 10/min limit")
        
        consecutive_failures = 0
        max_consecutive_failures = len(self.api_keys)
        
        for i, image_path in enumerate(image_paths, 1):
            retry_count = 0
            max_retries = 2
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    # Generate caption
                    caption = self.generate_image_caption(image_path)
                    
                    captions.append({
                        'image_path': image_path,
                        'caption': caption
                    })
                    
                    logger.info(f"  [{i}/{total_images}] ✅ Captioned (Vision Key #{self.vision_key_index + 1})")
                    success = True
                    consecutive_failures = 0  # Reset failure counter
                    
                    # Rate limiting - wait before next request (except for last image)
                    if i < total_images:
                        time.sleep(delay)
                    
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check if this is a rate limit error
                    is_rate_limit = ('429' in error_msg or 
                                   'quota' in error_msg.lower() or 
                                   'rate' in error_msg.lower())
                    
                    if is_rate_limit:
                        retry_count += 1
                        consecutive_failures += 1
                        
                        if retry_count < max_retries and consecutive_failures < max_consecutive_failures:
                            # Try rotating to next key
                            logger.warning(f"  ⏳ [{i}/{total_images}] Rate limit on vision key #{self.vision_key_index + 1}")
                            self._rotate_vision_key()
                            logger.warning(f"     Retrying with vision key #{self.vision_key_index + 1}...")
                        else:
                            # All keys exhausted
                            logger.error(f"  ❌ [{i}/{total_images}] All vision keys rate limited")
                            captions.append({
                                'image_path': image_path,
                                'caption': '[Caption unavailable - all keys rate limited]'
                            })
                            success = True  # Move to next image
                    else:
                        # Non-rate-limit error - log and continue
                        logger.error(f"  ❌ [{i}/{total_images}] Error: {error_msg[:100]}")
                        captions.append({
                            'image_path': image_path,
                            'caption': f'[Caption generation failed]'
                        })
                        success = True  # Move to next image
        
        logger.info(f"✅ Caption generation complete: {len(captions)}/{total_images} successful")
        return captions
    
    def select_key_visuals(self, captions: List[Dict], 
                          transcript: str, num_visuals: int = 5) -> List[int]:
        """
        Use AI to select most important visuals (VISION POOL)
        
        Args:
            captions: List of image captions
            transcript: Full transcript
            num_visuals: Number of visuals to select
            
        Returns:
            List of indices of selected images
        """
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                captions_text = "\n".join([
                    f"{i}. {cap['caption']}" 
                    for i, cap in enumerate(captions)
                    if not cap['caption'].startswith('[')
                ])
                
                prompt = f"""
                Given these visual descriptions from a video and the transcript, 
                select the {num_visuals} MOST IMPORTANT visuals that best represent the key concepts.
                
                VISUALS:
                {captions_text}
                
                TRANSCRIPT SNIPPET:
                {transcript[:1000]}...
                
                Return ONLY the numbers (0-{len(captions)-1}) of the {num_visuals} most important visuals, 
                comma-separated, like: 0,3,7,12,15
                """
                
                response = self.vision_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                indices_text = response.text.strip()
                
                # Parse indices
                indices = [int(x.strip()) for x in indices_text.split(',') if x.strip().isdigit()]
                indices = [i for i in indices if 0 <= i < len(captions)][:num_visuals]
                
                logger.info(f"Selected {len(indices)} key visuals: {indices}")
                return indices
                
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = '429' in error_msg or 'quota' in error_msg.lower()
                
                if is_rate_limit and retry_count < max_retries - 1:
                    retry_count += 1
                    logger.warning(f"⏳ Rate limit on visual selection (vision key #{self.vision_key_index + 1})")
                    self._rotate_vision_key()
                    logger.warning(f"   Retrying with vision key #{self.vision_key_index + 1}...")
                else:
                    logger.error(f"Error selecting visuals: {e}")
                    # Fallback: evenly spaced selection
                    step = len(captions) // num_visuals if num_visuals > 0 else 1
                    return list(range(0, len(captions), step))[:num_visuals]
        
        # Fallback
        step = len(captions) // num_visuals if num_visuals > 0 else 1
        return list(range(0, len(captions), step))[:num_visuals]
    
    # ========================================================================
    # TEXT POOL METHODS
    # ========================================================================
    
    def create_video_summary(self, transcript: str, captions: List[Dict], 
                            custom_prompt: str = None) -> Dict[str, str]:
        """
        Create comprehensive video summary with retry logic (TEXT POOL)
        
        Args:
            transcript: Audio transcript text
            captions: List of image captions
            custom_prompt: Custom prompt (uses default if None)
            
        Returns:
            Dictionary with summary components
        """
        max_retries = 3
        retry_count = 0
        consecutive_failures = 0
        max_consecutive_failures = len(self.api_keys)
        
        while retry_count < max_retries:
            try:
                # Combine visual and audio information
                visual_content = "\n\n".join([
                    f"Visual {i+1}: {cap['caption']}" 
                    for i, cap in enumerate(captions)
                    if not cap['caption'].startswith('[')  # Skip failed captions
                ])
                
                # Default prompt
                prompt = custom_prompt or f"""
                You are generating a structured analysis of a video that will be converted into a presentation. 
                Use a clear, educational tone similar to Google NotebookLM auto-generated reports.

                Use this format:

                TITLE:
                Write a concise 5–10 word title.

                OVERVIEW:
                Write a 2–3 sentence explanation of the video's purpose and main idea.

                MAIN SECTIONS:
                Create 4–6 section headers with 2–3 sentences each describing:
                - The concept
                - Why it matters
                - How it fits into the topic

                KEY POINTS:
                List 5–8 important takeaways.

                DETAILED SLIDE-READY SUMMARY:
                Write a clear, structured breakdown that matches how slides would be designed. 
                For each conceptual group, include:
                - A short descriptive paragraph
                - 3–5 concise bullet points

                Ensure the tone and structure resemble a professional educational presentation.

                AUDIO TRANSCRIPT:
                {transcript}

                VISUAL DESCRIPTIONS:
                {visual_content}
                """
                
                # Generate summary using text pool
                response = self.text_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                summary_text = response.text.strip()
                
                # Parse response
                summary = self._parse_summary_response(summary_text)
                
                logger.info("✅ Video summary generated successfully (text pool)")
                return summary
                
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = '429' in error_msg or 'quota' in error_msg.lower()
                
                if is_rate_limit:
                    retry_count += 1
                    consecutive_failures += 1
                    
                    if retry_count < max_retries and consecutive_failures < max_consecutive_failures:
                        logger.warning(f"⏳ Rate limit on summary (text key #{self.text_key_index + 1})")
                        self._rotate_text_key()
                        logger.warning(f"   Retrying with text key #{self.text_key_index + 1}... ({retry_count}/{max_retries})")
                    else:
                        logger.error("❌ Summary generation failed - all text keys rate limited")
                        return self._create_fallback_summary(transcript)
                else:
                    logger.error(f"Error creating video summary: {e}")
                    return self._create_fallback_summary(transcript)
        
        return self._create_fallback_summary(transcript)
    
    def create_content_sections(self, transcript: str, 
                               num_sections: int = 5) -> Dict:
        """
        Create structured content sections with retry logic (TEXT POOL)
        
        Args:
            transcript: Full transcript text
            num_sections: Number of sections to create
            
        Returns:
            Dictionary with title, overview, and sections
        """
        max_retries = 3
        retry_count = 0
        consecutive_failures = 0
        max_consecutive_failures = len(self.api_keys)
        
        while retry_count < max_retries:
            try:
                prompt = f"""
                🚨 CRITICAL REQUIREMENT - READ FIRST 🚨
                You MUST include 1-2 slides (MAXIMUM 2!) with [COMPARISON] or [FEATURES] tags.
                Most slides should be REGULAR slides (no tags).
                Use [FEATURES]/[COMPARISON] only for truly list-like or comparative content.
                
                You are creating a PROFESSIONAL POWERPOINT PRESENTATION from a video transcript.
                This presentation will use an educational template with 5 different slide layouts.
                
                ═══════════════════════════════════════════════════════════
                SLIDE TYPES & USAGE:
                ═══════════════════════════════════════════════════════════
                
                Your slides will be mapped to different visual templates based on content type:
                
                1. 📘 REGULAR TOPIC SLIDE (USE FOR MOST SLIDES - 80% OF PRESENTATION):
                   - Use for: Standard topics, explanations, concepts, details
                   - Format: Title + 4-6 bullet points
                   - NO special tags needed
                   - This should be your DEFAULT choice
                   
                2. 🔴 COMPARISON/FEATURE SLIDE (USE SPARINGLY - ONLY 1-2 PER PRESENTATION!):
                   - Use for: ONLY when content is inherently list-like or comparative
                   - Format: Title + exactly 6 bullets (will be split into 3 columns × 2 points each)
                   - Mark with: [COMPARISON] or [FEATURES] tag after title
                   
                   🎯 WHEN TO USE [FEATURES] OR [COMPARISON] SLIDES (SELECTIVE USE ONLY):
                   ✅ Component breakdowns with 6+ distinct parts (e.g., "Core Components")
                   ✅ Direct comparisons (e.g., "X vs Y", "Before vs After")
                   ✅ Explicit feature lists (e.g., "Key Features")
                   ❌ DON'T use for: Regular explanations, how-to content, general topics
                   ❌ DON'T use for: Steps, processes, or sequential content
                   ❌ DON'T overuse - MAXIMUM 2 per presentation!
                   
                   📝 GOOD EXAMPLES (USE ONLY 1-2 OF THESE):
                   - "Core Components [FEATURES]" - when video explicitly lists 6 components
                   - "Traditional vs Agentic AI [COMPARISON]" - when comparing two approaches
                   - "Framework Options [FEATURES]" - when listing multiple framework options
                   
                   🚨 LIMIT: Use this ONLY 1-2 times per presentation!
                   
                3. IMAGE SLIDE:
                   - Automatically assigned when keyframe images are available
                   - Format: Title + 3-6 bullet points
                
                ═══════════════════════════════════════════════════════════
                CRITICAL REQUIREMENTS:
                ═══════════════════════════════════════════════════════════
                
                1. SLIDE TITLES - MUST BE CONCISE AND DESCRIPTIVE:
                   ✅ DO: "What is N8N?"
                   ✅ DO: "How It Works"
                   ✅ DO: "Building Your Agent"
                   ❌ DON'T: "Section 1", "Introduction", "Overview"
                   ❌ DON'T: Long titles with more than 5 words
                   
                   - Maximum 5 words (STRICTLY ENFORCED)
                   - Specific to the topic (not generic)
                   - Use title case
                   - Questions are allowed (e.g., "What is X?")
                
                2. BULLET POINTS:
                   - Regular slides: 4-6 bullets
                   - Comparison/Feature slides: EXACTLY 6 bullets (3 columns × 2 points each)
                   - Each bullet: 8-12 words maximum
                   - Start with action verbs or key nouns
                   - Complete, self-contained thoughts
                
                3. 🚨 CONTENT VARIETY (BALANCED APPROACH!):
                   - MOST slides (80-85%) should be REGULAR slides with NO tags
                   - ONLY 1-2 slides should have [COMPARISON] or [FEATURES] tags
                   - Use regular slides for: explanations, steps, how-tos, concepts
                   - Use feature slides for: explicit lists, comparisons, component breakdowns
                   - Strategy: Be SELECTIVE - not every list needs to be [FEATURES]
                
                ═══════════════════════════════════════════════════════════
                REQUIRED OUTPUT FORMAT:
                ═══════════════════════════════════════════════════════════
                
                TITLE:
                [Specific video title from content - max 5 words]
                
                SUBTITLE:
                [maximum 1 sentence summarizing the presentation]
                
                SLIDE 1: [Specific Descriptive Title]
                - Bullet point 1 (8-12 words)
                - Bullet point 2 (8-12 words)
                - Bullet point 3 (8-12 words)
                - Bullet point 4 (8-12 words)
                - Bullet point 5 (8-12 words)
                
                SLIDE 2: [Another Topic Title]
                - Bullet 1
                - Bullet 2
                - Bullet 3
                - Bullet 4
                - Bullet 5
                
                SLIDE 3: [Title for Features] [FEATURES]
                - Feature 1
                - Feature 2
                - Feature 3
                - Feature 4
                - Feature 5
                - Feature 6
                ⚠️  EXACTLY 6 bullets for [FEATURES]/[COMPARISON] slides!
                
                SLIDE 4: [Regular Topic Title]
                - Bullet 1
                - Bullet 2
                - Bullet 3
                - Bullet 4
                
                [Continue with REGULAR slides for most content...]
                
                SLIDE {num_sections}: [Concluding Title]
                - Takeaway 1
                - Takeaway 2
                - Takeaway 3
                - Takeaway 4
                
                ═══════════════════════════════════════════════════════════
                CONTENT GUIDELINES:
                ═══════════════════════════════════════════════════════════
                
                - Create exactly {num_sections} slides total
                - 🔴 CRITICAL: MAXIMUM 2 slides with [COMPARISON] or [FEATURES] tags
                - MOST slides should be REGULAR slides (no special tags)
                - Use regular slides for: explanations, how-tos, concepts, details
                - Use [FEATURES] only for: explicit lists, comparisons, component breakdowns
                - [COMPARISON]/[FEATURES] slides: 6 bullets (3 columns × 2 points), NO images
                - Regular slides: 4-6 bullets (MAX 6)
                - DO NOT create a "Table of Contents" or "Agenda" slide - it will be auto-generated
                - Ensure logical flow between slides
                - Use CONCISE titles - MAX 5 WORDS (not generic)
                
                ═══════════════════════════════════════════════════════════
                EXAMPLE DISTRIBUTION (for 15 slides):
                ═══════════════════════════════════════════════════════════
                
                Slides 1-14: REGULAR slides (no tags)
                Slide 3: [FEATURES] slide (if content has explicit feature list)
                Slide 8: [COMPARISON] slide (if content has comparison)
                Slide 15: REGULAR conclusion slide
                
                👉 Notice: Only 2 out of 15 slides use special tags!
                
                ═══════════════════════════════════════════════════════════
                TRANSCRIPT TO ANALYZE:
                ═══════════════════════════════════════════════════════════
                {transcript}
                """
                
                response = self.text_client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                result = self._parse_sections_response(response.text.strip())
                
                logger.info(f"✅ Created {len(result['sections'])} content sections (text pool)")
                return result
                
            except Exception as e:
                error_msg = str(e)
                is_rate_limit = '429' in error_msg or 'quota' in error_msg.lower()
                
                if is_rate_limit:
                    retry_count += 1
                    consecutive_failures += 1
                    
                    if retry_count < max_retries and consecutive_failures < max_consecutive_failures:
                        logger.warning(f"⏳ Rate limit on section creation (text key #{self.text_key_index + 1})")
                        self._rotate_text_key()
                        logger.warning(f"   Retrying with text key #{self.text_key_index + 1}... ({retry_count}/{max_retries})")
                    else:
                        logger.error("❌ Section creation failed - all text keys rate limited")
                        return self._create_fallback_sections(transcript, num_sections)
                else:
                    logger.error(f"Error creating content sections: {e}")
                    return self._create_fallback_sections(transcript, num_sections)
        
        return self._create_fallback_sections(transcript, num_sections)
    
    # ========================================================================
    # HELPER FUNCTIONS (unchanged)
    # ========================================================================
    
    def _extract_wait_time(self, error_message: str) -> float:
        """
        Extract wait time from rate limit error message
        
        Args:
            error_message: Error message from API
            
        Returns:
            Wait time in seconds (with 5s buffer added)
        """
        # Default wait time
        default_wait = 60
        
        try:
            # Try to find "retry in XX.XXs" pattern
            match = re.search(r'retry in ([\d.]+)s', error_message)
            if match:
                wait_time = float(match.group(1))
                # Add 5 second buffer for safety
                return wait_time + 5
            
            # Try to find "seconds: XX" pattern
            match = re.search(r'seconds["\s:]+(\\d+)', error_message)
            if match:
                wait_time = float(match.group(1))
                return wait_time + 5
                
        except Exception as e:
            logger.debug(f"Could not parse wait time: {e}")
        
        # Return default if parsing failed
        logger.debug(f"Using default wait time: {default_wait}s")
        return default_wait
    
    def _create_fallback_summary(self, transcript: str) -> Dict:
        """Create basic summary when AI generation fails"""
        return {
            'title': 'Video Summary',
            'overview': transcript[:200] + '...' if len(transcript) > 200 else transcript,
            'key_points': ['Summary generation unavailable due to rate limits'],
            'detailed_summary': transcript
        }
    
    def _create_fallback_sections(self, transcript: str, num_sections: int) -> Dict:
        """Create basic sections when AI generation fails"""
        # Split transcript into roughly equal parts
        words = transcript.split()
        words_per_section = len(words) // num_sections
        
        sections = []
        for i in range(num_sections):
            start = i * words_per_section
            end = start + words_per_section if i < num_sections - 1 else len(words)
            section_text = ' '.join(words[start:end])
            
            sections.append({
                'title': f'Section {i+1}',
                'content': [section_text[:200] + '...']
            })
        
        return {
            'title': 'Video Content Summary',
            'overview': transcript[:200] + '...',
            'sections': sections,
            'takeaways': ['Summary generation unavailable']
        }
    
    def _parse_summary_response(self, text: str) -> Dict[str, any]:
        """Parse structured summary response - supports multiple formats"""
        result = {
            'title': 'Video Summary',
            'overview': '',
            'key_points': [],
            'detailed_summary': ''
        }
        
        try:
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('TITLE:'):
                    result['title'] = line.replace('TITLE:', '').strip()
                elif line.startswith('OVERVIEW:'):
                    result['overview'] = line.replace('OVERVIEW:', '').strip()
                    current_section = 'overview'
                # Support both old and new section headers
                elif line.startswith(('KEY POINTS:', 'MAIN SECTIONS:')):
                    current_section = 'key_points'
                elif line.startswith(('DETAILED SUMMARY:', 'DETAILED SLIDE-READY SUMMARY:')):
                    current_section = 'detailed_summary'
                elif line.startswith('- ') and current_section == 'key_points':
                    result['key_points'].append(line[2:].strip())
                elif current_section == 'overview' and line and not line.startswith(('TITLE:', 'KEY POINTS:', 'MAIN SECTIONS:')):
                    result['overview'] += ' ' + line
                elif current_section == 'detailed_summary' and line:
                    result['detailed_summary'] += line + '\n'
            
            result['overview'] = result['overview'].strip()
            result['detailed_summary'] = result['detailed_summary'].strip()
            
        except Exception as e:
            logger.error(f"Error parsing summary: {e}")
        
        return result
    
    def _parse_sections_response(self, text: str) -> Dict:
        """Parse structured sections response - supports both SLIDE X: and SECTION X: formats"""
        result = {
            'title': 'Content Summary',
            'overview': '',
            'sections': [],
            'takeaways': []
        }
        
        try:
            # Log the first 800 chars of Gemini response for debugging
            logger.info(f"📥 RAW Gemini Response (first 800 chars):")
            logger.info(f"{text[:800]}")
            logger.info(f"{'='*60}")
            
            lines = text.split('\n')
            current_section = None
            current_section_data = None
            current_paragraph = []
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Try to find TITLE (content might be on same line or next line)
                if line.upper().startswith('TITLE:'):
                    title_text = line[6:].strip()
                    if not title_text and i + 1 < len(lines):
                        title_text = lines[i + 1].strip()
                        i += 1
                    result['title'] = title_text
                    logger.info(f"✅ Found TITLE: '{result['title']}'")
                # Try to find SUBTITLE or OVERVIEW (content might be on same line or next lines)
                elif line.upper().startswith(('SUBTITLE:', 'OVERVIEW:')):
                    overview_text = line[9:].strip()
                    if not overview_text and i + 1 < len(lines):
                        overview_lines = []
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().startswith(('SLIDE ', 'SECTION ')):
                            if lines[j].strip():
                                overview_lines.append(lines[j].strip())
                            j += 1
                        overview_text = ' '.join(overview_lines)
                        i = j - 1
                    result['overview'] = overview_text
                    logger.info(f"✅ Found SUBTITLE: '{result['overview'][:100]}...'")
                    
                # Support both SLIDE X: and SECTION X: formats
                elif line.startswith(('SLIDE ', 'SECTION ')):
                    # Save previous section if exists
                    if current_section_data:
                        # Add any pending paragraph content
                        if current_paragraph:
                            current_section_data['content'].append(' '.join(current_paragraph))
                            current_paragraph = []
                        result['sections'].append(current_section_data)
                
                    # Extract title after the colon
                    title = line.split(':', 1)[1].strip() if ':' in line else line
                    current_section_data = {'title': title, 'content': []}
                elif line.startswith('KEY TAKEAWAYS:'):
                    # Save current section before processing takeaways
                    if current_section_data:
                        if current_paragraph:
                            current_section_data['content'].append(' '.join(current_paragraph))
                            current_paragraph = []
                        result['sections'].append(current_section_data)
                        current_section_data = None
                    current_section = 'takeaways'
                elif line.startswith('- '):
                    # Bullet point
                    content = line[2:].strip()
                    if current_section == 'takeaways':
                        result['takeaways'].append(content)
                    elif current_section_data:
                        # Flush paragraph if exists before adding bullet
                        if current_paragraph:
                            current_section_data['content'].append(' '.join(current_paragraph))
                            current_paragraph = []
                        current_section_data['content'].append(content)
                elif line and current_section_data:
                    # Regular paragraph text - accumulate it
                    current_paragraph.append(line)
                
                i += 1  # Increment loop counter
            
            # Add final pending content
            if current_section_data:
                if current_paragraph:
                    current_section_data['content'].append(' '.join(current_paragraph))
                result['sections'].append(current_section_data)
            
            # Log final result
            logger.info(f"📊 PARSED: title='{result['title']}' (len={len(result['title'])}), overview_len={len(result['overview'])}, sections={len(result['sections'])}")
            
            # Warn if title is still default
            if result['title'] == 'Content Summary':
                logger.warning(f"⚠️  Title was not found in Gemini response! Using default.")
            if not result['overview']:
                logger.warning(f"⚠️  Overview was not found in Gemini response!")
            
        except Exception as e:
            logger.error(f"Error parsing sections: {e}")
        
        return result


def test_gemini_connection(api_key: str = None) -> bool:
    """
    Test Gemini API connection
    
    Args:
        api_key: API key to test (uses config if None)
        
    Returns:
        True if connection successful
    """
    try:
        # Test with first available key
        api_keys = [api_key] if api_key else config.GEMINI_API_KEYS
        if not api_keys or len(api_keys) == 0:
            raise ValueError("No API keys available for testing")
        
        processor = GeminiProcessor(api_keys=api_keys)
        
        # Simple test prompt (using text pool)
        response = processor.text_client.models.generate_content(
            model=processor.model_name,
            contents="Say 'Hello, Gemini is working!'"
        )
        result = response.text.strip()
        
        logger.info(f"✅ Gemini test successful: {result}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gemini test failed: {e}")
        return False