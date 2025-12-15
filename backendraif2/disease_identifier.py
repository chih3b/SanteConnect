"""
Agent d'identification de maladies
Identifie les maladies possibles basées sur les symptômes détectés
"""

from typing import List, Dict, Optional
import json
import re


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
    
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        cleaned = cleaned[first_brace:last_brace + 1]
    
    try:
        return json.loads(cleaned.strip())
    except:
        pass
    
    # Extraction manuelle
    result = {}
    primary_match = re.search(r'"disease"\s*:\s*"([^"]*)"', cleaned)
    if primary_match:
        result["primary_diagnosis"] = {"disease": primary_match.group(1), "confidence": 0.7}
    
    urgency_match = re.search(r'"urgency_level"\s*:\s*"([^"]*)"', cleaned)
    if urgency_match:
        result["urgency_level"] = urgency_match.group(1)
    
    return result


class DiseaseIdentifierAgent:
    """Agent pour identifier les maladies basées sur les symptômes"""
    
    def __init__(self, llm_client, embeddings_client, rag_retriever, knowledge_loader):
        self.llm = llm_client
        self.embeddings = embeddings_client
        self.rag = rag_retriever
        self.knowledge = knowledge_loader
        
        self.identified_diseases: List[Dict] = []
        self.primary_disease: Optional[Dict] = None
        self.analysis_count = 0
        
        print("✅ DiseaseIdentifierAgent initialisé")
    
    def identify_diseases(self, symptoms: List[str], symptom_details: Optional[Dict] = None) -> Dict:
        """Identifie les maladies possibles basées sur les symptômes"""
        self.analysis_count += 1
        
        if not symptoms:
            return self._empty_result("Aucun symptôme détecté.")
        
        print(f"🔬 Analyse diagnostique #{self.analysis_count} - {len(symptoms)} symptômes")
        
        # Recherche par matching symptômes
        try:
            matching_diseases = self.knowledge.search_by_symptoms(symptoms, threshold=0.15)
        except Exception as e:
            print(f"⚠️ Erreur search_by_symptoms: {e}")
            matching_diseases = []
        
        # Recherche RAG
        rag_context = ""
        try:
            symptoms_text = ", ".join(symptoms)
            query = self.embeddings.prepare_medical_query(symptoms, "diagnostic")
            query_embedding = self.embeddings.embed_text(query)
            rag_context = self.rag.get_differential_context(symptoms, query_embedding, top_k=5)
        except Exception as e:
            print(f"⚠️ Erreur RAG: {e}")
        
        # Analyse LLM
        llm_analysis = self._llm_differential_diagnosis(symptoms, matching_diseases, rag_context)
        
        # Consolidation
        result = self._consolidate_results(symptoms, matching_diseases, llm_analysis)
        result["needs_more_info"] = len(symptoms) < 3 or result.get("confidence", 0) < 0.5
        result["questions_for_confirmation"] = self._generate_confirmation_questions(symptoms, result)
        
        if result["primary_disease"]:
            self.primary_disease = result["primary_disease"]
            self.identified_diseases = result["possible_diseases"]
        
        return result
    
    def _llm_differential_diagnosis(self, symptoms: List[str], matching_diseases: List[Dict], rag_context: str) -> Dict:
        """Diagnostic différentiel avec LLM"""
        system_prompt = """Tu es un médecin expert. Analyse les symptômes et propose un diagnostic.
RÉPONDS UNIQUEMENT EN JSON:
{
    "primary_diagnosis": {"disease": "nom", "confidence": 0.75, "reasoning": "explication", "matching_symptoms": []},
    "differential_diagnoses": [{"disease": "autre", "confidence": 0.5}],
    "urgency_level": "modéré",
    "urgency_reasoning": "explication",
    "recommendation": "conseil"
}
NIVEAUX D'URGENCE: critique, élevé, modéré, faible"""

        diseases_info = ""
        if matching_diseases:
            diseases_info = "\nMALADIES POSSIBLES:\n"
            for d in matching_diseases[:5]:
                diseases_info += f"- {d.get('maladie', 'Inconnu')} (score: {d.get('score', 0):.0%})\n"

        try:
            response = self.llm.generate([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"SYMPTÔMES: {', '.join(symptoms)}\n{diseases_info}\nAnalyse et retourne le diagnostic en JSON."}
            ], max_tokens=1500)
            
            parsed = robust_json_parse(response)
            if not parsed or not parsed.get("primary_diagnosis"):
                return self._fallback_diagnosis(matching_diseases)
            return parsed
        except Exception as e:
            print(f"⚠️ Erreur LLM diagnostic: {e}")
            return self._fallback_diagnosis(matching_diseases)
    
    def _consolidate_results(self, symptoms: List[str], matching_diseases: List[Dict], llm_analysis: Dict) -> Dict:
        """Consolide tous les résultats"""
        primary = llm_analysis.get("primary_diagnosis")
        
        primary_disease = None
        if primary:
            disease_name = primary.get("disease", "")
            disease_info = None
            try:
                disease_info = self.knowledge.get_disease_info(disease_name)
            except:
                pass
            
            # Get data from disease_info (JSON file) if available
            is_emergency = False
            treatment = ""
            all_symptoms = []
            category = ""
            description = ""
            severity = "Modéré"
            when_to_consult = ""
            
            if disease_info:
                # Direct fields from diseases.json
                is_emergency = disease_info.get("is_emergency", False)
                treatment = disease_info.get("treatment", "")
                all_symptoms = disease_info.get("symptoms", [])
                category = disease_info.get("category", "")
                description = disease_info.get("description", "")
                severity = disease_info.get("severity", "Modéré")
                when_to_consult = disease_info.get("when_to_consult", "")
            
            # Also check matching_diseases for fallback
            if not disease_info and matching_diseases:
                for md in matching_diseases:
                    if md.get("maladie", "").lower() == disease_name.lower():
                        all_symptoms = md.get("all_symptoms", [])
                        treatment = md.get("traitement", [""])[0] if md.get("traitement") else ""
                        category = md.get("category", "")
                        description = md.get("description", "")
                        is_emergency = "élevé" in md.get("niveau_urgence", "").lower() or "critique" in md.get("niveau_urgence", "").lower()
                        break
            
            primary_disease = {
                "name": disease_name,
                "confidence": primary.get("confidence", 0.5),
                "reasoning": primary.get("reasoning", ""),
                "matching_symptoms": primary.get("matching_symptoms", []),
                "all_symptoms": all_symptoms,
                "treatments": [treatment] if treatment else [],
                "treatment": treatment,
                "urgency": llm_analysis.get("urgency_level", "Modéré"),
                "severity": severity,
                "category": category,
                "description": description,
                "is_emergency": is_emergency,
                "when_to_consult": when_to_consult
            }
        
        # Diagnostics différentiels
        possible_diseases = []
        for diff_diag in llm_analysis.get("differential_diagnoses", [])[:5]:
            possible_diseases.append({
                "name": diff_diag.get("disease", ""),
                "confidence": diff_diag.get("confidence", 0.3),
                "reasoning": diff_diag.get("reasoning", "")
            })
        
        # Fallback si pas de diagnostic LLM
        if not primary_disease and matching_diseases:
            best_match = matching_diseases[0]
            # Get full disease info from knowledge
            disease_info = None
            try:
                disease_info = self.knowledge.get_disease_info(best_match.get("maladie", ""))
            except:
                pass
            
            is_emergency = False
            treatment = ""
            when_to_consult = ""
            severity = "Modéré"
            
            if disease_info:
                is_emergency = disease_info.get("is_emergency", False)
                treatment = disease_info.get("treatment", "")
                when_to_consult = disease_info.get("when_to_consult", "")
                severity = disease_info.get("severity", "Modéré")
            else:
                treatment = best_match.get("traitement", [""])[0] if best_match.get("traitement") else ""
            
            primary_disease = {
                "name": best_match.get("maladie", "Condition inconnue"),
                "confidence": best_match.get("score", 0.5),
                "reasoning": f"Correspondance de {best_match.get('exact_matches', 0)} symptômes",
                "matching_symptoms": best_match.get("matching_symptoms", []),
                "all_symptoms": best_match.get("all_symptoms", []),
                "treatments": [treatment] if treatment else [],
                "treatment": treatment,
                "urgency": best_match.get("niveau_urgence", "Modéré"),
                "severity": severity,
                "category": best_match.get("category", ""),
                "description": best_match.get("description", ""),
                "is_emergency": is_emergency,
                "when_to_consult": when_to_consult
            }
        
        # Determine if emergency based on primary disease
        is_emergency = primary_disease.get("is_emergency", False) if primary_disease else False
        urgency_level = "CRITIQUE" if is_emergency else llm_analysis.get("urgency_level", "Modéré")
        
        return {
            "primary_disease": primary_disease,
            "possible_diseases": possible_diseases,
            "confidence": primary.get("confidence", 0.0) if primary else 0.0,
            "urgency_level": urgency_level,
            "is_emergency": is_emergency,
            "urgency_reasoning": llm_analysis.get("urgency_reasoning", ""),
            "recommendation": llm_analysis.get("recommendation", "Consultation médicale recommandée")
        }
    
    def _generate_confirmation_questions(self, symptoms: List[str], result: Dict) -> List[str]:
        """Génère des questions pour confirmer le diagnostic"""
        questions = []
        primary = result.get("primary_disease")
        
        if not primary:
            return ["Pouvez-vous décrire plus en détail vos symptômes?"]
        
        disease_symptoms = primary.get("all_symptoms", [])
        mentioned = set(s.lower() for s in symptoms)
        
        for symptom in disease_symptoms[:10]:
            if symptom.lower() not in mentioned:
                questions.append(f"Ressentez-vous également: {symptom}?")
                if len(questions) >= 3:
                    break
        
        return questions[:3]
    
    def _fallback_diagnosis(self, matching_diseases: List[Dict]) -> Dict:
        """Diagnostic de secours"""
        if not matching_diseases:
            return {
                "primary_diagnosis": None,
                "differential_diagnoses": [],
                "urgency_level": "modéré",
                "recommendation": "Consultation médicale recommandée"
            }
        
        best_match = matching_diseases[0]
        return {
            "primary_diagnosis": {
                "disease": best_match.get("maladie", "Condition inconnue"),
                "confidence": min(0.7, best_match.get("score", 0.5)),
                "reasoning": f"Correspondance de {best_match.get('exact_matches', 0)} symptômes",
                "matching_symptoms": best_match.get("matching_symptoms", [])
            },
            "differential_diagnoses": [
                {"disease": d.get("maladie", ""), "confidence": d.get("score", 0.3)}
                for d in matching_diseases[1:4]
            ],
            "urgency_level": best_match.get("niveau_urgence", "modéré"),
            "recommendation": "Consultation médicale recommandée"
        }
    
    def _empty_result(self, message: str) -> Dict:
        """Retourne un résultat vide"""
        return {
            "primary_disease": None,
            "possible_diseases": [],
            "confidence": 0.0,
            "urgency_level": "",
            "recommendation": message,
            "needs_more_info": True,
            "questions_for_confirmation": ["Pouvez-vous décrire vos symptômes?"]
        }
    
    def export_diagnosis(self) -> Dict:
        """Exporte le diagnostic pour le rapport"""
        return {
            "primary_disease": self.primary_disease,
            "possible_diseases": self.identified_diseases,
            "analysis_count": self.analysis_count
        }
    
    def reset(self):
        """Réinitialise l'identification"""
        self.identified_diseases = []
        self.primary_disease = None
        self.analysis_count = 0
