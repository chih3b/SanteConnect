"""
Agent de détection des symptômes
Analyse les messages du patient et détecte les symptômes progressivement
"""

from typing import List, Dict, Optional
import re
import json


def robust_json_parse(response: str) -> Dict:
    """Parse JSON de manière robuste"""
    if not response:
        return {}
    
    cleaned = response.strip()
    
    if "```json" in cleaned:
        start = cleaned.find("```json") + 7
        end = cleaned.find("```", start)
        if end > start:
            cleaned = cleaned[start:end]
    elif "```" in cleaned:
        start = cleaned.find("```") + 3
        end = cleaned.find("```", start)
        if end > start:
            cleaned = cleaned[start:end]
    
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace:last_brace + 1]
    
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass
    
    # Extraction manuelle
    result = {}
    symptoms_match = re.search(r'"symptoms_detected"\s*:\s*\[(.*?)\]', cleaned, re.DOTALL)
    if symptoms_match:
        symptoms = re.findall(r'"symptom"\s*:\s*"([^"]*)"', symptoms_match.group(1))
        result["symptoms_detected"] = [{"symptom": s, "confidence": 0.7} for s in symptoms]
    
    return result


class SymptomDetectorAgent:
    """Agent pour détecter les symptômes dans les conversations"""
    
    def __init__(self, llm_client, embeddings_client, rag_retriever):
        self.llm = llm_client
        self.embeddings = embeddings_client
        self.rag = rag_retriever
        
        self.detected_symptoms: List[str] = []
        self.symptom_confidence: Dict[str, float] = {}
        self.symptom_details: Dict[str, Dict] = {}
        
        self._init_symptom_keywords()
        print(f"✅ SymptomDetectorAgent initialisé ({len(self.symptom_keywords)} mots-clés)")
    
    def _init_symptom_keywords(self):
        """Initialise la base de mots-clés de symptômes"""
        self.symptom_keywords = {
            "douleur thoracique": ["douleur thoracique", "douleur poitrine", "mal à la poitrine", "oppression thoracique"],
            "douleur abdominale": ["douleur abdominale", "mal au ventre", "douleur au ventre", "crampe abdominale"],
            "douleur lombaire": ["douleur lombaire", "mal au dos", "douleur bas du dos", "lombalgie"],
            "maux de tête": ["mal de tête", "maux de tête", "céphalée", "migraine", "tête fait mal"],
            "essoufflement": ["essoufflement", "souffle court", "difficulté à respirer", "dyspnée"],
            "toux": ["toux", "tousse", "tousser", "toux sèche", "toux grasse"],
            "palpitations": ["palpitations", "cœur qui bat vite", "tachycardie"],
            "nausées": ["nausée", "nausées", "envie de vomir", "mal au cœur"],
            "vomissement": ["vomissement", "vomissements", "vomir"],
            "diarrhée": ["diarrhée", "selles liquides"],
            "fièvre": ["fièvre", "température", "fébrile", "frissons avec chaleur"],
            "fatigue": ["fatigue", "fatigué", "épuisé", "épuisement", "asthénie"],
            "frissons": ["frissons", "frisson", "grelotte"],
            "sueurs": ["sueur", "sueurs", "transpiration", "sueurs nocturnes"],
            "vertiges": ["vertige", "vertiges", "étourdissement", "tête qui tourne"],
            "confusion": ["confusion", "confus", "désorienté"],
            "engourdissement": ["engourdissement", "engourdi", "fourmillement", "paresthésie"],
            "faiblesse": ["faiblesse", "faible", "sans force"],
            "mal de gorge": ["mal de gorge", "gorge irritée", "angine"],
            "congestion nasale": ["nez bouché", "congestion nasale", "nez qui coule"],
        }
        
        self.intensity_indicators = {
            "légère": ["légère", "faible", "peu", "un peu"],
            "modérée": ["modérée", "moyen", "normal"],
            "sévère": ["sévère", "forte", "intense", "très", "insupportable"]
        }
    
    def analyze_message(self, patient_message: str, conversation_history: List[Dict]) -> Dict:
        """Analyse un message patient et détecte les symptômes"""
        try:
            message_lower = patient_message.lower()
            
            # Détection par mots-clés
            keyword_symptoms = self._detect_symptoms_by_keywords(message_lower)
            
            # Analyse LLM
            llm_analysis = {}
            try:
                llm_analysis = self._analyze_with_llm(patient_message, conversation_history)
            except Exception as e:
                print(f"⚠️ LLM échoué: {e}")
            
            # Consolider
            new_symptoms = self._consolidate_symptoms(keyword_symptoms, llm_analysis)
            symptom_details = self._extract_symptom_details(patient_message, self.detected_symptoms)
            clarification = self._generate_clarification_questions(new_symptoms, symptom_details)
            
            return {
                "symptoms": self.detected_symptoms.copy(),
                "new_symptoms": new_symptoms,
                "symptom_details": symptom_details,
                "requires_clarification": clarification["requires_clarification"],
                "clarification_questions": clarification["questions"]
            }
            
        except Exception as e:
            print(f"❌ Erreur analyse symptômes: {e}")
            return {
                "symptoms": self.detected_symptoms.copy(),
                "new_symptoms": [],
                "symptom_details": {},
                "requires_clarification": True,
                "clarification_questions": ["Pouvez-vous me décrire vos symptômes?"]
            }
    
    def _detect_symptoms_by_keywords(self, message_lower: str) -> Dict[str, float]:
        """Détecte les symptômes par mots-clés"""
        detected = {}
        for symptom_name, keywords in self.symptom_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    detected[symptom_name] = 0.9
                    break
        return detected
    
    def _analyze_with_llm(self, patient_message: str, conversation_history: List[Dict]) -> Dict:
        """Analyse avec le LLM"""
        context_history = ""
        if conversation_history:
            recent = conversation_history[-4:]
            context_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent])
        
        system_prompt = """Tu es un expert médical qui détecte les symptômes.
Extrais TOUS les symptômes du message.
Réponds UNIQUEMENT en JSON:
{"symptoms_detected": [{"symptom": "nom", "confidence": 0.8, "intensity": "modérée"}]}"""

        try:
            response = self.llm.generate([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Historique:\n{context_history}\n\nMessage: {patient_message}"}
            ], max_tokens=800)
            return robust_json_parse(response)
        except:
            return {}
    
    def _consolidate_symptoms(self, keyword_symptoms: Dict[str, float], llm_analysis: Dict) -> List[str]:
        """Fusionne les symptômes détectés"""
        new_symptoms = []
        
        for symptom, confidence in keyword_symptoms.items():
            if symptom not in self.detected_symptoms:
                self.detected_symptoms.append(symptom)
                self.symptom_confidence[symptom] = confidence
                new_symptoms.append(symptom)
        
        for symptom_data in llm_analysis.get("symptoms_detected", []):
            symptom_name = symptom_data.get("symptom", "") if isinstance(symptom_data, dict) else str(symptom_data)
            if symptom_name and symptom_name not in self.detected_symptoms:
                is_new = not any(s.lower() == symptom_name.lower() for s in self.detected_symptoms)
                if is_new:
                    self.detected_symptoms.append(symptom_name)
                    self.symptom_confidence[symptom_name] = 0.6
                    new_symptoms.append(symptom_name)
        
        return new_symptoms
    
    def _extract_symptom_details(self, message: str, symptoms: List[str]) -> Dict[str, Dict]:
        """Extrait les détails des symptômes"""
        message_lower = message.lower()
        details = {}
        
        for symptom in symptoms:
            symptom_details = self.symptom_details.get(symptom, {"intensity": "non_spécifié"}).copy()
            
            for intensity, indicators in self.intensity_indicators.items():
                if any(ind in message_lower for ind in indicators):
                    symptom_details["intensity"] = intensity
                    break
            
            details[symptom] = symptom_details
            self.symptom_details[symptom] = symptom_details
        
        return details
    
    def _generate_clarification_questions(self, new_symptoms: List[str], symptom_details: Dict) -> Dict:
        """Génère des questions de clarification"""
        questions = []
        needs_clarification = len(new_symptoms) == 0
        
        for symptom in new_symptoms:
            details = symptom_details.get(symptom, {})
            if not details.get("duration"):
                questions.append(f"Depuis combien de temps ressentez-vous {symptom}?")
        
        return {
            "requires_clarification": needs_clarification,
            "questions": questions[:3]
        }
    
    def export_symptoms(self) -> Dict:
        """Exporte les symptômes pour le rapport"""
        return {
            "symptoms": self.detected_symptoms.copy(),
            "confidence_scores": self.symptom_confidence.copy(),
            "symptom_details": self.symptom_details.copy(),
            "total_symptoms": len(self.detected_symptoms)
        }
    
    def reset(self):
        """Réinitialise la détection"""
        self.detected_symptoms = []
        self.symptom_confidence = {}
        self.symptom_details = {}
