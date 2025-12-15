"""
Vector Store FAISS pour Dr. Raif 2
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pickle

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("⚠️ FAISS non installé")

from config import config


class VectorStore:
    """Store vectoriel avec FAISS"""
    
    def __init__(self):
        self.dimension = config.EMBEDDING_DIMENSION
        self.index = None
        self.documents: List[str] = []
        self.metadata: List[Dict] = []
        
        if HAS_FAISS:
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine sim)
            print(f"✅ FAISS index créé (dim={self.dimension})")
    
    @property
    def total_documents(self) -> int:
        return len(self.documents)
    
    def add_documents(self, embeddings: List[np.ndarray], documents: List[str], metadata: List[Dict]):
        """Ajoute des documents à l'index"""
        if not HAS_FAISS or self.index is None:
            return
        
        embeddings_array = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings_array)
        self.index.add(embeddings_array)
        
        self.documents.extend(documents)
        self.metadata.extend(metadata)
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[int, float, str, Dict]]:
        """Recherche les documents les plus similaires"""
        if not HAS_FAISS or self.index is None or self.index.ntotal == 0:
            return []
        
        query = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query)
        
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                results.append((
                    idx,
                    float(score),
                    self.documents[idx],
                    self.metadata[idx]
                ))
        
        return results
    
    def clear(self):
        """Vide l'index"""
        if HAS_FAISS:
            self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []
        self.metadata = []
    
    def save(self, path: str):
        """Sauvegarde l'index"""
        if not HAS_FAISS or self.index is None:
            return
        
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(path / "index.faiss"))
        
        with open(path / "data.pkl", 'wb') as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata
            }, f)
    
    def load(self, path: str) -> bool:
        """Charge l'index"""
        if not HAS_FAISS:
            return False
        
        path = Path(path)
        index_path = path / "index.faiss"
        data_path = path / "data.pkl"
        
        if not index_path.exists() or not data_path.exists():
            return False
        
        try:
            self.index = faiss.read_index(str(index_path))
            
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data["documents"]
                self.metadata = data["metadata"]
            
            return True
        except Exception as e:
            print(f"⚠️ Erreur chargement index: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques"""
        return {
            "total_documents": self.total_documents,
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.dimension
        }


class MedicalRAGRetriever:
    """Retriever RAG spécialisé pour les connaissances médicales"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.embeddings = None
        print("✅ MedicalRAGRetriever initialisé")
    
    def set_embeddings_client(self, embeddings_client):
        """Définit le client d'embeddings"""
        self.embeddings = embeddings_client
    
    def retrieve_for_symptoms(self, query_embedding: np.ndarray, symptoms: List[str] = None, top_k: int = 5) -> str:
        """Récupère le contexte pertinent pour l'analyse de symptômes"""
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        if not results:
            return "Aucune information médicale trouvée."
        
        context_parts = []
        for i, (idx, score, doc, meta) in enumerate(results, 1):
            context_parts.append(f"""
📋 DOCUMENT {i} (Pertinence: {score:.0%})
🏥 Maladie: {meta.get('maladie', 'N/A')}
📂 Catégorie: {meta.get('category', 'N/A')}
⚠️ Urgence: {meta.get('niveau_urgence', 'N/A')}
🔴 Symptômes: {', '.join(meta.get('symptomes', [])[:8])}
💊 Traitements: {', '.join(meta.get('traitement', [])[:5])}
""")
        
        return "\n".join(context_parts)
    
    def get_differential_context(self, symptoms: List[str], query_embedding: np.ndarray, top_k: int = 8) -> str:
        """Récupère le contexte pour le diagnostic différentiel"""
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        if not results:
            return "Aucune information trouvée."
        
        context = "📊 DONNÉES POUR DIAGNOSTIC DIFFÉRENTIEL:\n\n"
        
        for i, (idx, score, doc, meta) in enumerate(results, 1):
            disease_symptoms = meta.get('symptomes', [])
            symptoms_lower = [s.lower() for s in symptoms]
            disease_symptoms_lower = [s.lower() for s in disease_symptoms]
            common = len(set(symptoms_lower) & set(disease_symptoms_lower))
            
            context += f"""
{i}. {meta.get('maladie', 'N/A')} (Score: {score:.0%})
   Catégorie: {meta.get('category', 'N/A')}
   Urgence: {meta.get('niveau_urgence', 'N/A')}
   Symptômes communs: {common}/{len(symptoms)}
   Tous les symptômes: {', '.join(disease_symptoms[:6])}
   Traitements: {', '.join(meta.get('traitement', [])[:4])}
"""
        
        return context


# Instances globales
vector_store = VectorStore()
rag_retriever = MedicalRAGRetriever(vector_store)
