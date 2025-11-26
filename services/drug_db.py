import json
import os

DB_PATH = "data/tunisian_drugs.json"

def load_database():
    """Load drug database"""
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_drug_info(drug_name: str) -> dict:
    """Get drug information from database"""
    if not drug_name:
        return None
    
    db = load_database()
    
    # Normalize drug name for matching
    drug_name_normalized = drug_name.lower().strip()
    
    # Exact match
    for key, value in db.items():
        if key.lower() == drug_name_normalized:
            return value
    
    # Partial match - check if key words are present
    for key, value in db.items():
        key_lower = key.lower()
        # Extract main drug name (before dosage)
        main_name = key_lower.split()[0] if ' ' in key_lower else key_lower
        search_name = drug_name_normalized.split()[0] if ' ' in drug_name_normalized else drug_name_normalized
        
        # Match on main name (at least 4 chars to avoid false positives)
        if len(search_name) >= 4 and (main_name.startswith(search_name) or search_name.startswith(main_name)):
            return value
        
        # Check if any significant word matches
        if len(drug_name_normalized) >= 4 and (drug_name_normalized in key_lower or key_lower in drug_name_normalized):
            return value
    
    return None

def add_drug(drug_name: str, info: dict):
    """Add drug to database"""
    db = load_database()
    db[drug_name] = info
    
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def normalize_text(text: str) -> str:
    """Normalize text by removing accents and special characters"""
    import unicodedata
    # Remove accents
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.lower().strip()

def search_similar_drugs(query: str, limit: int = 5) -> list:
    """Search for similar drugs by name with fuzzy matching"""
    if not query or len(query) < 2:
        return []
    
    db = load_database()
    query_lower = query.lower().strip()
    query_normalized = normalize_text(query)
    results = []
    
    for drug_name, drug_info in db.items():
        drug_name_lower = drug_name.lower()
        drug_name_normalized = normalize_text(drug_name)
        
        # Also check the full name (which includes active ingredient in parentheses)
        full_name = drug_info.get('name', '').lower()
        full_name_normalized = normalize_text(full_name)
        
        # Extract just the drug name (before dosage) - keep "fort" if present
        drug_parts = drug_name_lower.split()
        if len(drug_parts) >= 2 and drug_parts[1] in ['fort', 'forte']:
            drug_base = ' '.join(drug_parts[:2])  # Keep "inflamyl fort"
        else:
            drug_base = drug_parts[0] if drug_parts else drug_name_lower
        
        # Same for query - normalize OCR errors for "fort"
        query_parts = query_lower.split()
        if len(query_parts) >= 2:
            second_word = query_parts[1]
            # Normalize common OCR errors for "fort"
            if second_word in ['fort', 'forte', 'ort', 'frt', '/ort', 'iort']:
                query_base = query_parts[0] + ' fort'  # Normalize to "fort"
            else:
                query_base = ' '.join(query_parts[:2])
        else:
            query_base = query_parts[0] if query_parts else query_lower
        
        # Extract active ingredient from full name (text in parentheses)
        active_ingredient = ''
        if '(' in full_name and ')' in full_name:
            active_ingredient = full_name.split('(')[1].split(')')[0].strip()
        
        # Calculate similarity score
        score = 0
        
        # Check against active ingredient first (for when OCR extracts ingredient instead of brand)
        if active_ingredient and len(query_base) >= 4:
            active_base = active_ingredient.split()[0] if ' ' in active_ingredient else active_ingredient
            # Character-based similarity for active ingredient
            if len(query_base) >= 4 and len(active_base) >= 4:
                matches = sum(1 for i, c in enumerate(query_base) if i < len(active_base) and c == active_base[i])
                similarity = matches / max(len(query_base), len(active_base))
                if similarity > 0.6:  # 60% character match
                    score = int(similarity * 90)  # High score for active ingredient match
        
        # Exact match (including "fort") - check both original and normalized
        if score == 0 and (query_lower == drug_name_lower or query_base == drug_base or 
                          query_normalized == drug_name_normalized or 
                          normalize_text(query_base) == normalize_text(drug_base)):
            score = 100
        # Starts with (check normalized versions too)
        elif score == 0 and (drug_name_lower.startswith(query_lower) or query_lower.startswith(drug_name_lower) or
                            drug_name_normalized.startswith(query_normalized) or query_normalized.startswith(drug_name_normalized)):
            score = 80
        elif score == 0 and (drug_base.startswith(query_base) or query_base.startswith(drug_base) or
                            normalize_text(drug_base).startswith(normalize_text(query_base)) or 
                            normalize_text(query_base).startswith(normalize_text(drug_base))):
            score = 75
        # Contains
        elif score == 0 and (query_lower in drug_name_lower or drug_name_lower in query_lower):
            score = 60
        # Levenshtein-like similarity (character difference)
        else:
            # Simple character-based similarity for OCR errors
            if len(query_base) >= 4 and len(drug_base) >= 4:
                # Count matching characters in order
                matches = sum(1 for i, c in enumerate(query_base) if i < len(drug_base) and c == drug_base[i])
                similarity = matches / max(len(query_base), len(drug_base))
                if similarity > 0.6:  # 60% character match
                    score = int(similarity * 70)
                    
                    # Bonus for matching "fort" variant
                    if 'fort' in drug_base and any(x in query_base for x in ['fort', 'ort', 'frt']):
                        score += 15  # Boost score for fort variants
            
            # Word match
            if score == 0:
                query_words = set(query_lower.split())
                drug_words = set(drug_name_lower.split())
                common_words = query_words & drug_words
                if common_words:
                    score = 40 + (len(common_words) * 10)
                    
                    # Bonus if "fort" is in common words
                    if 'fort' in common_words or ('fort' in drug_words and any(x in query_words for x in ['ort', 'frt'])):
                        score += 20
        
        if score > 0:
            results.append({
                "drug_name": drug_name,
                "info": drug_info,
                "similarity_score": score
            })
    
    # Sort by score and return top results
    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:limit]

def get_database_stats() -> dict:
    """Get statistics about the drug database"""
    db = load_database()
    
    manufacturers = {}
    for drug_info in db.values():
        mfr = drug_info.get("manufacturer", "Unknown")
        manufacturers[mfr] = manufacturers.get(mfr, 0) + 1
    
    return {
        "total_drugs": len(db),
        "manufacturers": manufacturers,
        "drug_names": list(db.keys())
    }
