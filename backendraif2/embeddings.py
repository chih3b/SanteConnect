"""
Client d'embeddings pour Dr. Raif 2
Utilise sentence-transformers
"""

from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("⚠️ sentence-transformers non installé, utilisation d'embeddings simples")

from config import config


class EmbeddingsClient:
    """Client pour générer des embeddings"""
    
    def __init__(self):
        self.model = None
        self.dimension = config.EMBEDDING_DIMENSION
        
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                print(f"📦 Chargement du modèle d'embeddings: {config.EMBEDDING_MODEL}")
                self.model = SentenceTransformer(config.EMBEDDING_MODEL)
                self.dimension = self.model.get_sentence_embedding_dimension()
                print(f"✅ Modèle d'embeddings chargé (dim={self.dimension})")
            except Exception as e:
                print(f"⚠️ Erreur chargement modèle: {e}")
                self.model = None
    
    def embed(self, text: str) -> np.ndarray:
        """Génère un embedding pour un texte"""
        if self.model:
            return self.model.encode(text, normalize_embeddings=True)
        else:
            # Fallback: embedding simple basé sur hash
            return self._simple_embed(text)
    
    def embed_batch(self, texts: List[str], show_progress: bool = False) -> List[np.ndarray]:
        """Génère des embeddings pour plusieurs textes"""
        if self.model:
            return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=show_progress)
        else:
            return [self._simple_embed(t) for t in texts]
    
    def _simple_embed(self, text: str) -> np.ndarray:
        """Embedding simple de fallback"""
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(self.dimension).astype(np.float32)
    
    def embed_text(self, text: str) -> np.ndarray:
        """Alias pour embed - génère un embedding pour un texte"""
        return self.embed(text)
    
    def prepare_medical_query(self, symptoms: List[str], context: str = "") -> str:
        """Prépare une requête médicale optimisée pour l'embedding"""
        query_parts = []
        
        if symptoms:
            symptoms_text = ", ".join(symptoms)
            query_parts.append(f"Patient présentant les symptômes suivants: {symptoms_text}")
        
        if context:
            query_parts.append(f"Contexte: {context}")
        
        query_parts.append("Recherche de maladies correspondantes avec traitements et niveau d'urgence.")
        
        return " ".join(query_parts)


# Instance globale
embeddings_client = EmbeddingsClient()
