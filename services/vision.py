import requests
import pytesseract
from PIL import Image
import cv2
import numpy as np
import base64
import io

# Configure tesseract path for macOS
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

# Initialize EasyOCR (lazy loading)
_easy_ocr = None

def get_easy_ocr():
    """Get or initialize EasyOCR instance"""
    global _easy_ocr
    if _easy_ocr is None:
        try:
            import easyocr
            # Initialize with French, English, and Arabic support
            _easy_ocr = easyocr.Reader(
                ['fr', 'en'],  # French and English (most drug names)
                gpu=False,      # CPU mode (works on all machines)
                verbose=False   # Suppress logs
            )
            print("✅ EasyOCR initialized successfully")
        except ImportError:
            print("⚠️ EasyOCR not installed, falling back to Tesseract")
            _easy_ocr = False  # Mark as unavailable
        except Exception as e:
            print(f"⚠️ EasyOCR initialization failed: {e}")
            _easy_ocr = False
    return _easy_ocr if _easy_ocr else None

def identify_medication(image: Image.Image) -> dict:
    """Identify medication using EasyOCR, Tesseract OCR, and Ollama LLaVA as fallback"""
    
    # Try EasyOCR first (best accuracy for product labels)
    ocr_result = None
    easy_ocr = get_easy_ocr()
    
    if easy_ocr:
        try:
            print("🔍 Trying EasyOCR...")
            ocr_result = identify_with_easy(image)
            if ocr_result.get("drug_name") and len(ocr_result.get("drug_name", "")) > 2:
                drug_name = ocr_result.get("drug_name", "")
                
                # Check if drug exists in database
                from services.drug_db import get_drug_info, search_similar_drugs
                
                # Always use fuzzy search first to get best match (handles "fort" variants)
                similar = search_similar_drugs(drug_name, limit=3)
                if similar and similar[0]["similarity_score"] >= 70:
                    # Use fuzzy match if score is good
                    matched_name = similar[0]["drug_name"]
                    score = similar[0]["similarity_score"]
                    print(f"✅ EasyOCR fuzzy match: '{drug_name}' → '{matched_name}' (score: {score})")
                    ocr_result["drug_name"] = matched_name
                    ocr_result["original_ocr"] = drug_name
                    ocr_result["fuzzy_match"] = True
                    ocr_result["fuzzy_score"] = score
                    return ocr_result
                
                # Fallback to direct match
                drug_info = get_drug_info(drug_name)
                if drug_info:
                    print(f"✅ EasyOCR found match: {drug_name}")
                    return ocr_result
                
                # EasyOCR gave valid result but not in database - skip Tesseract, go to LLaVA
                if is_valid_drug_name(drug_name):
                    print(f"⚠️ EasyOCR result '{drug_name}' not found in database, trying LLaVA...")
        except Exception as e:
            print(f"EasyOCR failed: {e}")
    
    # Tesseract fallback is disabled - EasyOCR is more accurate for product labels
    # Go directly to LLaVA if EasyOCR fails
    
    # Fallback to Ollama LLaVA if EasyOCR failed or gave garbage
    try:
        print("🤖 Using LLaVA vision model as fallback...")
        result = identify_with_ollama(image)
        
        # Check if LLaVA detected no medication in the image
        if result.get("no_medication"):
            return {"error": "No medication detected in image. Please take a photo of a medication box or packaging.", "drug_name": None, "no_medication": True}
        
        if result.get("drug_name"):
            # Check if LLaVA result is in database
            from services.drug_db import get_drug_info, search_similar_drugs
            drug_name = result.get("drug_name")
            
            drug_info = get_drug_info(drug_name)
            if drug_info:
                print(f"✅ LLaVA found exact match: {drug_name}")
                return result
            
            # Try fuzzy search
            similar = search_similar_drugs(drug_name, limit=3)
            if similar and similar[0]["similarity_score"] >= 50:
                print(f"✅ LLaVA fuzzy match: '{drug_name}' → '{similar[0]['drug_name']}' (score: {similar[0]['similarity_score']})")
                result["drug_name"] = similar[0]["drug_name"]
                result["original_llava"] = drug_name
                result["fuzzy_match"] = True
                return result
            
            if is_valid_drug_name(drug_name):
                print(f"⚠️ LLaVA result '{drug_name}' not in database")
                return result
    except Exception as e:
        print(f"Ollama failed: {e}")
    
    # Return OCR result even if questionable, or error
    if ocr_result and ocr_result.get("drug_name"):
        return ocr_result
    
    return {"error": "Could not identify medication", "drug_name": None}

