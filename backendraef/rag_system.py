"""
RAG System with FAISS for Dr. MediBot
"""

import json
import time
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from config import DATA_DIR, MEDICAL_FILES, EMBEDDING_MODEL, FAISS_INDEX_PATH, TOP_K_RESULTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalRAGSystem:
    """RAG System using FAISS for medical diagnosis"""
    
    def __init__(self, embedding_model_name: str = EMBEDDING_MODEL):
        logger.info(f"Initializing RAG System with model: {embedding_model_name}")
        
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.disease_metadata = []
        self.medical_data = {}
        
        logger.info(f"RAG System initialized (embedding_dim={self.embedding_dim})")
    
    def load_medical_data(self, data_path: Path = DATA_DIR) -> int:
        """Load all medical JSON files"""
        logger.info(f"Loading medical data from: {data_path}")
        
        total_diseases = 0
        
        for category, filename in MEDICAL_FILES.items():
            filepath = data_path / filename
            
            if not filepath.exists():
                logger.warning(f"File not found: {filepath}")
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if 'maladies_neurologiques' in data:
                        diseases = data['maladies_neurologiques']
                    elif 'maladies_poitrine' in data:
                        diseases = data['maladies_poitrine']
                    elif 'maladies_du_dos' in data:
                        diseases = data['maladies_du_dos']
                    elif 'maux_de_tete' in data:
                        diseases = data['maux_de_tete']
                    elif 'patients' in data:
                        diseases = data['patients']
                    else:
                        diseases = data.get('maladies', [])
                    
                    self.medical_data[category] = diseases
                    total_diseases += len(diseases)
                    logger.info(f"  {category}: {len(diseases)} diseases loaded")
                    
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        
        logger.info(f"Total diseases loaded: {total_diseases}")
        return total_diseases
    
    def build_index(self) -> int:
        """Build FAISS index from medical data"""
        logger.info("Building FAISS index...")
        start_time = time.time()
        
        texts_to_embed = []
        
        for category, diseases in self.medical_data.items():
            for disease in diseases:
                disease_name = disease.get('nom') or disease.get('maladie', 'Unknown')
                symptoms = disease.get('symptomes', [])
                description = disease.get('description', '')
                synonymes = disease.get('synonymes', [])
                questions_patients = disease.get('questions_patients_typiques', [])
                mots_cles = disease.get('mots_cles_recherche', [])
                symptomes_detailles = disease.get('symptomes_detailles', [])
                
                patient_synonyms = []
                for symp_detail in symptomes_detailles:
                    patient_synonyms.extend(symp_detail.get('synonymes_patient', []))
                
                text_parts = [disease_name]
                
                if synonymes:
                    text_parts.append("Aussi appelé: " + ", ".join(synonymes))
                
                if description:
                    text_parts.append(description)
                
                if symptoms:
                    text_parts.append("Symptômes: " + ", ".join(symptoms[:10]))
                
                if patient_synonyms:
                    text_parts.append("Langage patient: " + ", ".join(patient_synonyms[:20]))
                
                if questions_patients:
                    text_parts.append("Questions typiques: " + " | ".join(questions_patients[:7]))
                
                if mots_cles:
                    text_parts.append("Mots-clés: " + " ".join(mots_cles[:12]))
                
                combined_text = ". ".join(text_parts)
                texts_to_embed.append(combined_text)
                
                self.disease_metadata.append({
                    'category': category,
                    'disease': disease,
                    'name': disease_name,
                    'symptoms': symptoms,
                    'synonymes': synonymes,
                    'questions_patients_typiques': questions_patients,
                    'symptomes_detailles': symptomes_detailles,
                    'questions_diagnostic': disease.get('questions_diagnostic', []),
                    'arbre_decisionnel': disease.get('arbre_decisionnel', {}),
                    'score_gravite': disease.get('score_gravite', {}),
                    'urgence': disease.get('urgent') or disease.get('urgence'),
                    'niveau_urgence': disease.get('niveau_urgence', ''),
                    'cas_cliniques': disease.get('cas_cliniques_types', []),
                    'drapeaux_rouges': disease.get('drapeaux_rouges', []),
                    'profil_patient_type': disease.get('profil_patient_type', {}),
                    'text': combined_text
                })
        
        if len(texts_to_embed) == 0:
            logger.error("No diseases to index!")
            return 0
        
        logger.info(f"Generating embeddings for {len(texts_to_embed)} diseases...")
        embeddings = self.embedding_model.encode(
            texts_to_embed,
            show_progress_bar=True,
            batch_size=32,
            convert_to_numpy=True
        )
        
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        
        self.index.add(embeddings.astype('float32'))
        
        elapsed = time.time() - start_time
        logger.info(f"FAISS index built: {len(texts_to_embed)} vectors in {elapsed:.2f}s")
        
        return len(texts_to_embed)
    
    def search(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict]:
        """Search for similar diseases"""
        if self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        top_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            idx = int(idx)
            
            if idx < len(self.disease_metadata):
                metadata = self.disease_metadata[idx]
            else:
                continue
            
            similarity_score = max(0, 100 - distance * 10)
            
            results.append({
                'rank': i + 1,
                'name': metadata['name'],
                'category': metadata['category'],
                'similarity_score': round(similarity_score, 2),
                'distance': float(distance),
                'symptoms': metadata['symptoms'],
                'synonymes': metadata.get('synonymes', []),
                'questions_diagnostic': metadata.get('questions_diagnostic', []),
                'arbre_decisionnel': metadata.get('arbre_decisionnel', {}),
                'score_gravite': metadata.get('score_gravite', {}),
                'urgence': metadata.get('urgence'),
                'niveau_urgence': metadata.get('niveau_urgence', ''),
                'cas_cliniques': metadata.get('cas_cliniques', []),
                'drapeaux_rouges': metadata.get('drapeaux_rouges', []),
                'profil_patient': metadata.get('profil_patient_type', {}),
                'disease_full': metadata['disease']
            })
        
        return results
    
    def save_index(self, index_path: Path = FAISS_INDEX_PATH):
        """Save FAISS index and metadata"""
        logger.info(f"Saving FAISS index to {index_path}/...")
        
        index_path.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(index_path / "index.faiss"))
        
        with open(index_path / "metadata.pkl", 'wb') as f:
            pickle.dump(self.disease_metadata, f)
        
        logger.info("Index saved successfully")
    
    def load_index(self, index_path: Path = FAISS_INDEX_PATH) -> bool:
        """Load FAISS index and metadata"""
        logger.info(f"Loading FAISS index from {index_path}/...")
        
        try:
            self.index = faiss.read_index(str(index_path / "index.faiss"))
            
            with open(index_path / "metadata.pkl", 'rb') as f:
                self.disease_metadata = pickle.load(f)
            
            logger.info(f"Index loaded: {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.warning(f"Could not load index: {e}")
            return False


def initialize_rag_system() -> MedicalRAGSystem:
    """Initialize and return the RAG system"""
    rag_system = MedicalRAGSystem()
    
    if FAISS_INDEX_PATH.exists():
        if rag_system.load_index():
            logger.info("Using cached FAISS index")
            return rag_system
    
    logger.info("Building new index...")
    rag_system.load_medical_data()
    rag_system.build_index()
    rag_system.save_index()
    
    return rag_system
