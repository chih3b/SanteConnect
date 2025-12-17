import re

def extract_values(text):
    """Extract medical values from text using regex patterns"""
    tension = re.search(r"(\d{2})/(\d{2})", text)
    gly = re.search(r"([\d\.]+)\s*g/L", text)
    ldl = re.search(r"LDL.*?([\d\.]+)\s*g/L", text, re.IGNORECASE)
    sympt = re.search(r"Sympt[oô]mes?:\s*(.*)", text)

    return {
        "tension": tension.group(0) if tension else "",
        "glycemie": gly.group(1) if gly else "",
        "ldl": ldl.group(1) if ldl else "",
        "symptomes": sympt.group(1) if sympt else ""
    }