def is_valid_drug_name(name: str) -> bool:
    """Check if extracted text looks like a valid drug name"""
    if not name or len(name) < 3:
        return False
    
    # Should have mostly letters
    alpha_count = sum(1 for c in name if c.isalpha())
    total_len = len(name.replace(' ', ''))
    
    if total_len == 0 or alpha_count < total_len * 0.6:  # Lowered from 0.7 to be more tolerant
        return False
    
    # Should not have too many spaces (indicates multiple words/garbage)
    words = name.split()
    if len(words) > 4:  # Drug names are usually 1-3 words
        return False
    
    # Should not have too many special characters
    special_count = sum(1 for c in name if not c.isalnum() and c != ' ' and c != '-')
    if special_count > 2:
        return False
    
    # Should not be all numbers
    if name.replace(' ', '').replace('-', '').isdigit():
        return False
    
    # Check if it contains common garbage patterns (OCR errors)
    garbage_patterns = ['jes', 'ent', 'Liorane', 'Adulte', 'eus', 'RCE', 'TR', 'EJupsA']
    name_lower = name.lower()
    for pattern in garbage_patterns:
        if pattern.lower() == name_lower:  # Exact match to garbage
            return False
    
    # Should be reasonable length (most drug names are 4-20 characters)
    clean_name = name.replace(' ', '').replace('-', '')
    if len(clean_name) < 3 or len(clean_name) > 25:  # Lowered minimum from 4 to 3
        return False
    
    return True

def identify_with_ollama(image: Image.Image) -> dict:
    """Use ESPRIT Token Factory LLaVA API to identify medication"""
    
    # Convert image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    # Use ESPRIT API
    result = identify_with_esprit(image, img_base64)
    if result and result.get("drug_name"):
        return result
    
    return {"drug_name": None, "method": "esprit_llava", "confidence": 0}


