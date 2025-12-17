"""
Medical AI Agent using AutoGen for document analysis
"""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Try to import autogen
try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logging.warning("autogen not available - using fallback")

from ocr_tool import ocr_tool


class MedicalAIAgent:
    """Medical AI Agent that processes images and extracts medical data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("TOKENFACTORY_API_KEY")
        self.ocr_tool = ocr_tool
        
        if AUTOGEN_AVAILABLE and self.api_key:
            self._setup_autogen()
        else:
            self.agent = None
            logging.info("Running in fallback mode (no AutoGen)")
    
    def _setup_autogen(self):
        """Setup AutoGen agent"""
        self.llm_config = {
            "config_list": [{
                "model": "hosted_vllm/Llama-3.1-70B-Instruct",
                "api_key": self.api_key,
                "base_url": "https://tokenfactory.esprit.tn/api",
                "api_type": "openai"
            }],
            "temperature": 0.3,
            "max_tokens": 2000,
        }
        
        self.agent = autogen.AssistantAgent(
            name="MedicalAnalyst",
            llm_config=self.llm_config,
            system_message="""Tu es un expert médical spécialisé dans l'analyse de documents médicaux.
            
Ton rôle:
1. Extraire les informations clés des documents médicaux
2. Identifier les données patient (nom, âge, ID)
3. Repérer les résultats d'analyses et valeurs anormales
4. Structurer les informations de manière claire

Réponds toujours de manière structurée et professionnelle."""
        )
    
    def process_medical_image(self, image_path: str) -> Dict[str, Any]:
        """Process medical image and extract text
        
        Args:
            image_path: Path to medical document image
            
        Returns:
            Dictionary with extracted text and analysis
        """
        logging.info(f"Processing medical document: {image_path}")
        
        # Step 1: OCR extraction
        ocr_result = self.ocr_tool.process_document(image_path)
        
        if not ocr_result.get('success'):
            return {
                'success': False,
                'error': ocr_result.get('error', 'OCR failed'),
                'extracted_text': '',
                'analysis': None
            }
        
        extracted_text = ocr_result.get('text', '')
        
        if len(extracted_text) < 50:
            return {
                'success': False,
                'error': 'Insufficient text extracted from image',
                'extracted_text': extracted_text,
                'analysis': None
            }
        
        # Step 2: AI Analysis (if AutoGen available)
        analysis = None
        if self.agent and AUTOGEN_AVAILABLE:
            analysis = self._analyze_with_agent(extracted_text)
        
        return {
            'success': True,
            'extracted_text': extracted_text,
            'ocr_method': ocr_result.get('method'),
            'text_length': len(extracted_text),
            'analysis': analysis,
            'error': None
        }
    
    def _analyze_with_agent(self, text: str) -> Optional[str]:
        """Use AutoGen agent to analyze extracted text"""
        try:
            query = f"""Analyse ce document médical extrait par OCR:

{text[:3000]}

Identifie et structure:
1. Informations patient (nom, âge, sexe, ID)
2. Type de document (analyse de sang, radiologie, etc.)
3. Résultats principaux avec valeurs
4. Valeurs anormales ou préoccupantes
5. Résumé clinique

Sois précis et factuel."""

            temp_proxy = autogen.UserProxyAgent(
                name="Analyzer",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=1,
                code_execution_config=False,
            )
            
            temp_proxy.initiate_chat(
                self.agent,
                message=query,
                max_turns=1
            )
            
            messages = temp_proxy.chat_messages[self.agent]
            if messages:
                return messages[-1].get('content', '')
            
        except Exception as e:
            logging.error(f"Agent analysis failed: {e}")
        
        return None
    
    def quick_extract(self, image_path: str) -> str:
        """Quick extraction - just OCR, no AI analysis
        
        Args:
            image_path: Path to image
            
        Returns:
            Extracted text
        """
        result = self.ocr_tool.process_document(image_path)
        return result.get('text', '')


# Singleton instance
medical_agent = MedicalAIAgent()
