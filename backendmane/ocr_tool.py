"""
Advanced OCR tool for medical documents
"""
import re
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image, ImageEnhance, ImageFilter

logging.basicConfig(level=logging.INFO)

# Try to import optional dependencies
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract not available - OCR will be limited")

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class MedicalOCRTool:
    """OCR tool for medical documents with preprocessing"""
    
    def __init__(self):
        self.tesseract_config = '--psm 6 --oem 3'
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process medical document (PDF or image)
        
        Args:
            file_path: Path to PDF or image file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            return {
                'success': False,
                'error': f'File not found: {file_path}',
                'text': ''
            }
        
        try:
            suffix = path.suffix.lower()
            
            if suffix == '.pdf':
                text, method = self._extract_from_pdf(file_path)
            elif suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                text, method = self._extract_from_image(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {suffix}',
                    'text': ''
                }
            
            # Clean text
            text = self._clean_text(text)
            
            return {
                'success': True,
                'text': text,
                'method': method,
                'length': len(text),
                'error': None
            }
            
        except Exception as e:
            logging.error(f"Error processing document: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }
    
    def _extract_from_pdf(self, pdf_path: str) -> Tuple[str, str]:
        """Extract text from PDF"""
        # Try pdfplumber first
        if PDFPLUMBER_AVAILABLE:
            try:
                text_parts = []
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                
                if text_parts and len("".join(text_parts)) > 100:
                    return "\n\n".join(text_parts), "pdfplumber"
            except Exception as e:
                logging.warning(f"pdfplumber failed: {e}")
        
        # Fallback to OCR
        if PDF2IMAGE_AVAILABLE and TESSERACT_AVAILABLE:
            try:
                images = convert_from_path(pdf_path, dpi=300)
                text_parts = []
                
                for i, img in enumerate(images):
                    processed_img = self._preprocess_image(img)
                    page_text = pytesseract.image_to_string(
                        processed_img, 
                        config=self.tesseract_config
                    )
                    if page_text.strip():
                        text_parts.append(f"=== Page {i+1} ===\n{page_text}")
                
                return "\n\n".join(text_parts), "ocr_pdf"
            except Exception as e:
                logging.error(f"OCR PDF failed: {e}")
        
        return "", "extraction_failed"
    
    def _extract_from_image(self, image_path: str) -> Tuple[str, str]:
        """Extract text from image using OCR"""
        if not TESSERACT_AVAILABLE:
            return "", "tesseract_not_available"
        
        try:
            img = Image.open(image_path)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            processed_img = self._preprocess_image(img)
            text = pytesseract.image_to_string(
                processed_img,
                config=self.tesseract_config
            )
            
            return text, "ocr_image"
        except Exception as e:
            logging.error(f"Image OCR failed: {e}")
            return "", "ocr_failed"
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR"""
        width, height = image.size
        if width < 1500:
            scale = 1500 / width
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        
        # Denoise
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove bullet artifacts
        text = re.sub(r"[@•·\*\u2022\u2023\u25E6\u2043\u2219]", " ", text)
        
        # Clean punctuation artifacts
        text = re.sub(r"\s[.,;:!?']\s", " ", text)
        
        # Normalize whitespace
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        lines = [line.strip() for line in text.splitlines()]
        return '\n'.join(lines).strip()
    
    def is_available(self) -> bool:
        """Check if OCR is available"""
        return TESSERACT_AVAILABLE


# Singleton instance
ocr_tool = MedicalOCRTool()
