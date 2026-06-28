"""Keyframe extraction using OpenCV with duplicate removal"""

import cv2
import numpy as np
from pathlib import Path
import logging
from typing import List, Tuple, Dict
import pytesseract
from difflib import SequenceMatcher
import config

logger = logging.getLogger(__name__)

# Configure Tesseract path from config
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD


class KeyframeExtractor:
    """Extract keyframes with intelligent duplicate removal"""

    def __init__(
        self,
        motion_threshold=30,
        histogram_threshold=0.7,
        min_frame_interval=30,
        max_keyframes=20,
    ):
        self.motion_threshold = motion_threshold
        self.histogram_threshold = histogram_threshold
        self.min_frame_interval = min_frame_interval
        self.max_keyframes = max_keyframes

    def _is_blank_frame(self, frame) -> bool:
        """Detect if frame is blank/black/white"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Blank if very dark or very bright with low variation
        is_blank = (mean_brightness < 20 or mean_brightness > 235) and std_brightness < 30
        return is_blank

    def _extract_text(self, frame) -> str:
        """Extract text content from frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(thresh)
            return text.strip()
        except Exception as e:
            logger.debug(f"Text extraction error: {e}")
            return ""

    def _calculate_image_similarity(self, img1, img2) -> float:
        """Calculate visual similarity between two images (0-1, 1=identical)"""
        # Resize for faster comparison
        img1_small = cv2.resize(img1, (64, 64))
        img2_small = cv2.resize(img2, (64, 64))
        
        # Convert to grayscale
        gray1 = cv2.cvtColor(img1_small, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2_small, cv2.COLOR_BGR2GRAY)
        
        # Histogram comparison
        hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        hist_similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # Structural similarity (pixel difference)
        mse = np.mean((gray1.astype(float) - gray2.astype(float)) ** 2)
        max_mse = 255 ** 2
        structural_similarity = 1 - (mse / max_mse)
        
        # Combined similarity
        similarity = (hist_similarity * 0.5) + (structural_similarity * 0.5)
        return similarity

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity (0-1, 1=identical)"""
        if not text1 or not text2:
            return 0.0
        if len(text1) < 10 or len(text2) < 10:
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()

    def _remove_duplicates(self, keyframes: List[Dict], max_keep: int) -> List[Dict]:
        """
        Remove duplicate/similar keyframes keeping most diverse ones
        
        Args:
            keyframes: List of keyframe dicts with 'frame', 'text', 'score', etc.
            max_keep: Maximum number of keyframes to keep
            
        Returns:
            Filtered list of unique keyframes
        """
        if len(keyframes) <= max_keep:
            return keyframes
        
        logger.info(f"🔍 Removing duplicates from {len(keyframes)} keyframes...")
        
        # Sort by score (keep best ones first)
        keyframes.sort(key=lambda x: x['score'], reverse=True)
        
        unique_keyframes = []
        
        for candidate in keyframes:
            is_duplicate = False
            
            for unique_kf in unique_keyframes:
                # Check text similarity
                text_sim = self._calculate_text_similarity(candidate['text'], unique_kf['text'])
                
                # Check visual similarity
                visual_sim = self._calculate_image_similarity(candidate['frame'], unique_kf['frame'])
                
                # Determine if duplicate
                # High text similarity (>80%) OR high visual similarity (>85%) = duplicate
                if text_sim > 0.80:
                    logger.debug(f"  ❌ Duplicate TEXT: {text_sim:.2f} similarity")
                    is_duplicate = True
                    break
                elif visual_sim > 0.85:
                    logger.debug(f"  ❌ Duplicate VISUAL: {visual_sim:.2f} similarity")
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_keyframes.append(candidate)
                logger.info(f"  ✅ Kept keyframe at {candidate['timestamp']:.2f}s (unique)")
                
                if len(unique_keyframes) >= max_keep:
                    break
        
        # Sort by timestamp
        unique_keyframes.sort(key=lambda x: x['index'])
        
        logger.info(f"✅ Reduced from {len(keyframes)} to {len(unique_keyframes)} unique keyframes")
        return unique_keyframes

    def extract_keyframes(self, video_path: str, output_dir: str = None) -> List[Tuple[int, str]]:
        """
        Extract keyframes with GUARANTEED distribution across entire video
        
        Args:
            video_path: Path to input video file
            output_dir: Directory to save keyframes
            
        Returns:
            List of tuples (frame_number, frame_path)
        """
        logger.info(f"Starting TWO-PHASE keyframe extraction from {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_duration = total_frames / fps
        
        logger.info(f"Video info: {total_frames} frames, {fps:.2f} fps, {video_duration:.1f}s duration")
        logger.info(f"🎯 Target: {self.max_keyframes} unique keyframes")
        
        # Phase 1: Sample frames ACROSS ENTIRE VIDEO (not sequentially!)
        logger.info(f"📊 PHASE 1: Sampling frames across ENTIRE video...")
        
        # Calculate how many frames to sample (2x target to allow for duplicates)
        target_candidates = self.max_keyframes * 2
        
        # Create sampling intervals distributed across entire video
        # This ensures we look at beginning, middle, AND end!
        sample_indices = np.linspace(
            30,  # Skip first 30 frames (often blank/intro)
            total_frames - 30,  # Skip last 30 frames (often blank/outro)
            target_candidates * 2  # Sample even MORE to ensure coverage
        ).astype(int)
        
        logger.info(f"  📍 Sampling {len(sample_indices)} frames from 0.0s to {video_duration:.1f}s")
        
        candidates = []
        prev_frame = None
        prev_gray = None
        prev_hist = None
        
        for i, frame_idx in enumerate(sample_indices):
            # Progress logging
            if i % 10 == 0:
                progress = (i / len(sample_indices)) * 100
                time_at = frame_idx / fps
                logger.info(f"  Analyzing: {progress:.1f}% | Time: {time_at:.1f}s/{video_duration:.1f}s | Candidates: {len(candidates)}")
            
            # Jump to specific frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                continue
            
            # Skip blank frames
            if self._is_blank_frame(frame):
                continue
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            # Extract text
            text_content = self._extract_text(frame)
            has_text = len(text_content) > 20
            
            # Calculate scores
            score = 0
            reason = ""
            
            if has_text:
                score = 100
                reason = "TEXT"
            elif prev_frame is not None:
                # Motion detection
                frame_diff = cv2.absdiff(gray, prev_gray)
                motion_score = np.mean(frame_diff)
                
                # Scene change
                hist_similarity = cv2.compareHist(hist, prev_hist, cv2.HISTCMP_CORREL)
                scene_score = (1 - hist_similarity) * 100
                
                # Edge detection (visual complexity)
                edges = cv2.Canny(gray, 50, 150)
                edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
                complexity_score = edge_density * 50
                
                # Combined scoring
                if motion_score > self.motion_threshold:
                    score = motion_score + complexity_score
                    reason = f"MOTION ({motion_score:.1f})"
                elif scene_score > 30:
                    score = scene_score + complexity_score
                    reason = f"SCENE ({hist_similarity:.2f})"
                else:
                    score = complexity_score
                    reason = f"VISUAL ({complexity_score:.1f})"
            else:
                # First valid frame
                score = 50
                reason = "FIRST_VALID"
            
            # Add as candidate if score is decent
            if score > 25:  # Lower threshold to collect more candidates
                candidates.append({
                    'index': frame_idx,
                    'frame': frame.copy(),
                    'text': text_content,
                    'score': score,
                    'reason': reason,
                    'timestamp': frame_idx / fps
                })
            
            prev_frame = frame
            prev_gray = gray
            prev_hist = hist
            
            # Stop if we have enough high-quality candidates
            if len(candidates) >= target_candidates:
                break
        
        cap.release()
        
        logger.info(f"✅ Phase 1 complete: Collected {len(candidates)} candidates across entire video")
        logger.info(f"   📍 Time range: {candidates[0]['timestamp']:.1f}s to {candidates[-1]['timestamp']:.1f}s")
        
        # Phase 2: Remove duplicates and select best diverse frames
        logger.info(f"🔍 PHASE 2: Removing duplicates and selecting best {self.max_keyframes}...")
        
        unique_keyframes = self._remove_duplicates(candidates, self.max_keyframes)
        
        # Phase 3: Save keyframes
        logger.info("💾 PHASE 3: Saving final keyframes...")
        
        keyframes = []
        for i, kf in enumerate(unique_keyframes):
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                filename = f"keyframe_{i:03d}_t{kf['timestamp']:.2f}s.jpg"
                filepath = str(Path(output_dir) / filename)
                cv2.imwrite(filepath, kf['frame'])
                keyframes.append((kf['index'], filepath))
                
                text_indicator = "📝" if len(kf['text']) > 20 else "🎬"
                logger.info(f"  {text_indicator} {filename} | {kf['reason']} | Score: {kf['score']:.1f}")
            else:
                keyframes.append((kf['index'], kf['frame']))
        
        text_count = sum(1 for kf in unique_keyframes if len(kf['text']) > 20)
        visual_count = len(unique_keyframes) - text_count
        
        first_time = unique_keyframes[0]['timestamp']
        last_time = unique_keyframes[-1]['timestamp']
        time_span = last_time - first_time
        
        logger.info("=" * 70)
        logger.info(f"✅ FINAL RESULT: {len(keyframes)} unique keyframes")
        logger.info(f"   📝 Text frames: {text_count}")
        logger.info(f"   🎬 Visual frames: {visual_count}")
        logger.info(f"   ⏱️  Time span: {first_time:.1f}s to {last_time:.1f}s ({time_span:.1f}s covered)")
        logger.info(f"   📊 Coverage: {(time_span/video_duration)*100:.1f}% of video")
        logger.info("=" * 70)
        
        return keyframes

    def _add_evenly_spaced_frames(
        self, video_path: str, output_dir: str, count: int
    ) -> List[Tuple[int, str]]:
        """Extract evenly spaced frames as fallback"""
        logger.info(f"Fallback: Extracting {count} evenly spaced frames")
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        keyframes = []
        frame_indices = np.linspace(0, total_frames - 1, count, dtype=int)

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            
            if ret and not self._is_blank_frame(frame):
                if output_dir:
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                    timestamp = idx / fps
                    filename = f"keyframe_{len(keyframes):03d}_t{timestamp:.2f}s.jpg"
                    filepath = str(Path(output_dir) / filename)
                    cv2.imwrite(filepath, frame)
                    keyframes.append((idx, filepath))
                else:
                    keyframes.append((idx, frame))

        cap.release()
        return keyframes
