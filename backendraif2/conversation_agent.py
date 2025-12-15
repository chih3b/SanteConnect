"""
Agent de conversation médicale - Questions dynamiques basées sur les symptômes des maladies
"""

from typing import List, Dict, Optional, Set
import re
import traceback


class ConversationAgent:
    """Agent de conversation pour questionner le patient progressivement"""
    
    def __init__(self, llm_client, symptom_detector, disease_identifier, embeddings_client, rag_retriever):
        self.llm = llm_client
        self.symptom_detector = symptom_detector
        self.disease_identifier = disease_identifier
        self.embeddings = embeddings_client
        self.rag = rag_retriever
        
        self.conversation_phase = "initial"
        self.conversation_history: List[Dict] = []
        self.message_count = 0
        self.diagnosis_confirmed = False
        self.last_disease_analysis = None
        
        self.asked_symptoms: Set[str] = set()
        self.confirmed_symptoms: Set[str] = set()
        self.candidate_diseases: List[Dict] = []
        
        self._symptom_keywords: List[str] = []
        self._disease_keywords: List[str] = []
        self._treatment_keywords: List[str] = []
        
        print("✅ ConversationAgent initialisé")
    
    def process_message(self, patient_message: str, session_id: str) -> Dict:
        """Traite un message du patient"""
        try:
            self.message_count += 1
            print(f"🔄 Message #{self.message_count} - Phase: {self.conversation_phase}")
            
            self.conversation_history.append({"role": "user", "content": patient_message})
            
            # 1. Détection des symptômes
            symptom_analysis = self._safe_analyze_symptoms(patient_message)
            self._update_highlight_keywords(symptom_analysis)
            
            for symptom in symptom_analysis.get("new_symptoms", []):
                self.confirmed_symptoms.add(symptom.lower())
            
            # 2. Identification des maladies
            symptoms = symptom_analysis.get("symptoms", [])
            disease_analysis = None
            
            if len(symptoms) >= 2:
                disease_analysis = self._safe_identify_diseases(symptoms, symptom_analysis)
                if disease_analysis:
                    self._update_disease_keywords(disease_analysis)
                    self.last_disease_analysis = disease_analysis
            
            # 3. Mise à jour de la phase
            old_phase = self.conversation_phase
            self._update_phase(symptom_analysis, disease_analysis)
            if old_phase != self.conversation_phase:
                print(f"   📍 Phase: {old_phase} → {self.conversation_phase}")
            
            # 4. Génération de la réponse
            response = self._generate_response(patient_message, symptom_analysis, disease_analysis)
            response_text = response.get("response", "Je vous écoute.")
            
            self.conversation_history.append({"role": "assistant", "content": response_text})
            formatted_response = self._format_response_with_colors(response_text)
            
            # Déterminer urgence
            urgency_level = ""
            is_emergency = False
            if disease_analysis and disease_analysis.get("primary_disease"):
                primary = disease_analysis["primary_disease"]
                is_emergency = primary.get("is_emergency", False)
                urgency_level = "CRITIQUE" if is_emergency else primary.get("severity", "Modéré")
            
            return {
                "response": response_text,
                "formatted_response": formatted_response,
                "detected_symptoms": list(self.confirmed_symptoms),
                "new_symptoms": symptom_analysis.get("new_symptoms", []),
                "identified_disease": disease_analysis.get("primary_disease") if disease_analysis else None,
                "possible_diseases": disease_analysis.get("possible_diseases", []) if disease_analysis else [],
                "urgency_level": urgency_level,
                "is_emergency": is_emergency,
                "phase": self.conversation_phase,
                "should_end": self.conversation_phase == "completed",
                "message_count": self.message_count
            }
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            traceback.print_exc()
            return self._error_response()
    
    def _safe_analyze_symptoms(self, msg: str) -> Dict:
        try:
            return self.symptom_detector.analyze_message(msg, self.conversation_history)
        except:
            return {"symptoms": [], "new_symptoms": []}
    
    def _safe_identify_diseases(self, symptoms: List[str], analysis: Dict) -> Optional[Dict]:
        try:
            return self.disease_identifier.identify_diseases(symptoms, analysis.get("symptom_details", {}))
        except:
            return None
    
    def _update_highlight_keywords(self, analysis: Dict):
        for s in analysis.get("symptoms", []) + analysis.get("new_symptoms", []):
            if s and s.lower() not in [x.lower() for x in self._symptom_keywords]:
                self._symptom_keywords.append(s)
    
    def _update_disease_keywords(self, analysis: Dict):
        if analysis.get("primary_disease"):
            name = analysis["primary_disease"].get("name", "")
            if name:
                self._disease_keywords.append(name)
            # Get treatment - check both 'treatment' (string) and 'treatments' (list)
            treatment = analysis["primary_disease"].get("treatment", "")
            if not treatment and analysis["primary_disease"].get("treatments"):
                treatment = analysis["primary_disease"].get("treatments", [""])[0]
            if treatment:
                self._treatment_keywords.append(treatment[:50])
    
    def _update_phase(self, symptom_analysis: Dict, disease_analysis: Optional[Dict]):
        symptoms_count = len(self.confirmed_symptoms)
        
        if self.conversation_phase == "initial" and symptoms_count > 0:
            self.conversation_phase = "gathering"
        
        elif self.conversation_phase == "gathering":
            # Move to analyzing when we have enough symptoms
            if symptoms_count >= 3 and self.message_count >= 3:
                self.conversation_phase = "analyzing"
        
        elif self.conversation_phase == "analyzing":
            # Move directly to diagnosis when we have a disease identified
            if disease_analysis and disease_analysis.get("primary_disease"):
                self.conversation_phase = "diagnosis"
        
        # Note: diagnosis -> treatment -> completed transitions happen automatically in _generate_response
    
    def _get_next_symptom_question(self, disease_analysis: Optional[Dict]) -> Optional[str]:
        if not disease_analysis:
            return None
        
        candidate_symptoms = set()
        
        # Get symptoms from primary disease
        primary = disease_analysis.get("primary_disease", {})
        if primary:
            for s in primary.get("all_symptoms", primary.get("symptoms", [])):
                candidate_symptoms.add(s.lower())
        
        # Also get symptoms from possible diseases
        for possible in disease_analysis.get("possible_diseases", []):
            for s in possible.get("all_symptoms", possible.get("symptoms", [])):
                candidate_symptoms.add(s.lower())
        
        # Find a symptom we haven't asked about yet
        for symptom in candidate_symptoms:
            symptom_lower = symptom.lower()
            # Check if we already asked or confirmed this symptom
            already_asked = any(symptom_lower in asked.lower() or asked.lower() in symptom_lower for asked in self.asked_symptoms)
            already_confirmed = any(symptom_lower in conf.lower() or conf.lower() in symptom_lower for conf in self.confirmed_symptoms)
            
            if not already_asked and not already_confirmed:
                self.asked_symptoms.add(symptom)
                return symptom
        
        return None
    
    def _generate_response(self, msg: str, symptom_analysis: Dict, disease_analysis: Optional[Dict]) -> Dict:
        if self.conversation_phase == "initial":
            return {"response": "Bonjour! Je suis Dr. Raif. 👋\n\nDécrivez-moi vos symptômes (ce que vous ressentez, où, depuis quand)."}
        
        elif self.conversation_phase == "gathering":
            new_symptoms = symptom_analysis.get("new_symptoms", [])
            response = f"Je note: **{', '.join(new_symptoms)}**.\n\n" if new_symptoms else ""
            
            next_symptom = self._get_next_symptom_question(disease_analysis)
            if next_symptom:
                response += f"Ressentez-vous également **{next_symptom}**?"
            else:
                questions = ["Depuis combien de temps?", "Intensité (légère/modérée/sévère)?", "Autres symptômes?", "Avez-vous de la fièvre?"]
                response += questions[min(self.message_count - 1, len(questions) - 1)]
            return {"response": response}
        
        elif self.conversation_phase == "analyzing":
            # Show symptoms summary, then automatically continue to full diagnosis
            symptoms = list(self.confirmed_symptoms)
            analysis = disease_analysis or self.last_disease_analysis
            
            response = f"📋 **Symptômes identifiés:** {', '.join(symptoms)}\n\n"
            response += "🔬 Analyse en cours...\n\n"
            
            # If we have a diagnosis, show everything in one response
            if analysis and analysis.get("primary_disease"):
                # Add diagnosis
                diagnosis_resp = self._generate_diagnosis_response(analysis)
                response += diagnosis_resp.get("response", "") + "\n\n"
                
                # Add treatment
                treatment_resp = self._generate_treatment_response(analysis)
                response += treatment_resp.get("response", "") + "\n\n"
                
                # Add completion
                completion_resp = self._generate_completion_response(analysis)
                response += completion_resp.get("response", "")
                
                # Set phase to completed
                self.conversation_phase = "completed"
            
            return {"response": response}
        
        elif self.conversation_phase == "diagnosis":
            # Generate full response: diagnosis + treatment + completion
            analysis = disease_analysis or self.last_disease_analysis
            
            diagnosis_resp = self._generate_diagnosis_response(analysis)
            treatment_resp = self._generate_treatment_response(analysis)
            completion_resp = self._generate_completion_response(analysis)
            
            response = diagnosis_resp.get("response", "") + "\n\n"
            response += treatment_resp.get("response", "") + "\n\n"
            response += completion_resp.get("response", "")
            
            # Set phase to completed
            self.conversation_phase = "completed"
            
            return {"response": response}
        
        elif self.conversation_phase == "treatment":
            # Should not reach here normally, but handle it
            analysis = disease_analysis or self.last_disease_analysis
            treatment_resp = self._generate_treatment_response(analysis)
            completion_resp = self._generate_completion_response(analysis)
            
            response = treatment_resp.get("response", "") + "\n\n"
            response += completion_resp.get("response", "")
            
            self.conversation_phase = "completed"
            return {"response": response}
        
        elif self.conversation_phase == "completed":
            return {"response": "La consultation est terminée. Cliquez sur 'Nouvelle consultation' pour recommencer. 💙"}
        
        return {"response": "Je vous écoute."}
    
    def _generate_diagnosis_response(self, analysis: Optional[Dict]) -> Dict:
        if not analysis or not analysis.get("primary_disease"):
            return {"response": "Décrivez d'autres symptômes pour affiner l'analyse."}
        
        p = analysis["primary_disease"]
        is_emergency = p.get("is_emergency", False)
        
        response = "🏥 **DIAGNOSTIC**\n\n"
        if is_emergency:
            response += "🚨 **URGENCE MÉDICALE**\n\n"
        
        response += f"**{p.get('name', 'N/A')}**\n"
        response += f"📂 {p.get('category', '')}\n\n"
        
        if p.get("description"):
            response += f"{p.get('description')}\n\n"
        
        if is_emergency:
            response += "⚠️ **APPELEZ LE 15 (SAMU) IMMÉDIATEMENT**\n\n"
        else:
            response += f"⚠️ Sévérité: **{p.get('severity', 'Modérée')}**\n\n"
        
        if p.get("when_to_consult"):
            response += f"🏥 {p.get('when_to_consult')}\n"
        
        return {"response": response}
    
    def _generate_treatment_response(self, analysis: Optional[Dict]) -> Dict:
        if not analysis or not analysis.get("primary_disease"):
            return {"response": "Consultez un médecin pour le traitement."}
        
        p = analysis["primary_disease"]
        # Get treatment - check both 'treatment' (string) and 'treatments' (list)
        treatment = p.get("treatment", "")
        if not treatment and p.get("treatments"):
            treatment = p.get("treatments", [""])[0]
        
        is_emergency = p.get("is_emergency", False)
        when_to_consult = p.get("when_to_consult", "")
        
        response = "💊 **TRAITEMENT RECOMMANDÉ**\n\n"
        if is_emergency:
            response += "🚨 **URGENCE MÉDICALE - APPELEZ LE 15 (SAMU) IMMÉDIATEMENT**\n\n"
        
        if treatment:
            response += f"**Traitement:** {treatment}\n\n"
        else:
            response += "Consultez un médecin pour le traitement approprié.\n\n"
        
        if when_to_consult:
            response += f"🏥 **Quand consulter:** {when_to_consult}\n\n"
        
        response += "⚠️ Ce conseil ne remplace pas une consultation médicale.\n\n"
        response += "📄 Rapport médical en cours de génération..."
        
        return {"response": response}
    
    def _generate_completion_response(self, analysis: Optional[Dict]) -> Dict:
        response = "✅ **CONSULTATION TERMINÉE**\n\n"
        
        if analysis and analysis.get("primary_disease"):
            p = analysis["primary_disease"]
            response += f"• **Condition:** {p.get('name', 'N/A')}\n"
            response += f"• **Symptômes:** {', '.join(list(self.confirmed_symptoms)[:5])}\n"
            
            if p.get("is_emergency"):
                response += "\n🚨 **APPELEZ LE 15 IMMÉDIATEMENT**\n"
        
        response += "\n📄 Rapport envoyé.\n\nPrenez soin de vous! 💙"
        return {"response": response}
    
    def _format_response_with_colors(self, text: str) -> str:
        formatted = text
        for s in self._symptom_keywords:
            if len(s) >= 3:
                formatted = re.sub(re.escape(s), f'<span style="color:#ef4444;font-weight:600">{s}</span>', formatted, flags=re.IGNORECASE)
        for d in self._disease_keywords:
            if len(d) >= 3:
                formatted = re.sub(re.escape(d), f'<span style="color:#10b981;font-weight:600">{d}</span>', formatted, flags=re.IGNORECASE)
        return formatted
    
    def _error_response(self) -> Dict:
        return {"response": "Décrivez vos symptômes.", "formatted_response": "Décrivez vos symptômes.", "detected_symptoms": [], "new_symptoms": [], "identified_disease": None, "possible_diseases": [], "urgency_level": "", "phase": self.conversation_phase, "should_end": False, "message_count": self.message_count}
    
    def export_conversation(self) -> Dict:
        return {"history": self.conversation_history, "symptoms": self.symptom_detector.export_symptoms(), "confirmed_symptoms": list(self.confirmed_symptoms), "diagnosis": self.disease_identifier.export_diagnosis() if hasattr(self.disease_identifier, 'export_diagnosis') else {}, "phase": self.conversation_phase}
    
    def reset(self):
        self.conversation_phase = "initial"
        self.conversation_history = []
        self.message_count = 0
        self.last_disease_analysis = None
        self.asked_symptoms = set()
        self.confirmed_symptoms = set()
        self._symptom_keywords = []
        self._disease_keywords = []
        self._treatment_keywords = []
        self.symptom_detector.reset()
        self.disease_identifier.reset()
