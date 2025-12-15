"""
Chargeur de connaissances médicales pour Dr. Raif 2
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from config import config


class KnowledgeLoader:
    """Charge et gère les connaissances médicales"""
    
    def __init__(self):
        self.knowledge_dir = str(config.MEDICAL_KNOWLEDGE_DIR)
        self.diseases: Dict[str, Dict] = {}
        self.symptoms: Dict[str, Dict] = {}
        self.categories: Dict[str, List[str]] = {}
        
    def load_all_knowledge(self) -> Tuple[List[str], List[Dict]]:
        """Charge toutes les connaissances médicales"""
        documents = []
        metadata = []
        
        knowledge_path = Path(self.knowledge_dir)
        if not knowledge_path.exists():
            print(f"⚠️ Dossier {self.knowledge_dir} non trouvé")
            return documents, metadata
        
        # Charger tous les fichiers JSON
        for json_file in knowledge_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Traiter les maladies
                if "diseases" in data:
                    for disease in data["diseases"]:
                        self._process_disease(disease, documents, metadata)
                
                # Traiter les symptômes
                if "symptoms" in data:
                    for symptom in data["symptoms"]:
                        self._process_symptom(symptom, documents, metadata)
                        
            except Exception as e:
                print(f"⚠️ Erreur lecture {json_file}: {e}")
        
        print(f"✅ {len(self.diseases)} maladies et {len(self.symptoms)} symptômes chargés")
        return documents, metadata
    
    def _process_disease(self, disease: Dict, documents: List, metadata: List):
        """Traite une maladie"""
        name = disease.get("name", "")
        if not name:
            return
        
        self.diseases[name.lower()] = disease
        
        # Ajouter à la catégorie
        category = disease.get("category", "Autre")
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)
        
        # Créer le document pour l'indexation
        doc_parts = [
            f"Maladie: {name}",
            f"Catégorie: {category}",
            f"Description: {disease.get('description', '')}",
            f"Symptômes: {', '.join(disease.get('symptoms', []))}",
            f"Traitement: {disease.get('treatment', '')}",
            f"Quand consulter: {disease.get('when_to_consult', '')}"
        ]
        
        documents.append("\n".join(doc_parts))
        metadata.append({
            "type": "disease",
            "name": name,
            "category": category,
            "severity": disease.get("severity", "modérée"),
            "is_emergency": disease.get("is_emergency", False)
        })
    
    def _process_symptom(self, symptom: Dict, documents: List, metadata: List):
        """Traite un symptôme"""
        name = symptom.get("name", "")
        if not name:
            return
        
        self.symptoms[name.lower()] = symptom
        
        # Créer le document
        doc_parts = [
            f"Symptôme: {name}",
            f"Description: {symptom.get('description', '')}",
            f"Causes possibles: {', '.join(symptom.get('possible_causes', []))}",
            f"Drapeaux rouges: {', '.join(symptom.get('red_flags', []))}"
        ]
        
        documents.append("\n".join(doc_parts))
        metadata.append({
            "type": "symptom",
            "name": name,
            "severity": symptom.get("severity", "variable")
        })
    
    def get_disease_info(self, name: str) -> Optional[Dict]:
        """Récupère les infos d'une maladie"""
        return self.diseases.get(name.lower())
    
    def get_all_diseases(self) -> List[Dict]:
        """Retourne toutes les maladies"""
        return list(self.diseases.values())
    
    def get_all_symptoms(self) -> List[str]:
        """Retourne tous les symptômes connus"""
        all_symptoms = set()
        for disease in self.diseases.values():
            all_symptoms.update(disease.get("symptoms", []))
        return list(all_symptoms)
    
    def get_urgent_diseases(self) -> List[Dict]:
        """Retourne les maladies urgentes"""
        return [d for d in self.diseases.values() if d.get("is_emergency")]
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques"""
        return {
            "total_diseases": len(self.diseases),
            "total_symptoms": len(self.get_all_symptoms()),
            "total_treatments": sum(1 for d in self.diseases.values() if d.get("treatment")),
            "categories": {k: len(v) for k, v in self.categories.items()}
        }
    
    def search_by_symptoms(self, symptoms: List[str], threshold: float = 0.2) -> List[Dict]:
        """Recherche des maladies par symptômes avec scoring"""
        if not symptoms:
            return []
        
        results = []
        symptoms_lower = [s.lower().strip() for s in symptoms]
        
        for disease_name, disease in self.diseases.items():
            disease_symptoms = [s.lower().strip() for s in disease.get("symptoms", [])]
            
            if not disease_symptoms:
                continue
            
            # Calcul des correspondances
            matching_symptoms = []
            for patient_symptom in symptoms_lower:
                for disease_symptom in disease_symptoms:
                    if patient_symptom in disease_symptom or disease_symptom in patient_symptom:
                        matching_symptoms.append(disease_symptom)
                        break
            
            # Calcul du score
            if matching_symptoms:
                score = len(matching_symptoms) / max(len(symptoms_lower), len(disease_symptoms))
                
                if score >= threshold or len(matching_symptoms) >= 1:
                    results.append({
                        "maladie": disease.get("name", disease_name),
                        "category": disease.get("category", ""),
                        "score": score,
                        "exact_matches": len(matching_symptoms),
                        "matching_symptoms": matching_symptoms,
                        "all_symptoms": disease_symptoms,
                        "niveau_urgence": "Élevé" if disease.get("is_emergency") else disease.get("severity", "Modéré"),
                        "traitement": [disease.get("treatment", "")] if disease.get("treatment") else [],
                        "description": disease.get("description", "")
                    })
        
        # Tri par score décroissant
        results.sort(key=lambda x: (x['exact_matches'], x['score']), reverse=True)
        return results


# Instance globale
knowledge_loader = KnowledgeLoader()
