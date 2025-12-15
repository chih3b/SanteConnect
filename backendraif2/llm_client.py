"""
Client LLM pour Dr. Raif 2
Utilise l'API ESPRIT Token Factory
"""

import httpx
from openai import OpenAI
from config import config


class LLMClient:
    """Client pour interagir avec le LLM"""
    
    def __init__(self):
        self.http_client = httpx.Client(
            verify=False,
            timeout=httpx.Timeout(
                timeout=config.READ_TIMEOUT,
                connect=config.CONNECTION_TIMEOUT,
                read=config.READ_TIMEOUT,
                write=30.0,
                pool=10.0
            )
        )
        
        self.client = OpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_API_BASE,
            http_client=self.http_client,
            max_retries=config.MAX_RETRIES,
            timeout=config.READ_TIMEOUT
        )
        
        print(f"✅ LLM Client initialisé (model={config.LLM_MODEL})")
    
    def generate(self, messages: list, temperature: float = None, max_tokens: int = None) -> str:
        """Génère une réponse du LLM"""
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=temperature or config.LLM_TEMPERATURE,
                max_tokens=max_tokens or config.LLM_MAX_TOKENS,
                top_p=config.LLM_TOP_P
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Erreur LLM: {e}")
            raise
    
    def close(self):
        """Ferme le client HTTP"""
        if self.http_client:
            self.http_client.close()


# Instance globale
llm_client = LLMClient()
