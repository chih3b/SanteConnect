# logic.py
import os
from dotenv import load_dotenv
import base64
import httpx
from openai import OpenAI
import urllib3
import requests

import json

# ⚠️ Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
# Initialise le client pour TokenFactory (LLaVA)
http_client = httpx.Client(verify=False)

# On utilise les variables du fichier .env
LLAVA_API_KEY = os.getenv("LLAVA_API_KEY") 
LLAVA_BASE_URL = os.getenv("LLAVA_BASE_URL") 

client = OpenAI(
api_key=LLAVA_API_KEY, # Utilisation de la nouvelle variable
base_url=LLAVA_BASE_URL, # Utilisation de la nouvelle variable
http_client=http_client
)

def analyser_patient(texte, image_path=None):
    """Analyse spécialisée pour la cohérence image/résumé - VERSION ÉPURÉE"""
    
    prompt_specialise = f"""
[EXPERT MÉDICAL - VÉRIFICATION COHÉRENCE]

DOCUMENT IMAGE : Document médical
RÉSUMÉ FOURNI : 
\"\"\"{texte}\"\"\"

ANALYSE REQUISE :

1. **COMPARAISON** :
   - Données patient correspondent-elles ? (Nom, âge, ID)
   - Résultats principaux identiques ? 
   - Valeurs numériques correctes ?

2. **INCOHÉRENCES** :
   - Données manquantes dans le résumé ?
   - Données manquantes dans l'image ?
   - Interprétations justifiées ?

3. **SCORE FINAL** : X/100

4. **POINTS CLÉS** :
   - ✅ Points corrects
   - ❌ Erreurs détectées
   - 💡 Suggestions

Sois concis et cite les valeurs exactes.
"""

    messages = [
        {
            "role": "system", 
            "content": "Tu es un médecin expert chargé de vérifier la cohérence entre des documents médicaux et leurs résumés. Sois précis et factuel."
        },
        {
            "role": "user", 
            "content": prompt_specialise
        }
    ]

    # Ajouter l'image si fournie
    if image_path:
        try:
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            messages[1]["content"] = [
                {"type": "text", "text": messages[1]["content"]},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
            
        except Exception as e:
            return f"❌ Erreur lecture image: {e}"

    try:
        response = client.chat.completions.create(
            model="hosted_vllm/llava-1.5-7b-hf",
            messages=messages,
            temperature=0.1,  # Plus bas pour plus de précision
            max_tokens=1200   # Un peu plus pour l'analyse détaillée
        )
        result_text = response.choices[0].message.content
    except Exception as e:
        result_text = f"❌ Erreur API : {e}"

    return result_text

# === CONFIGURATION CENTRALE ===

# On récupère les variables du fichier .env
SAMBA_KEY = os.getenv("SAMBANOVA_API_KEY") 
SAMBA_BASE = os.getenv("SAMBANOVA_BASE_URL")

SAMBANOVA_CONFIG = {
 "api_key": SAMBA_KEY, # Variable lue via .env
 "base_url": SAMBA_BASE, # Variable lue via .env
 "model": "Meta-Llama-3.3-70B-Instruct",
"headers": {
# IMPORTANT: On utilise la variable ici aussi !
 "Authorization": f"Bearer {SAMBA_KEY}", 
 "Content-Type": "application/json"
   }
}

# === FONCTION GÉNÉRIQUE SAMBANOVA ===
def appeler_sambanova(prompt, role_system, max_tokens=1000, temperature=0.1):
    """Fonction générique pour appeler SambaNova"""
    try:
        payload = {
            "model": SAMBANOVA_CONFIG["model"],
            "messages": [
                {"role": "system", "content": role_system},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{SAMBANOVA_CONFIG['base_url']}/chat/completions",
            headers=SAMBANOVA_CONFIG["headers"],
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            resultat = response.json()
            return resultat['choices'][0]['message']['content']
        else:
            return f"❌ Erreur API ({response.status_code}): {response.text}"
            
    except Exception as e:
        return f"❌ Erreur: {str(e)}"

# === MODULES OPTIMISÉS ===

def analyser_risque_et_recommandations(analyse_llava, resume_existant):
    """
    COMBINE : Ancien Module 2, 3 et 5 - Version AMÉLIORÉE
    """
    
    prompt = f"""
[SYSTÈME: Médecin Expert - Analyse Factuelle et Prudente]

**PRINCIPE FONDAMENTAL : UTILISE UNIQUEMENT LES DONNÉES FOURNIES**
- Extrait TOUTES les informations médicales du texte ci-dessous
- Ne crée PAS de nouvelles données (pas de tension, pas de leucocytes, etc.)
- Si une information n'est pas dans le texte, ne l'utilise PAS

**TEXTE COMPLET À ANALYSER :**
{analyse_llava[:600]}

{resume_existant[:400]}

**TÂCHE :**
1. Liste toutes les données médicales OBJECTIVES trouvées dans le texte
2. Propose une interprétation BASÉE UNIQUEMENT sur ces données
3. Estime un risque BASÉ sur ce qui est documenté

**FORMAT DE SORTIE (JSON) :**
{{
  "donnees_objectives": ["Liste EXACTE des données médicales trouvées"],
  "diagnostic_principal": "Interprétation BASÉE sur les données listées",
  "explication_diagnostic": "Lien DIRECT entre diagnostic et données",
  "drapeaux_rouges": [
    {{
      "risque": "Risque DÉRIVÉ des données (pas inventé)",
      "urgence": "faible/moyenne/élevée",
      "source_donnees": "Citation exacte du texte"
    }}
  ],
  "score_rehospitalisation": "X%",
  "explication_score": "Calculé uniquement avec les données disponibles",
  "plan_action": {{
    "confirmations": ["Examens pour confirmer les données existantes"],
    "complementaires": ["Examens pour informations manquantes"]
  }}
}}

**EXEMPLE SI HCG TROUVÉ :**
Données objectives: ["HCG: 855 mIU/mL", "Patient: 32 ans"]
Diagnostic: "Grossesse probable nécessitant confirmation"
Risques: "Surveillance grossesse" (source: "HCG élevé")
Score: "10%" (car données limitées)
"""

    try:
        payload = {
            "model": "DeepSeek-R1-Distill-Llama-70B",
            "messages": [
                {
                    "role": "system", 
                    "content": "Tu es un médecin MÉTHODIQUE. D'abord, extrais TOUTES les données du texte. Ensuite, analyse UNIQUEMENT ces données. N'invente RIEN. Réponds en JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.1
        }
        
        response = requests.post(
            f"{SAMBANOVA_CONFIG['base_url']}/chat/completions",
            headers=SAMBANOVA_CONFIG["headers"],
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            resultat = response.json()
            reponse_text = resultat['choices'][0]['message']['content']
            
            # Nettoyer le raisonnement de DeepSeek
            if "<think>" in reponse_text:
            # Supprime COMPLÈTEMENT les balises think
                reponse_text = reponse_text.replace("<think>", "").replace("</think>", "")
                reponse_text = reponse_text.strip()
            
            try:
                import re
                json_match = re.search(r'\{.*\}', reponse_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    
                    # Ajouter une synthèse rapide incluse
                    data["synthese_rapide"] = (
                        f"Patient avec {data.get('diagnostic_principal', 'diagnostic non spécifié')}. "
                        f"Score de réhospitalisation à {data.get('score_rehospitalisation', 'N/A')}. "
                        f"{len(data.get('drapeaux_rouges', []))} drapeau(x) rouge(s) identifié(s)."
                    )
                    return data
                else:
                    return {"erreur": "Format JSON non trouvé", "reponse": reponse_text[:200]}
                    
            except json.JSONDecodeError as e:
                return {"erreur": f"JSON invalide: {str(e)}", "reponse": reponse_text[:200]}
                
        else:
            return {"erreur": f"API: {response.status_code}"}
            
    except Exception as e:
        return {"erreur": f"Exception: {str(e)}"}

def generer_synthese_medecin(analyse_complete_dict):
    if not isinstance(analyse_complete_dict, dict) or "erreur" in analyse_complete_dict:
        return "⚠️ Données d'analyse incomplètes - nécessite une réévaluation manuelle"
    
    prompt = f"""
[SYNTHÈSE MÉDICALE POUR MÉDECIN TRAITANT]

**PATIENT :** Informations disponibles
**DIAGNOSTIC :** {analyse_complete_dict.get('diagnostic_principal', 'À confirmer')}

**SCORE RÉHOSPITALISATION (30j) :** {analyse_complete_dict.get('score_rehospitalisation', 'Non calculé')}
**EXPLICATION :** {analyse_complete_dict.get('explication_score', '')}

**DRAPEAUX ROUGES :**
{chr(10).join([f"- {d.get('risque', '')} ({d.get('urgence', '')})" for d in analyse_complete_dict.get('drapeaux_rouges', [])])}

**TÂCHE :** 
Rédige une synthèse CLINIQUE UTILE pour un médecin. Structure en :

1. **SITUATION ACTUELLE** (2 phrases - ce qu'on sait)
2. **PRINCIPAUX RISQUES** (3 points maximum)
3. **ACTIONS IMMÉDIATES** (2-3 actions concrètes)
4. **SUIVI PROPOSÉ** (plan clair avec délais)
5. **CONSEILS POUR LE PATIENT** (1-2 points)

**TON :** Professionnel, concis mais complet. Langage médical adapté.
**LONGUEUR :** 10-12 phrases maximum.
**PAS DE LISTES À PUCES** - rédige en paragraphes fluides.
"""
    
    return appeler_sambanova(
        prompt,
        "Tu es un médecin senior qui rédige une note de synthèse pour un collègue. Sois précis, pratique et utile pour la prise en charge immédiate.",
        max_tokens=600
    )