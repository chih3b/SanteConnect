"""
Fast query processor that bypasses the agent for simple queries
This is 10-20x faster than using the full LangGraph agent
"""
import re
from typing import Dict, Any, Optional
from PIL import Image

# Import database functions - use JSON for speed (no vector DB overhead)
from services.drug_db import get_drug_info, search_similar_drugs


def is_simple_query(query: str) -> tuple[bool, Optional[str]]:
    """
    Detect if query is simple enough to bypass the agent
    Returns (is_simple, drug_name)
    """
    query_lower = query.lower().strip()
    
    # Pattern 1: Direct drug info request
    # "doliprane", "info sur doliprane", "c'est quoi doliprane"
    # "side effects of doliprane", "effets secondaires de doliprane"
    patterns = [
        # Basic info requests
        r'^(?:info(?:rmation)?s?\s+(?:sur|pour|de)\s+)?([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        r'^(?:c\'est\s+quoi|qu\'est-ce\s+que)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        r'^([a-zàâäéèêëïîôùûüÿç]+)\s+(?:c\'est\s+quoi|info|usage|dosage)\s*\??$',
        r'^(?:donne|montre|affiche)(?:-moi)?\s+(?:info|infos|informations)\s+(?:sur|de|pour)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        
        # Specific attribute requests (side effects, dosage, usage, etc.)
        r'^(?:side\s+effects?|effets?\s+secondaires?)\s+(?:of|de|du)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        r'^(?:dosage|posologie)\s+(?:of|de|du)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        r'^(?:usage|utilisation)\s+(?:of|de|du)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        r'^(?:warnings?|précautions?|avertissements?)\s+(?:of|de|du|pour|for)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        r'^(?:instructions?)\s+(?:for|pour|de)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        
        # Reverse order: "doliprane side effects"
        r'^([a-zàâäéèêëïîôùûüÿç]+)\s+(?:side\s+effects?|effets?\s+secondaires?)\s*\??$',
        r'^([a-zàâäéèêëïîôùûüÿç]+)\s+(?:dosage|posologie|usage|utilisation|warnings?|précautions?)\s*\??$',
        
        # Questions about specific uses: "does X help with Y?"
        r'^(?:does|est-ce\s+que|is)\s+([a-zàâäéèêëïîôùûüÿç]+)\s+(?:help|aide|good|bon)\s+(?:with|for|pour|contre)\s+',
        r'^([a-zàâäéèêëïîôùûüÿç]+)\s+(?:helps?|aide)\s+(?:with|for|pour|contre)\s+',
        
        # When to use questions: "when do we use X?"
        r'^(?:when|quand)\s+(?:do\s+we|to|do\s+i)?\s*(?:use|utiliser|prendre)\s+([a-zàâäéèêëïîôùûüÿç]+)\s*\??$',
        r'^(?:when|quand)\s+(?:do\s+we|to|do\s+i)?\s*(?:use|utiliser|prendre)\s+([a-zàâäéèêëïîôùûüÿç\s]+)\s*\??$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            drug_name = match.group(1)
            # Capitalize first letter
            drug_name = drug_name.capitalize()
            return True, drug_name
    
    # Pattern 2: Single word that might be a drug name
    words = query_lower.split()
    if len(words) == 1 and len(words[0]) > 3:
        return True, words[0].capitalize()
    
    return False, None


def format_drug_response(drug_name: str, drug_info: Dict[str, Any], query: str = "") -> str:
    """Format drug information into a nice response, optionally context-aware"""
    
    query_lower = query.lower()
    
    # Check if query asks about specific usage
    asking_about_usage = False
    usage_keywords = []
    
    if "help" in query_lower or "good for" in query_lower or "treat" in query_lower:
        asking_about_usage = True
        # Extract what they're asking about
        if "stress" in query_lower:
            usage_keywords.append("stress")
        if "sleep" in query_lower:
            usage_keywords.append("sleep")
        if "depression" in query_lower:
            usage_keywords.append("depression")
        if "cancer" in query_lower:
            usage_keywords.append("cancer")
    
    response = f"**{drug_info['name']}**\n\n"
    
    # If asking about specific usage, check if drug treats it
    if asking_about_usage and usage_keywords:
        usage = drug_info.get('usage', '').lower()
        treats_it = any(keyword in usage for keyword in usage_keywords)
        
        if not treats_it:
            response += f"❌ **Non, {drug_name} n'est PAS utilisé pour {', '.join(usage_keywords)}.**\n\n"
            response += f"✅ **Usage réel:** {drug_info.get('usage')}\n\n"
            response += "💡 Consultez un professionnel de santé pour un traitement approprié.\n\n"
            return response.strip()
    
    # Standard full response
    if drug_info.get('dosage'):
        response += f"💊 **Dosage:** {drug_info['dosage']}\n\n"
    
    if drug_info.get('usage'):
        response += f"🎯 **Usage:** {drug_info['usage']}\n\n"
    
    if drug_info.get('side_effects'):
        response += f"⚠️ **Effets secondaires:** {drug_info['side_effects']}\n\n"
    
    if drug_info.get('warnings'):
        response += f"🚨 **Précautions:** {drug_info['warnings']}\n\n"
    
    if drug_info.get('interactions'):
        response += f"⚡ **Interactions:** {drug_info['interactions']}\n\n"
    
    if drug_info.get('instructions'):
        response += f"📋 **Instructions:** {drug_info['instructions']}\n\n"
    
    if drug_info.get('manufacturer'):
        response += f"🏭 **Fabricant:** {drug_info['manufacturer']}\n"
    
    return response.strip()


def search_by_symptom_fast(symptom: str) -> Optional[Dict[str, Any]]:
    """
    Fast symptom-based search without agent
    Returns medications for common symptoms
    """
    symptom_lower = symptom.lower()
    
    # Symptom to medication mapping (hardcoded for speed)
    symptom_map = {
        "fever": ["Doliprane 1000mg", "Paracétamol 500mg", "Efferalgan 1g", "Advil 400mg"],
        "fièvre": ["Doliprane 1000mg", "Paracétamol 500mg", "Efferalgan 1g", "Advil 400mg"],
        "pain": ["Doliprane 1000mg", "Paracétamol 500mg", "Advil 400mg", "Aspirine 100mg"],
        "douleur": ["Doliprane 1000mg", "Paracétamol 500mg", "Advil 400mg", "Aspirine 100mg"],
        "headache": ["Doliprane 1000mg", "Paracétamol 500mg", "Advil 400mg"],
        "mal de tête": ["Doliprane 1000mg", "Paracétamol 500mg", "Advil 400mg"],
        "cold": ["Doliprane 1000mg", "Paracétamol 500mg", "Efferalgan 1g"],
        "rhume": ["Doliprane 1000mg", "Paracétamol 500mg", "Efferalgan 1g"],
        "inflammation": ["Advil 400mg", "Voltarène 50mg"],
    }
    
    # Find matching medications
    medications = symptom_map.get(symptom_lower)
    if not medications:
        return None
    
    # Get details for each medication
    results = []
    for drug_name in medications:
        drug_info = get_drug_info(drug_name)
        if drug_info:
            results.append({
                "name": drug_name,
                "usage": drug_info.get("usage"),
                "dosage": drug_info.get("dosage")
            })
    
    if not results:
        return None
    
    # Format response
    answer = f"**Médicaments pour {symptom}:**\n\n"
    for med in results:
        answer += f"• **{med['name']}**\n"
        answer += f"  - Usage: {med['usage']}\n"
        answer += f"  - Dosage: {med['dosage']}\n\n"
    
    answer += "⚠️ **Important**: Consultez un pharmacien ou médecin pour un conseil personnalisé."
    
    return {
        "answer": answer,
        "success": True,
        "confidence": "high",
        "method": "fast_path_symptom",
        "tool_calls": [{"tool": "search_by_symptom_tool", "args": {"symptom": symptom}}],
        "reasoning": "Fast symptom search (hardcoded mapping)"
    }


def fast_query(query: str, image: Optional[Image.Image] = None) -> Optional[Dict[str, Any]]:
    """
    Process query using fast path (no agent, no LLM)
    Returns None if query is too complex and needs the agent
    """
    
    # Can't bypass agent if there's an image
    if image:
        return None
    
    # Check for symptom-based queries first
    symptom_patterns = [
        r'(?:what|quel|quels?)\s+(?:medicine|medication|médicament)s?\s+(?:for|pour)\s+([a-z\s]+)',
        r'(?:medicine|medication|médicament)s?\s+(?:for|pour)\s+([a-z\s]+)',
        r'(?:what|quel)\s+(?:to|pour)\s+take\s+for\s+([a-z\s]+)',
    ]
    
    query_lower = query.lower().strip()
    for pattern in symptom_patterns:
        match = re.search(pattern, query_lower)
        if match:
            symptom = match.group(1).strip()
            result = search_by_symptom_fast(symptom)
            if result:
                return result
    
    # Check if it's a simple drug query
    is_simple, drug_name = is_simple_query(query)
    
    if not is_simple or not drug_name:
        return None
    
    print(f"⚡ Fast path: Direct lookup for '{drug_name}'")
    
    # Try exact match first
    drug_info = get_drug_info(drug_name)
    
    if drug_info:
        return {
            "answer": format_drug_response(drug_name, drug_info, query),
            "drug_name": drug_name,
            "success": True,
            "confidence": "high",
            "method": "fast_path",
            "tool_calls": [{"tool": "get_drug_details_tool", "args": {"drug_name": drug_name}}],
            "reasoning": "Direct database lookup (fast path)"
        }
    
    # Try fuzzy search
    similar = search_similar_drugs(drug_name, limit=3)
    
    if similar and similar[0]["similarity_score"] >= 60:
        # Found a good match
        best_match = similar[0]
        drug_name = best_match["drug_name"]
        drug_info = best_match["info"]
        
        response = f"Je pense que vous cherchez **{drug_name}** (similarité: {best_match['similarity_score']}%)\n\n"
        response += format_drug_response(drug_name, drug_info, query)
        
        return {
            "answer": response,
            "drug_name": drug_name,
            "success": True,
            "confidence": "medium",
            "method": "fast_path_fuzzy",
            "tool_calls": [{"tool": "search_medication_tool", "args": {"query": drug_name}}],
            "reasoning": "Fuzzy search match (fast path)"
        }
    
    # No good match found
    if similar:
        suggestions = ", ".join([s["drug_name"] for s in similar[:3]])
        return {
            "answer": f"Je n'ai pas trouvé '{drug_name}' dans la base de données.\n\nVouliez-vous dire: {suggestions}?",
            "success": False,
            "confidence": "low",
            "method": "fast_path_no_match",
            "tool_calls": [{"tool": "search_medication_tool", "args": {"query": drug_name}}],
            "reasoning": "No match found (fast path)"
        }
    
    return None


def should_use_fast_path(query: str) -> bool:
    """Check if we should use fast path"""
    try:
        from config import ENABLE_AGENT_BYPASS
        if not ENABLE_AGENT_BYPASS:
            return False
    except ImportError:
        pass
    
    # Check for simple drug queries
    is_simple, _ = is_simple_query(query)
    if is_simple:
        return True
    
    # Check for symptom queries
    symptom_patterns = [
        r'(?:what|quel|quels?)\s+(?:medicine|medication|médicament)s?\s+(?:for|pour)\s+([a-z\s]+)',
        r'(?:medicine|medication|médicament)s?\s+(?:for|pour)\s+([a-z\s]+)',
    ]
    
    query_lower = query.lower().strip()
    for pattern in symptom_patterns:
        if re.search(pattern, query_lower):
            return True
    
    return False
