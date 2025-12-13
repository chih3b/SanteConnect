"""
MCP Client Service for SanteConnect
Connects to external medical data sources
"""

import asyncio
from typing import Dict, Any, List, Optional
import httpx
import json


class MCPMedicalService:
    """
    Service to connect to MCP servers for external medical data
    Includes French/European sources for Tunisian drugs
    """
    
    def __init__(self):
        self.servers = {
            # OpenFDA MCP Server (drug info, recalls, adverse events)
            "fda": {
                "url": "https://api.fda.gov/drug",
                "enabled": True
            },
            # PubMed MCP Server (medical literature)
            "pubmed": {
                "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
                "enabled": True
            },
            # Base de données publique des médicaments (French government - FREE!)
            "bdpm": {
                "url": "https://base-donnees-publique.medicaments.gouv.fr",
                "enabled": True,
                "description": "Official French medicine database - FREE"
            },
            # European Medicines Agency (EMA)
            "ema": {
                "url": "https://www.ema.europa.eu",
                "enabled": False  # Limited API
            },
            # Vidal (French drug database)
            "vidal": {
                "url": "https://www.vidal.fr",
                "enabled": False,  # Requires scraping or API key
                "api_key": None
            },
            # DrugBank MCP Server (comprehensive drug data)
            "drugbank": {
                "url": "https://api.drugbank.com",
                "enabled": False,  # Requires API key
                "api_key": None
            }
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # French brand name mappings (common Tunisian drugs)
        self.french_brand_mappings = {
            "gastral": "omeprazole",
            "mopral": "omeprazole",
            "inexium": "esomeprazole",
            "doliprane": "paracetamol",
            "efferalgan": "paracetamol",
            "dafalgan": "paracetamol",
            "advil": "ibuprofen",
            "nurofen": "ibuprofen",
            "voltarene": "diclofenac",
            "kardegic": "aspirin",
            "lexomil": "bromazepam",
            "xanax": "alprazolam",
            "stilnox": "zolpidem",
            "imovane": "zopiclone"
        }
    
    async def get_fda_drug_info(self, drug_name: str) -> Dict[str, Any]:
        """
        Get drug information from FDA database
        Automatically converts French brand names to generic names
        
        Returns:
            - Warnings
            - Adverse reactions
            - Drug interactions
            - Pregnancy category
        """
        if not self.servers["fda"]["enabled"]:
            return {"error": "FDA server disabled"}
        
        # Check if it's a French brand name
        drug_name_lower = drug_name.lower()
        generic_name = self.french_brand_mappings.get(drug_name_lower, drug_name)
        
        if generic_name != drug_name:
            print(f"🇫🇷 Mapped French brand '{drug_name}' → '{generic_name}'")
        
        try:
            # Search FDA drug database with generic name
            url = f"{self.servers['fda']['url']}/label.json"
            
            # Try both brand name and generic name
            search_terms = [generic_name, drug_name]
            
            for search_term in search_terms:
                params = {
                    "search": f"openfda.brand_name:{search_term} OR openfda.generic_name:{search_term}",
                    "limit": 1
                }
                
                response = await self.client.get(url, params=params)
                data = response.json()
                
                if "results" in data and len(data["results"]) > 0:
                    result = data["results"][0]
                    return {
                        "source": "FDA",
                        "brand_name": drug_name,
                        "generic_name": generic_name,
                        "warnings": result.get("warnings", []),
                        "adverse_reactions": result.get("adverse_reactions", []),
                        "drug_interactions": result.get("drug_interactions", []),
                        "pregnancy_category": result.get("pregnancy", []),
                        "found": True
                    }
            
            return {"found": False, "source": "FDA", "searched": [drug_name, generic_name]}
        
        except Exception as e:
            return {"error": str(e), "source": "FDA"}
    
    async def search_pubmed(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search PubMed for medical literature
        
        Returns:
            - Recent studies
            - Clinical trials
            - Safety information
        """
        if not self.servers["pubmed"]["enabled"]:
            return {"error": "PubMed server disabled"}
        
        try:
            # Search PubMed
            search_url = f"{self.servers['pubmed']['url']}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
            
            response = await self.client.get(search_url, params=params)
            data = response.json()
            
            if "esearchresult" in data and "idlist" in data["esearchresult"]:
                ids = data["esearchresult"]["idlist"]
                
                # Fetch article details
                fetch_url = f"{self.servers['pubmed']['url']}/esummary.fcgi"
                params = {
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "json"
                }
                
                response = await self.client.get(fetch_url, params=params)
                articles = response.json()
                
                return {
                    "source": "PubMed",
                    "count": len(ids),
                    "articles": articles.get("result", {}),
                    "found": True
                }
            
            return {"found": False, "source": "PubMed"}
        
        except Exception as e:
            return {"error": str(e), "source": "PubMed"}
    
    async def check_drug_recalls(self, drug_name: str) -> Dict[str, Any]:
        """
        Check if drug has any recalls from FDA
        """
        if not self.servers["fda"]["enabled"]:
            return {"error": "FDA server disabled"}
        
        try:
            url = "https://api.fda.gov/drug/enforcement.json"
            params = {
                "search": f"product_description:{drug_name}",
                "limit": 10
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if "results" in data:
                recalls = []
                for result in data["results"]:
                    recalls.append({
                        "reason": result.get("reason_for_recall"),
                        "status": result.get("status"),
                        "date": result.get("recall_initiation_date"),
                        "classification": result.get("classification")
                    })
                
                return {
                    "source": "FDA Recalls",
                    "has_recalls": len(recalls) > 0,
                    "recalls": recalls,
                    "found": True
                }
            
            return {"found": False, "has_recalls": False, "source": "FDA Recalls"}
        
        except Exception as e:
            return {"error": str(e), "source": "FDA Recalls"}
    
    async def get_adverse_events(self, drug_name: str) -> Dict[str, Any]:
        """
        Get adverse event reports from FDA
        """
        if not self.servers["fda"]["enabled"]:
            return {"error": "FDA server disabled"}
        
        try:
            url = "https://api.fda.gov/drug/event.json"
            params = {
                "search": f"patient.drug.medicinalproduct:{drug_name}",
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": 10
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            if "results" in data:
                reactions = []
                for result in data["results"]:
                    reactions.append({
                        "reaction": result.get("term"),
                        "count": result.get("count")
                    })
                
                return {
                    "source": "FDA Adverse Events",
                    "top_reactions": reactions,
                    "found": True
                }
            
            return {"found": False, "source": "FDA Adverse Events"}
        
        except Exception as e:
            return {"error": str(e), "source": "FDA Adverse Events"}
    
    async def search_french_medicine_db(self, drug_name: str) -> Dict[str, Any]:
        """
        Search French public medicine database (BDPM)
        FREE official database with ALL French drugs including Tunisian brands
        
        Args:
            drug_name: Drug name (French brand or generic)
            
        Returns:
            Drug information from French database
        """
        if not self.servers["bdpm"]["enabled"]:
            return {"error": "BDPM server disabled"}
        
        try:
            # French database is available as public data files
            # For full implementation, would need to download and parse the data files
            # For now, we acknowledge it exists and can be integrated
            
            return {
                "source": "BDPM (French Government)",
                "found": False,
                "message": "French database available but needs full integration",
                "note": f"Drug '{drug_name}' can be found in French public database",
                "database_url": "https://base-donnees-publique.medicaments.gouv.fr",
                "integration_status": "Configured - needs data file parsing"
            }
        
        except Exception as e:
            return {"error": str(e), "source": "BDPM"}
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global instance
_mcp_service = None

def get_mcp_service() -> MCPMedicalService:
    """Get or create MCP service instance"""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPMedicalService()
    return _mcp_service
