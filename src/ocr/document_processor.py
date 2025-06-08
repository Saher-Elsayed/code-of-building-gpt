import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
from typing import List, Dict, Any
import logging
from pathlib import Path
import os
import sys

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import settings

class DocumentProcessor:
    def __init__(self, tesseract_path: str = None, poppler_path: str = None):
        # Set Tesseract path
        if tesseract_path or settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path or settings.TESSERACT_PATH
        
        # Set Poppler path for pdf2image
        self.poppler_path = poppler_path or settings.POPPLER_PATH
        
        self.logger = logging.getLogger(__name__)
        
        # Test if Tesseract is working
        self._test_tesseract()
    
    def _test_tesseract(self):
        """Test if Tesseract is properly configured"""
        try:
            # Create a simple test image
            test_image = Image.new('RGB', (100, 50), color='white')
            pytesseract.image_to_string(test_image)
            self.logger.info("Tesseract is working correctly")
        except Exception as e:
            self.logger.error(f"Tesseract test failed: {e}")
            self.logger.error("Please check your Tesseract installation and path in .env file")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR"""
        try:
            # Convert to OpenCV format
            img_array = np.array(image)
            
            # Handle different image modes
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Noise removal
            denoised = cv2.medianBlur(gray, 5)
            
            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Convert back to PIL
            return Image.fromarray(enhanced)
        
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed: {e}, using original image")
            return image
    
    def extract_text_from_pdf(self, pdf_path: str, dpi: int = None) -> List[Dict[str, Any]]:
        """Extract text from PDF with page information"""
        dpi = dpi or settings.DPI
        pages_data = []
        
        try:
            self.logger.info(f"Starting PDF processing: {pdf_path}")
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path, dpi=dpi)
            
            self.logger.info(f"PDF converted to {len(pages)} images")
            
            for i, page in enumerate(pages):
                self.logger.info(f"Processing page {i+1}/{len(pages)}")
                
                # Preprocess image
                processed_page = self.preprocess_image(page)
                
                # OCR with detailed output
                try:
                    ocr_data = pytesseract.image_to_data(
                        processed_page, 
                        output_type=pytesseract.Output.DICT,
                        config='--psm 6'
                    )
                    
                    # Extract text with confidence scores
                    page_text = self.extract_structured_text(ocr_data)
                    
                    pages_data.append({
                        'page_number': i + 1,
                        'text': page_text['text'],
                        'confidence': page_text['avg_confidence'],
                        'structure': page_text['structure'],
                        'source': os.path.basename(pdf_path)
                    })
                    
                except Exception as e:
                    self.logger.error(f"OCR failed for page {i+1}: {e}")
                    # Add empty page data to maintain page numbering
                    pages_data.append({
                        'page_number': i + 1,
                        'text': '',
                        'confidence': 0,
                        'structure': {'paragraphs': 0, 'total_words': 0},
                        'source': os.path.basename(pdf_path)
                    })
                
        except Exception as e:
            self.logger.error(f"Error processing PDF: {e}")
            raise
            
        self.logger.info(f"PDF processing complete: {len(pages_data)} pages processed")
        return pages_data
    
    def extract_structured_text(self, ocr_data: Dict) -> Dict[str, Any]:
        """Extract text while preserving structure"""
        text_blocks = []
        current_paragraph = []
        valid_confidences = []
        
        for i in range(len(ocr_data['text'])):
            confidence = ocr_data['conf'][i]
            text = ocr_data['text'][i].strip()
            
            if confidence > 30 and text:  # Filter low confidence
                current_paragraph.append(text)
                valid_confidences.append(confidence)
                
                # Detect paragraph breaks (when block number changes)
                next_block = ocr_data['block_num'][i+1] if i+1 < len(ocr_data['text']) else None
                current_block = ocr_data['block_num'][i]
                
                if next_block is None or current_block != next_block:
                    if current_paragraph:
                        text_blocks.append(' '.join(current_paragraph))
                        current_paragraph = []
        
        # Handle any remaining paragraph
        if current_paragraph:
            text_blocks.append(' '.join(current_paragraph))
        
        avg_confidence = np.mean(valid_confidences) if valid_confidences else 0
        
        return {
            'text': '\n\n'.join(text_blocks),
            'avg_confidence': float(avg_confidence),
            'structure': {
                'paragraphs': len(text_blocks),
                'total_words': len(' '.join(text_blocks).split()) if text_blocks else 0
            }
        }
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract text from a single image"""
        try:
            image = Image.open(image_path)
            processed_image = self.preprocess_image(image)
            
            ocr_data = pytesseract.image_to_data(
                processed_image,
                output_type=pytesseract.Output.DICT,
                config='--psm 6'
            )
            
            text_data = self.extract_structured_text(ocr_data)
            
            return {
                'text': text_data['text'],
                'confidence': text_data['avg_confidence'],
                'structure': text_data['structure'],
                'source': os.path.basename(image_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {e}")
            return {
                'text': '',
                'confidence': 0,
                'structure': {'paragraphs': 0, 'total_words': 0},
                'source': os.path.basename(image_path)
            }