def identify_with_esprit(image: Image.Image, img_base64: str = None) -> dict:
    """Use ESPRIT Token Factory LLaVA API to identify medication"""
    try:
        import httpx
        from openai import OpenAI
        from config import ESPRIT_API_KEY, ESPRIT_API_URL, ESPRIT_VISION_MODEL
        
        if not img_base64:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        print("🌐 Using ESPRIT Token Factory LLaVA API...")
        
        # Create client with SSL verification disabled and timeout (as per ESPRIT docs)
        http_client = httpx.Client(verify=False, timeout=httpx.Timeout(60.0, connect=10.0))
        
        client = OpenAI(
            api_key=ESPRIT_API_KEY,
            base_url=ESPRIT_API_URL,
            http_client=http_client
        )
        
        response = client.chat.completions.create(
            model=ESPRIT_VISION_MODEL,
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': '''Look at this image carefully. Is there a medication box, pill bottle, or medicine packaging visible?

If YES: Reply with ONLY the brand name of the medication (e.g., "Doliprane", "Fervex", "Augmentin").
If NO medication is visible (e.g., it's a selfie, person, landscape, food, or any non-medication image): Reply with exactly "NO_MEDICATION_FOUND".

Important: Only identify actual medication packaging. Do not guess or hallucinate drug names.'''},
                        {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{img_base64}'}}
                    ]
                }
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"✅ ESPRIT LLaVA response: {response_text}")
        
        # Check if no medication was found
        no_med_indicators = ['no_medication', 'no medication', 'not a medication', 'no drug', 'no medicine', 
                            'cannot identify', "can't identify", 'not visible', 'no packaging', 'selfie',
                            'person', 'face', 'human']
        response_lower = response_text.lower()
        if any(indicator in response_lower for indicator in no_med_indicators):
            print("ℹ️ No medication detected in image")
            return {"drug_name": None, "method": "esprit_llava", "confidence": 0, "no_medication": True}
        
        # Parse the response
        parsed = parse_ollama_response(response_text)
        
        if parsed.get("drug_name"):
            parsed["method"] = "esprit_llava"
            parsed["confidence"] = 0.75
            return parsed
        
        # If parsing failed, try to use the raw response as drug name
        clean_name = response_text.strip().split('\n')[0].strip()
        if clean_name and len(clean_name) >= 3 and len(clean_name) <= 30:
            # Try fuzzy match before returning
            from services.drug_db import search_similar_drugs
            similar = search_similar_drugs(clean_name, limit=3)
            if similar and similar[0]["similarity_score"] >= 50:
                matched_name = similar[0]["drug_name"]
                print(f"✅ ESPRIT fuzzy match: '{clean_name}' → '{matched_name}' (score: {similar[0]['similarity_score']})")
                return {
                    "drug_name": matched_name,
                    "original_response": clean_name,
                    "method": "esprit_llava",
                    "confidence": 0.7,
                    "fuzzy_match": True
                }
            
            return {
                "drug_name": clean_name,
                "method": "esprit_llava",
                "confidence": 0.7,
                "raw_response": response_text
            }
        
        return None
        
    except Exception as e:
        print(f"⚠️ ESPRIT API error: {e}")
        return None

def parse_ollama_response(response_text: str) -> dict:
    """Parse Ollama response to extract drug information"""
    import json
    import re
    
    try:
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```json\s*\n(.*?)\n```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            return data
        
        # Try to parse as direct JSON
        data = json.loads(response_text)
        return data
    except:
        # Fallback: extract drug name from text using better pattern matching
        drug_name = None
        
        # Look for common patterns in LLaVA responses
        patterns = [
            r'drug name.*?["\']([A-Za-z]+)["\']',  # "drug name is 'Doliprane'"
            r'brand name.*?["\']([A-Za-z]+)["\']',  # "brand name is 'Doliprane'"
            r'medication.*?["\']([A-Za-z]+)["\']',  # "medication is 'Doliprane'"
            r'called\s+["\']?([A-Z][a-z]+)["\']?',  # "called Doliprane"
            r'is\s+["\']?([A-Z][A-Za-z]+)["\']?',   # "is Doliprane"
            r'^["\']?([A-Z][A-Za-z]+)["\']?',       # "Doliprane" at start
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                drug_name = match.group(1)
                # Clean up common OCR mistakes
                drug_name = drug_name.replace('DOLPROANE', 'DOLIPRANE')
                drug_name = drug_name.replace('DOLIPROAINE', 'DOLIPRANE')
                break
        
        if not drug_name:
            # Try to extract any capitalized word that looks like a drug name
            words = response_text.split()
            for word in words:
                clean_word = re.sub(r'[^A-Za-z]', '', word)
                if len(clean_word) > 4 and clean_word[0].isupper():
                    drug_name = clean_word
                    break
        
        return {
            "drug_name": drug_name,
            "raw_response": response_text,
            "confidence": 0.7 if drug_name else 0.3
        }

def identify_with_easy(image: Image.Image) -> dict:
    """Use EasyOCR to extract text from medication"""
    easy_ocr = get_easy_ocr()
    if not easy_ocr:
        return {"drug_name": None, "method": "easy_unavailable"}
    
    # Convert PIL Image to numpy array
    img_array = np.array(image)
    
    # EasyOCR expects RGB
    if len(img_array.shape) == 2:  # Grayscale
        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    elif img_array.shape[2] == 4:  # RGBA
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
    
    # Run EasyOCR
    result = easy_ocr.readtext(img_array)
    
    if not result:
        return {"drug_name": None, "extracted_text": "", "method": "easy"}
    
    # Extract all text with confidence scores
    all_text = []
    words_with_conf = []
    
    for detection in result:
        bbox, text, confidence = detection
        all_text.append(text)
        
        # Calculate text height from bounding box
        height = int(bbox[2][1] - bbox[0][1])
        
        if len(text.strip()) >= 3 and confidence > 0.4:  # 40% confidence threshold (EasyOCR is more conservative)
            words_with_conf.append((text.strip(), confidence * 100, height))
    
    # Sort by height (size) first, then by confidence
    # Drug names are typically the largest text on packaging
    words_with_conf.sort(key=lambda x: (x[2], x[1]), reverse=True)
    
    # Debug: print top words
    print(f"🔍 EasyOCR top words by size (height):")
    for text, conf, height in words_with_conf[:10]:
        print(f"   '{text}' - height: {height}px, confidence: {conf:.1f}%")
    
    # Extract drug name from high-confidence words
    drug_name = extract_drug_name_from_easy(words_with_conf)
    
    return {
        "drug_name": drug_name,
        "extracted_text": " ".join(all_text),
        "confidence": words_with_conf[0][1] / 100 if words_with_conf else 0,
        "method": "easy"
    }

def extract_drug_name_from_easy(words_with_conf: list) -> str:
    """Extract drug name from EasyOCR results"""
    import re
    
    # Skip common non-drug words (packaging, conditions, manufacturers)
    skip_keywords = [
        'douleur', 'douleurs', 'fièvre', 'crise', 'traitement', 'adulte', 'enfant',
        'rhinite', 'grippe', 'upsa', 'sanofi', 'pfizer', 'gsk', 'merck',
        'comprimé', 'comprimés', 'gélule', 'gélules', 'sachet', 'boîte', 'mg', 'ml', 'cp',
        'pellicule', 'pellicules', 'tabs', 'tablet', 'capsule', 'enrobé',
        'et', 'de', 'du', 'la', 'le', 'les', 'pour', 'avec', 'sans'
    ]
    
    # Known active ingredients that indicate drug names
    active_ingredients = [
        'paracétamol', 'paracetamol', 'ibuprofène', 'ibuprofen',
        'aspirine', 'aspirin', 'amoxicilline', 'oméprazole',
        'metformine', 'diclofénac', 'kétoprofène', 'bromazépam'
    ]
    
    # First pass: Check if any word is a known active ingredient (even with lower confidence)
    for text, conf, height in words_with_conf:
        if conf < 50:  # Still need minimum confidence
            continue
        
        cleaned = text.lower().strip()
        if cleaned in active_ingredients:
            # Found active ingredient - search database for brand names with this ingredient
            from services.drug_db import search_similar_drugs
            results = search_similar_drugs(cleaned, limit=1)
            if results and results[0]["similarity_score"] >= 70:
                print(f"✅ Found drug by active ingredient: '{cleaned}' → '{results[0]['drug_name']}' (conf: {conf:.1f}%)")
                return results[0]['drug_name']
    
    # Check largest words first (sorted by height), with minimum confidence threshold
    for text, conf, height in words_with_conf:
        # Skip if confidence is too low or text is too small
        if conf < 50 or height < 10:
            continue
        
        # Clean the text
        cleaned = text.replace(']', 'l').replace('|', 'l').replace('1', 'l')
        cleaned = re.sub(r'[^A-Za-zÀ-ÿ0-9\s\-]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Skip if it's a keyword
        if cleaned.lower() in skip_keywords:
            continue
        
        # Check if it looks like a drug name
        if 4 <= len(cleaned) <= 25:
            alpha_count = sum(1 for c in cleaned if c.isalpha())
            if alpha_count >= len(cleaned) * 0.7:
                print(f"✅ Found drug name (high confidence): '{cleaned}' (conf: {conf:.1f}%, height: {height}px)")
                return cleaned
    
    # Check remaining words with lower confidence but still reasonable size
    for text, conf, height in words_with_conf:
        if conf < 40 or height < 5:
            continue
        
        cleaned = text.replace(']', 'l').replace('|', 'l').replace('1', 'l')
        cleaned = re.sub(r'[^A-Za-zÀ-ÿ0-9\s\-]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if cleaned.lower() in skip_keywords:
            continue
        
        if 4 <= len(cleaned) <= 25:
            alpha_count = sum(1 for c in cleaned if c.isalpha())
            if alpha_count >= len(cleaned) * 0.7:
                print(f"✅ Found drug name (medium confidence): '{cleaned}' (conf: {conf:.1f}%, height: {height}px)")
                return cleaned
    
    return None

def identify_with_tesseract(image: Image.Image) -> dict:
    """Use Tesseract OCR to extract text from medication with preprocessing"""
    
    # Try methods in order of effectiveness for noisy/blurry camera photos
    # Prioritize deblur and sharpening methods for webcam images
    methods = ["deblur", "sharpen", "denoise", "adaptive", "standard"]
    
    best_result = None
    best_score = 0
    
    for method in methods:
        result = _ocr_with_preprocessing(image, method=method)
        drug_name = result.get("drug_name")
        
        if drug_name:
            # Check against database
            from services.drug_db import get_drug_info, search_similar_drugs
            
            # Exact match = highest priority
            if get_drug_info(drug_name):
                print(f"✅ Found exact match with {method} method: {drug_name}")
                result["confidence"] = calculate_confidence(result)
                result["method"] = f"tesseract_{method}"
                return result
            
            # Fuzzy match - try immediately
            similar = search_similar_drugs(drug_name, limit=1)
            if similar and similar[0]["similarity_score"] >= 60:
                score = similar[0]["similarity_score"]
                matched_name = similar[0]["drug_name"]
                
                # If score is very high (>75), return immediately
                if score >= 75:
                    print(f"✅ Strong fuzzy match with {method}: '{drug_name}' → '{matched_name}' (score: {score})")
                    result["drug_name"] = matched_name
                    result["original_ocr"] = drug_name
                    result["fuzzy_match"] = True
                    result["fuzzy_match_score"] = score
                    result["confidence"] = calculate_confidence(result)
                    result["method"] = f"tesseract_{method}_fuzzy"
                    return result
                
                # Otherwise, keep track of best match
                if score > best_score:
                    best_score = score
                    best_result = result
                    best_result["fuzzy_match_score"] = score
                    best_result["fuzzy_match_name"] = matched_name
                    print(f"🔍 Fuzzy match with {method}: '{drug_name}' → '{matched_name}' (score: {score})")
    
    # Return best fuzzy match if found (score >= 60)
    if best_result and best_score >= 60:
        best_result["drug_name"] = best_result["fuzzy_match_name"]
        best_result["original_ocr"] = best_result.get("drug_name")
        best_result["fuzzy_match"] = True
        best_result["confidence"] = calculate_confidence(best_result)
        best_result["method"] = "tesseract_fuzzy"
        return best_result
    
    # No good match - try all methods and return best text extraction
    results = [_ocr_with_preprocessing(image, method=m) for m in methods]
    best_result = max(results, key=lambda x: len(x.get("extracted_text", "")))
    
    # Calculate confidence score
    confidence = calculate_confidence(best_result)
    best_result["confidence"] = confidence
    best_result["method"] = "tesseract"
    
    return best_result

def _ocr_with_preprocessing(image: Image.Image, method: str) -> dict:
    """Apply specific preprocessing method and run OCR"""
    img_array = np.array(image)
    
    # Always upscale for better OCR (especially important for blurry images)
    # Scale to at least 1600px width for better text recognition
    target_width = 1600
    if image.width < target_width:
        scale = target_width / image.width
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.LANCZOS)
        img_array = np.array(image)
    
    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Check if image is blurry
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    is_blurry = laplacian_var < 200  # Threshold for blur detection
    
    if is_blurry:
        print(f"⚠️ Detected blurry image (variance: {laplacian_var:.1f}), applying deblur...")
        # Apply unsharp mask to reduce blur
        gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
        gray = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)
    
    # Apply preprocessing based on method
    if method == "binary":
        # Simple binary threshold (works well for clear images)
        _, processed = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    elif method == "standard":
        # Increase contrast first
        contrast = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        # Otsu's thresholding
        processed = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    elif method == "adaptive":
        # Increase contrast
        contrast = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        # Adaptive thresholding (best for camera photos with uneven lighting)
        processed = cv2.adaptiveThreshold(
            contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    elif method == "denoise":
        # Denoising + contrast + thresholding
        denoised = cv2.fastNlMeansDenoising(gray)
        contrast = cv2.convertScaleAbs(denoised, alpha=1.5, beta=0)
        processed = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    elif method == "sharpen":
        # Aggressive sharpening for very blurry camera photos
        # First apply unsharp mask
        gaussian = cv2.GaussianBlur(gray, (0, 0), 3.0)
        unsharp = cv2.addWeighted(gray, 2.0, gaussian, -1.0, 0)
        # Then apply sharpening kernel
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(unsharp, -1, kernel)
        # Increase contrast
        contrast = cv2.convertScaleAbs(sharpened, alpha=1.5, beta=0)
        # Adaptive threshold
        processed = cv2.adaptiveThreshold(
            contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
    elif method == "deblur":
        # Specialized deblur method for very blurry images
        # 1. Bilateral filter to reduce noise while preserving edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        # 2. Unsharp mask with strong parameters
        gaussian = cv2.GaussianBlur(bilateral, (0, 0), 3.0)
        unsharp = cv2.addWeighted(bilateral, 2.5, gaussian, -1.5, 0)
        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(unsharp.astype(np.uint8))
        # 4. Morphological gradient to enhance text edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
        gradient = cv2.morphologyEx(enhanced, cv2.MORPH_GRADIENT, kernel)
        # 5. Combine with original
        combined = cv2.addWeighted(enhanced, 0.7, gradient, 0.3, 0)
        # 6. Final threshold
        processed = cv2.adaptiveThreshold(
            combined, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 2
        )
    else:
        processed = gray
    
    # Try multiple PSM modes - different modes work better for different image types
    # PSM 6: Uniform block of text (default)
    # PSM 11: Sparse text (better for product labels)
    # PSM 12: Sparse text with OSD (orientation detection)
    
    best_text = ""
    best_data = None
    
    for psm in [11, 12, 6, 3]:  # Try sparse text modes first for product labels
        try:
            text = pytesseract.image_to_string(
                processed,
                lang='fra+eng',
                config=f'--psm {psm} --oem 3'
            )
            
            # Get detailed data
            data = pytesseract.image_to_data(
                processed,
                lang='fra+eng',
                config=f'--psm {psm} --oem 3',
                output_type=pytesseract.Output.DICT
            )
            
            # Count valid words (confidence > 50)
            valid_words = sum(1 for i, t in enumerate(data['text']) 
                            if t.strip() and int(data['conf'][i]) > 50)
            
            if valid_words > 0 or len(text.strip()) > len(best_text.strip()):
                best_text = text
                best_data = data
                
                # If we found good text, stop trying other modes
                if valid_words >= 2:
                    print(f"✅ PSM {psm} found {valid_words} valid words")
                    break
        except Exception as e:
            continue
    
    text = best_text
    data = best_data if best_data else {}
    
    drug_name = extract_drug_name(text, data)
    
    return {
        "drug_name": drug_name,
        "extracted_text": text.strip(),
        "ocr_data": data,
        "preprocessing": method
    }

def calculate_confidence(result: dict) -> float:
    """Calculate confidence score based on OCR results"""
    text = result.get("extracted_text", "")
    ocr_data = result.get("ocr_data", {})
    
    if not text or len(text) < 3:
        return 0.0
    
    # Base confidence on text length and quality
    confidence = min(len(text) / 50.0, 1.0) * 0.3
    
    # Add confidence from tesseract's own confidence scores
    if ocr_data and "conf" in ocr_data:
        confidences = [float(c) for c in ocr_data["conf"] if str(c) != "-1"]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            confidence += (avg_conf / 100.0) * 0.7
    else:
        confidence += 0.5
    
    return round(min(confidence, 1.0), 2)

def extract_drug_name(text: str, ocr_data: dict = None) -> str:
    """Extract drug name from text, prioritizing larger text (drug names are usually biggest)"""
    import re
    
    # If we have OCR data with font sizes, use that to find the largest text
    if ocr_data and 'text' in ocr_data and 'height' in ocr_data:
        # Build a list of words with their heights
        word_sizes = []
        for i, word in enumerate(ocr_data['text']):
            if word.strip() and len(word.strip()) >= 3:
                height = ocr_data['height'][i]
                conf = int(ocr_data['conf'][i]) if ocr_data['conf'][i] != '-1' else 0
                # Only consider words with reasonable confidence
                # Lower threshold (45) for longer words that might be drug names
                min_conf = 45 if len(word.strip()) >= 6 else 50
                if conf > min_conf and height > 0:
                    word_sizes.append((word.strip(), height, conf))
        
        if word_sizes:
            # Sort by confidence FIRST (prioritize accuracy), then by height
            word_sizes.sort(key=lambda x: (x[2], x[1]), reverse=True)
            
            # Debug: print top 10 words by confidence
            print(f"🔍 Top 10 words by confidence:")
            for word, height, conf in word_sizes[:10]:
                print(f"   '{word}' - confidence: {conf}%, height: {height}px")
            
            # Check high-confidence words first (>80% confidence)
            high_conf_words = [(w, h, c) for w, h, c in word_sizes if c >= 80]
            
            for word, height, conf in high_conf_words:
                # Clean the word - remove special characters but keep letters
                # Common OCR errors: ] → l, | → l, 1 → l
                cleaned = word.replace(']', 'l').replace('|', 'l').replace('1', 'l')
                cleaned = re.sub(r'[^A-Za-zÀ-ÿ0-9\s\-]', '', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
                # Skip if it's a condition keyword
                word_lower = cleaned.lower()
                condition_keywords = ['douleur', 'fièvre', 'crise', 'traitement', 'adulte', 'enfant', 'rhinite', 'grippe']
                if any(kw in word_lower for kw in condition_keywords):
                    continue
                
                # Skip manufacturer names (usually smaller and not the drug name)
                manufacturer_keywords = ['upsa', 'sanofi', 'pfizer', 'gsk', 'merck']
                if word_lower in manufacturer_keywords:
                    continue
                
                # If it's a reasonable length and mostly letters, use it
                if 4 <= len(cleaned) <= 25:
                    alpha_count = sum(1 for c in cleaned if c.isalpha())
                    if alpha_count >= len(cleaned) * 0.7:
                        print(f"✅ Found drug name (high confidence): '{cleaned}' (conf: {conf}%, height: {height}px)")
                        return cleaned
            
            # If no high-confidence match, try medium confidence (60-80%) with larger size
            medium_conf_words = [(w, h, c) for w, h, c in word_sizes if 60 <= c < 80 and h > 20]
            
            for word, height, conf in medium_conf_words:
                # Clean the word with OCR error corrections
                cleaned = word.replace(']', 'l').replace('|', 'l').replace('1', 'l')
                cleaned = re.sub(r'[^A-Za-zÀ-ÿ0-9\s\-]', '', cleaned)
                cleaned = re.sub(r'\s+', ' ', cleaned).strip()
                
                word_lower = cleaned.lower()
                condition_keywords = ['douleur', 'fièvre', 'crise', 'traitement', 'adulte', 'enfant', 'rhinite', 'grippe']
                manufacturer_keywords = ['upsa', 'sanofi', 'pfizer', 'gsk', 'merck']
                
                if any(kw in word_lower for kw in condition_keywords):
                    continue
                if word_lower in manufacturer_keywords:
                    continue
                
                if 4 <= len(cleaned) <= 25:
                    alpha_count = sum(1 for c in cleaned if c.isalpha())
                    if alpha_count >= len(cleaned) * 0.7:
                        print(f"✅ Found drug name (medium confidence): '{cleaned}' (conf: {conf}%, height: {height}px)")
                        return cleaned
    
    # Fallback to text-based extraction
    lines = text.strip().split('\n')
    
    # Words that indicate medical conditions/indications (not drug names)
    condition_keywords = [
        'crise', 'traitement', 'symptom', 'douleur', 'fièvre', 'hémorroïdaire',
        'cardiovasculaire', 'digestif', 'respiratoire', 'allergique',
        'chronique', 'aigu', 'posologie', 'indication', 'contre-indication',
        'mode d\'emploi', 'notice', 'composition', 'excipient', 'adulte',
        'enfant', 'nourrisson', 'bébé'
    ]
    
    # Clean and filter lines
    candidates = []
    for idx, line in enumerate(lines[:15]):  # Only check first 15 lines (drug name is usually at top)
        line = line.strip()
        
        # Skip empty or very short lines
        if len(line) < 3:
            continue
        
        # Skip lines that are just numbers or dosages
        if line.isdigit() or re.match(r'^\d+\s*(mg|ml|g|cp)$', line.lower()):
            continue
        
        line_lower = line.lower()
        
        # Skip lines with condition keywords (only if they contain the full phrase)
        if any(keyword in line_lower for keyword in condition_keywords):
            continue
        
        # Skip lines with too many spaces (likely multiple words/phrases)
        if line.count(' ') > 3:
            continue
        
        # Keep lines with mostly Latin letters (including French accents)
        latin_chars = sum(1 for c in line if c.isalpha() and (ord(c) < 128 or 192 <= ord(c) <= 255))
        total_chars = sum(1 for c in line if c.isalpha())
        
        if total_chars > 0 and latin_chars / total_chars > 0.6:
            # Clean the line - keep French accents
            cleaned = re.sub(r'[^A-Za-zÀ-ÿ0-9\s\-]', '', line)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            if 3 <= len(cleaned) <= 25:  # Drug names are typically 3-25 chars
                # Prioritize lines from the top (drug name usually appears first)
                candidates.append((idx, cleaned))
    
    if not candidates:
        return None
    
    # Prioritize single-word candidates (drug names are usually one word)
    single_word = [(idx, name) for idx, name in candidates if ' ' not in name]
    
    if single_word:
        # Sort by position (earlier is better) and prioritize capitalized
        single_word.sort(key=lambda x: (x[0], not x[1][0].isupper()))
        return single_word[0][1]
    
    # If no single-word candidates, use all candidates
    candidates.sort(key=lambda x: (x[0], not x[1][0].isupper()))
    return candidates[0][1]
