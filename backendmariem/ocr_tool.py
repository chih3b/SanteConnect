"""
ocr_tool.py - OCR Document Processing Tool
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Try to import OCR libraries
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("⚠️ pytesseract not available")

try:
    import pdf2image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("⚠️ pdf2image not available")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class MedicalOCRTool:
    """OCR tool for medical documents"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        logger.info(f"✅ OCR Tool initialized (Tesseract: {TESSERACT_AVAILABLE})")
    
    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and extract text"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            ext = path.suffix.lower()
            
            if ext not in self.supported_formats:
                return {'success': False, 'error': f'Unsupported format: {ext}'}
            
            if ext == '.pdf':
                text = self._process_pdf(path)
            else:
                text = self._process_image(path)
            
            return {
                'success': True,
                'text': text,
                'filename': path.name,
                'length': len(text),
                'method': 'tesseract_ocr'
            }
        
        except Exception as e:
            logger.error(f"❌ OCR error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _process_pdf(self, path: Path) -> str:
        """Process PDF document"""
        text_parts = []
        
        # Try pdfplumber first (for text-based PDFs)
        if PDFPLUMBER_AVAILABLE:
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                
                if text_parts:
                    return '\n\n'.join(text_parts)
            except Exception as e:
                logger.warning(f"pdfplumber failed: {e}")
        
        # Fall back to OCR for scanned PDFs
        if PDF2IMAGE_AVAILABLE and TESSERACT_AVAILABLE:
            try:
                images = pdf2image.convert_from_path(path)
                for i, image in enumerate(images):
                    text = pytesseract.image_to_string(image, lang='fra+eng')
                    if text.strip():
                        text_parts.append(f"--- Page {i+1} ---\n{text}")
                
                return '\n\n'.join(text_parts)
            except Exception as e:
                logger.error(f"PDF OCR failed: {e}")
        
        return "Could not extract text from PDF"
    
    def _process_image(self, path: Path) -> str:
        """Process image with OCR"""
        if not TESSERACT_AVAILABLE:
            return "OCR not available (pytesseract not installed)"
        
        try:
            image = Image.open(path)
            text = pytesseract.image_to_string(image, lang='fra+eng')
            return text.strip()
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return f"OCR failed: {str(e)}"
