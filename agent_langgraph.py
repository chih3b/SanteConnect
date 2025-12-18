#!/usr/bin/env python3
"""
Fully Functional Agentic AI System using LangGraph
Production-grade medication identification agent with reasoning
"""

from typing import TypedDict, Annotated, Sequence, Literal, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from PIL import Image
import json
import base64
import io

# Import configuration
try:
    from config import MODEL_NAME, OLLAMA_BASE_URL
except ImportError:
    MODEL_NAME = "qwen2.5:1.5b"
    OLLAMA_BASE_URL = "http://localhost:11434"

# Import our services
from services.vision import identify_medication

# Use production database with vector search
# Use vector database but initialize once globally for speed
try:
    from config import USE_DATABASE
    if USE_DATABASE:
        from database_vector import VectorDatabaseManager
        
        # Initialize ONCE at module load time (not per request!)
        print("🚀 Initializing vector database (one-time setup)...")
        _vector_db = VectorDatabaseManager()
        print("✅ Vector database ready")
        
        # Wrapper functions
        def get_drug_info(drug_name: str):
            return _vector_db.get_medication(drug_name)
        
        def search_similar_drugs(query: str, limit: int = 5):
            return _vector_db.hybrid_search(query, limit)
        
        def get_database_stats():
            from database import get_database_stats as _get_stats
            return _get_stats()
        
        def load_database():
            from database import load_database as _load_db
            return _load_db()
    else:
        from services.drug_db import (
            get_drug_info,
            search_similar_drugs,
            get_database_stats,
            load_database
        )
except ImportError:
    from services.drug_db import (
        get_drug_info,
        search_similar_drugs,
        get_database_stats,
        load_database
    )


# Define tools for the agent
@tool
def identify_medication_tool(image_base64: str) -> dict:
    """
    Identify medication from a base64 encoded image using OCR and vision AI.
    Returns drug name, confidence scores, and database match.
    
    Args:
        image_base64: Base64 encoded image string
    
    Returns:
        Dictionary with identification results
    """
    try:
        # Decode image
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Identify
        result = identify_medication(image)
        
        # Get drug info
        if result.get("drug_name"):
            drug_info = get_drug_info(result["drug_name"])
            if drug_info:
                result["drug_info"] = drug_info
                result["match_confidence"] = "high"
            else:
                similar = search_similar_drugs(result["drug_name"], limit=3)
                if similar:
                    result["similar_drugs"] = [s["drug_name"] for s in similar]
                    result["match_confidence"] = "medium"
                else:
                    result["match_confidence"] = "low"
        
        return result
    except Exception as e:
        return {"error": str(e)}


@tool
def search_medication_tool(query: str, limit: int = 5) -> dict:
    """
    Search for medications by name using fuzzy matching.
    Returns similar drugs with similarity scores.
    
    Args:
        query: Medication name or partial name to search
        limit: Maximum number of results (default: 5)
    
    Returns:
        Dictionary with search results
    """
    results = search_similar_drugs(query, limit)
    return {
        "query": query,
        "results": [
            {
                "name": r["drug_name"],
                "score": r["similarity_score"],
                "dosage": r["info"]["dosage"],
                "usage": r["info"]["usage"][:100]
            }
            for r in results
        ],
        "count": len(results)
    }


# Simple in-memory cache for drug info
_drug_info_cache = {}

@tool
def get_drug_details_tool(drug_name: str) -> dict:
    """
    Get detailed information about a specific medication.
    Includes dosage, usage, side effects, warnings, and instructions.
    
    Args:
        drug_name: Name of the medication
    
    Returns:
        Dictionary with complete drug information
    """
    # Check cache first
    cache_key = drug_name.lower().strip()
    if cache_key in _drug_info_cache:
        print(f"✅ Using cached drug info for: {drug_name}")
        return _drug_info_cache[cache_key]
    
    drug_info = get_drug_info(drug_name)
    
    if not drug_info:
        # Try fuzzy search
        results = search_similar_drugs(drug_name, limit=1)
        if results and results[0]["similarity_score"] >= 60:
            drug_info = results[0]["info"]
            drug_name = results[0]["drug_name"]
    
    result = None
    if drug_info:
        result = {
            "found": True,
            "drug_name": drug_name,
            "details": drug_info
        }
    else:
        result = {
            "found": False,
            "drug_name": drug_name,
            "message": "Medication not found in database"
        }
    
    # Cache the result
    _drug_info_cache[cache_key] = result
    return result


@tool
def check_drug_interactions_tool(drug_list: str) -> dict:
    """
    Check for potential interactions between multiple medications.
    Provides warnings about dangerous combinations.
    
    Args:
        drug_list: Comma-separated list of medication names
    
    Returns:
        Dictionary with interaction warnings
    """
    drugs = [d.strip() for d in drug_list.split(",")]
    
    interactions = []
    warnings = []
    
    drug_names_lower = [d.lower() for d in drugs]
    
    # Anticoagulant + NSAID interaction
    if any("aspirine" in d or "kardégic" in d or "warfarin" in d for d in drug_names_lower):
        if any("advil" in d or "voltarène" in d or "ibuprofène" in d or "diclofénac" in d for d in drug_names_lower):
            interactions.append({
                "severity": "HIGH",
                "drugs": ["Anticoagulants", "NSAIDs"],
                "warning": "DANGER: Risque très élevé de saignement gastro-intestinal",
                "action": "Consulter immédiatement un médecin"
            })
    
    # Benzodiazepines warnings
    if any("lexomil" in d or "xanax" in d or "bromazépam" in d or "alprazolam" in d for d in drug_names_lower):
        warnings.append({
            "type": "alcohol",
            "warning": "ATTENTION: Ne jamais consommer d'alcool avec les benzodiazépines",
            "risk": "Dépression respiratoire potentiellement mortelle"
        })
        
        if any("opioïde" in d or "morphine" in d or "codéine" in d for d in drug_names_lower):
            interactions.append({
                "severity": "HIGH",
                "drugs": ["Benzodiazépines", "Opioïdes"],
                "warning": "DANGER: Risque de dépression respiratoire sévère",
                "action": "Combinaison dangereuse - consulter médecin"
            })
    
    # Metformin + contrast
    if any("metformine" in d or "glucophage" in d for d in drug_names_lower):
        warnings.append({
            "type": "medical_procedure",
            "warning": "Arrêter 48h avant tout examen avec produit de contraste iodé",
            "risk": "Risque d'acidose lactique"
        })
    
    # Paracetamol + alcohol
    if any("paracétamol" in d or "doliprane" in d or "efferalgan" in d for d in drug_names_lower):
        warnings.append({
            "type": "alcohol",
            "warning": "Éviter l'alcool - risque de toxicité hépatique",
            "risk": "Dommages au foie"
        })
    
    return {
        "drugs_checked": drugs,
        "interactions": interactions,
        "warnings": warnings,
        "severity_level": "HIGH" if interactions else "LOW",
        "safe": len(interactions) == 0
    }


@tool
def find_alternatives_tool(drug_name: str) -> dict:
    """
    Find alternative medications with the same active ingredient.
    Useful for finding generic equivalents or different brands.
    
    Args:
        drug_name: Name of the medication (can be partial, e.g., "Doliprane" will find "Doliprane 1000mg")
    
    Returns:
        Dictionary with alternative medications
    """
    # Try exact match first
    drug_info = get_drug_info(drug_name)
    
    # If not found, try fuzzy search
    if not drug_info:
        results = search_similar_drugs(drug_name, limit=1)
        if results and results[0]["similarity_score"] >= 50:  # Lower threshold
            drug_info = results[0]["info"]
            drug_name = results[0]["drug_name"]
            print(f"✅ Found drug via fuzzy search: '{drug_name}'")
    
    if not drug_info:
        return {"found": False, "alternatives": []}
    
    # Extract active ingredient
    active_ingredient = drug_info["name"].split("(")[1].split(")")[0] if "(" in drug_info["name"] else drug_info["name"]
    
    # Find alternatives
    alternatives = []
    db = load_database()
    
    # Normalize drug name for comparison (remove dosage info)
    drug_name_lower = drug_name.lower()
    drug_name_base = drug_name_lower.split()[0] if ' ' in drug_name_lower else drug_name_lower
    
    for key, value in db.items():
        key_lower = key.lower()
        key_base = key_lower.split()[0] if ' ' in key_lower else key_lower
        
        # Skip if it's the same drug (compare base names without dosage)
        if key_base == drug_name_base:
            continue
        
        # Check if it has the same active ingredient
        if active_ingredient.lower() in value["name"].lower():
            alternatives.append({
                "name": key,
                "dosage": value["dosage"],
                "manufacturer": value["manufacturer"],
                "reason": "Même principe actif"
            })
    
    return {
        "original_drug": drug_name,
        "active_ingredient": active_ingredient,
        "alternatives": alternatives,
        "count": len(alternatives)
    }


@tool
def search_by_symptom_tool(symptom: str) -> dict:
    """
    Search for medications that treat a specific symptom or condition.
    Useful for questions like "what medication for fever?" or "medicine for pain?"
    
    Args:
        symptom: The symptom or condition (e.g., "fever", "pain", "headache", "cold")
    
    Returns:
        Dictionary with list of medications that treat this symptom
    """
    symptom_lower = symptom.lower()
    
    # Map symptoms to keywords in usage field
    symptom_keywords = {
        "fever": ["fièvre", "fever", "antipyrétique"],
        "fièvre": ["fièvre", "fever", "antipyrétique"],
        "pain": ["douleur", "pain", "analgésique"],
        "douleur": ["douleur", "pain", "analgésique"],
        "headache": ["douleur", "céphalée", "migraine"],
        "cold": ["fièvre", "douleur", "symptomatique"],
        "rhume": ["fièvre", "douleur", "symptomatique"],
        "inflammation": ["inflammatoire", "inflammation"],
        "heart": ["cardiovasculaire", "cardiaque", "antiagr"],
        "coeur": ["cardiovasculaire", "cardiaque", "antiagr"],
        "stomach": ["digestif", "gastrique", "ulcère"],
        "estomac": ["digestif", "gastrique", "ulcère"],
    }
    
    # Get keywords for this symptom
    keywords = symptom_keywords.get(symptom_lower, [symptom_lower])
    
    # Search database
    db = load_database()
    matching_meds = []
    
    for drug_name, drug_info in db.items():
        usage = drug_info.get("usage", "").lower()
        
        # Check if any keyword matches
        if any(keyword in usage for keyword in keywords):
            matching_meds.append({
                "name": drug_name,
                "usage": drug_info.get("usage"),
                "dosage": drug_info.get("dosage"),
                "manufacturer": drug_info.get("manufacturer")
            })
    
    if not matching_meds:
        return {
            "found": False,
            "symptom": symptom,
            "message": f"Aucun médicament trouvé pour '{symptom}' dans la base de données"
        }
    
    return {
        "found": True,
        "symptom": symptom,
        "medications": matching_meds,
        "count": len(matching_meds)
    }


@tool
def compare_medications_tool(drug1: str, drug2: str) -> dict:
    """
    Compare two medications and determine if they can be substituted.
    Analyzes active ingredients, usages, and provides substitution advice.
    
    Args:
        drug1: First medication name
        drug2: Second medication name
    
    Returns:
        Dictionary with comparison and substitution advice
    """
    # Get info for both drugs
    info1 = get_drug_info(drug1)
    info2 = get_drug_info(drug2)
    
    if not info1:
        similar = search_similar_drugs(drug1, limit=1)
        if similar and similar[0]["similarity_score"] >= 60:
            info1 = similar[0]["info"]
            drug1 = similar[0]["drug_name"]
    
    if not info2:
        similar = search_similar_drugs(drug2, limit=1)
        if similar and similar[0]["similarity_score"] >= 60:
            info2 = similar[0]["info"]
            drug2 = similar[0]["drug_name"]
    
    if not info1 or not info2:
        return {
            "found": False,
            "message": f"Could not find information for both medications"
        }
    
    # Extract active ingredients
    def get_active_ingredient(name):
        if "(" in name and ")" in name:
            return name.split("(")[1].split(")")[0].lower()
        return name.lower()
    
    active1 = get_active_ingredient(info1["name"])
    active2 = get_active_ingredient(info2["name"])
    
    # Compare
    same_active = active1 == active2
    usage1 = info1.get("usage", "").lower()
    usage2 = info2.get("usage", "").lower()
    
    # Determine if substitution is safe
    can_substitute = False
    reason = ""
    warning = ""
    
    if same_active:
        can_substitute = True
        reason = f"Même principe actif ({active1})"
        warning = "Vérifier le dosage avec un pharmacien"
    else:
        # Check if usages overlap
        pain_keywords = ["douleur", "pain", "analgésique"]
        fever_keywords = ["fièvre", "fever", "antipyrétique"]
        antiplatelet_keywords = ["antiagr", "cardiovasculaire", "coagulation"]
        
        usage1_pain = any(k in usage1 for k in pain_keywords)
        usage2_pain = any(k in usage2 for k in pain_keywords)
        usage1_fever = any(k in usage1 for k in fever_keywords)
        usage2_fever = any(k in usage2 for k in fever_keywords)
        usage1_antiplatelet = any(k in usage1 for k in antiplatelet_keywords)
        usage2_antiplatelet = any(k in usage2 for k in antiplatelet_keywords)
        
        if (usage1_pain and usage2_pain) or (usage1_fever and usage2_fever):
            can_substitute = True
            reason = "Usages similaires (douleur/fièvre)"
            warning = "⚠️ Principes actifs différents - consulter un pharmacien"
        elif usage1_antiplatelet or usage2_antiplatelet:
            can_substitute = False
            reason = "Usages DIFFÉRENTS"
            warning = "🚨 DANGER: Ne PAS substituer! Un est un anticoagulant, l'autre non. Risque cardiovasculaire!"
        else:
            can_substitute = False
            reason = "Usages différents"
            warning = "⚠️ Consulter un médecin ou pharmacien avant substitution"
    
    return {
        "found": True,
        "drug1": {
            "name": drug1,
            "active_ingredient": active1,
            "usage": info1.get("usage"),
            "dosage": info1.get("dosage")
        },
        "drug2": {
            "name": drug2,
            "active_ingredient": active2,
            "usage": info2.get("usage"),
            "dosage": info2.get("dosage")
        },
        "same_active_ingredient": same_active,
        "can_substitute": can_substitute,
        "reason": reason,
        "warning": warning,
        "recommendation": "✅ Substitution possible" if can_substitute else "❌ Substitution NON recommandée"
    }


@tool
def check_pregnancy_safety_tool(drug_name: str) -> dict:
    """
    Check if a medication is safe during pregnancy and breastfeeding.
    Provides safety category and recommendations from the database.
    
    Args:
        drug_name: Name of the medication
    
    Returns:
        Dictionary with pregnancy safety information
    """
    drug_info = get_drug_info(drug_name)
    
    if not drug_info:
        results = search_similar_drugs(drug_name, limit=1)
        if results and results[0]["similarity_score"] >= 60:
            drug_info = results[0]["info"]
            drug_name = results[0]["drug_name"]
    
    if not drug_info:
        return {
            "found": False,
            "drug_name": drug_name,
            "message": "Médicament non trouvé dans la base de données"
        }
    
    # Check if pregnancy info exists in database
    if "pregnancy_category" not in drug_info:
        return {
            "found": True,
            "drug_name": drug_name,
            "safety_info": None,
            "message": "⚠️ Informations de sécurité grossesse non disponibles pour ce médicament. CONSULTER IMPÉRATIVEMENT UN MÉDECIN."
        }
    
    # Extract active ingredient for display
    active_ingredient = drug_info["name"].split("(")[1].split(")")[0] if "(" in drug_info["name"] else drug_info["name"]
    
    # Build response from database fields
    return {
        "found": True,
        "drug_name": drug_name,
        "active_ingredient": active_ingredient,
        "category": drug_info.get("pregnancy_category", "UNKNOWN"),
        "pregnancy": drug_info.get("pregnancy_info", "Information non disponible"),
        "breastfeeding": drug_info.get("breastfeeding_info", "Information non disponible"),
        "breastfeeding_safe": drug_info.get("breastfeeding_safe", False),
        "trimester_notes": drug_info.get("pregnancy_trimester_notes", "Consulter un médecin"),
        "recommendation": drug_info.get("pregnancy_recommendation", "Consulter un professionnel de santé"),
        "warning": "⚠️ IMPORTANT: Toujours consulter un médecin ou sage-femme avant de prendre un médicament pendant la grossesse ou l'allaitement."
    }


@tool
def get_database_stats_tool() -> dict:
    """
    Get statistics about the medication database.
    Shows total drugs, manufacturers, and coverage.
    
    Returns:
        Dictionary with database statistics
    """
    return get_database_stats()


@tool
def check_fda_drug_info_tool(drug_name: str) -> dict:
    """
    Get official FDA drug information including warnings and adverse reactions.
    Uses external MCP server to access FDA database.
    
    Args:
        drug_name: Name of the medication
    
    Returns:
        FDA drug information
    """
    try:
        import asyncio
        from services.mcp_client import get_mcp_service
        
        # Create new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            mcp = get_mcp_service()
            result = loop.run_until_complete(mcp.get_fda_drug_info(drug_name))
            return result
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "source": "FDA MCP", "found": False}


@tool
def search_medical_literature_tool(query: str) -> dict:
    """
    Search PubMed for recent medical literature and studies.
    Uses external MCP server to access PubMed database.
    
    Args:
        query: Search query (e.g., "paracetamol pregnancy safety")
    
    Returns:
        Recent medical literature
    """
    try:
        import asyncio
        from services.mcp_client import get_mcp_service
        
        # Create new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            mcp = get_mcp_service()
            result = loop.run_until_complete(mcp.search_pubmed(query, max_results=3))
            return result
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "source": "PubMed MCP", "found": False}


@tool
def check_drug_recalls_tool(drug_name: str) -> dict:
    """
    Check if a medication has any FDA recalls or safety alerts.
    Uses external MCP server to access FDA enforcement database.
    
    Args:
        drug_name: Name of the medication
    
    Returns:
        Recall information
    """
    try:
        import asyncio
        from services.mcp_client import get_mcp_service
        
        # Create new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            mcp = get_mcp_service()
            result = loop.run_until_complete(mcp.check_drug_recalls(drug_name))
            return result
        finally:
            loop.close()
    except Exception as e:
        return {"error": str(e), "source": "FDA Recalls MCP", "found": False}


@tool
def search_web_drug_info_tool(drug_name: str) -> dict:
    """
    FALLBACK: Search medical websites (Drugs.com, WebMD, MedlinePlus, RxList) for drug information.
    Use this ONLY when the drug is NOT found in local database AND NOT found in FDA/MCP sources.
    Scrapes trusted medical websites for drug uses, side effects, warnings, and dosage.
    
    Args:
        drug_name: Name of the medication to search on the web
    
    Returns:
        Dictionary with drug information from web sources
    """
    try:
        from services.web_scraper import search_web_for_drug
        
        result = search_web_for_drug(drug_name)
        
        if result.get('found') and result.get('summary'):
            return {
                "found": True,
                "source": "Web Search",
                "sources_checked": result.get('sources_checked', []),
                "drug_name": drug_name,
                "brand_name": result['summary'].get('brand_name', drug_name),
                "uses": result['summary'].get('uses', 'Not available'),
                "side_effects": result['summary'].get('side_effects', 'See source'),
                "warnings": result['summary'].get('warnings', 'Consult healthcare provider'),
                "dosage": result['summary'].get('dosage', 'Follow prescription'),
                "source_urls": result['summary'].get('source_urls', []),
                "disclaimer": "⚠️ Information from web sources. Always verify with healthcare professional."
            }
        else:
            return {
                "found": False,
                "source": "Web Search",
                "sources_checked": result.get('sources_checked', []),
                "drug_name": drug_name,
                "message": f"Could not find '{drug_name}' on medical websites"
            }
    except Exception as e:
        return {
            "found": False,
            "source": "Web Search",
            "error": str(e),
            "drug_name": drug_name
        }


# Define agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    image_data: Optional[str]


# Create the agent
class MedicationAgent:
    """Fully functional agentic system with LangGraph"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the agent with configurable model
        
        Default model (qwen2.5:1.5b) is optimized for:
        - Fast inference on macOS (5-10s per query)
        - Excellent tool calling support
        - Good reasoning capabilities
        - Low memory usage (~1GB)
        """
        if model_name is None:
            model_name = MODEL_NAME
        
        # Check if MLX should be used
        try:
            from config import USE_MLX, MLX_MODEL
            use_mlx = USE_MLX
        except:
            use_mlx = False
        
        # Initialize LLM based on backend choice
        if use_mlx:
            print("🚀 Using MLX-LM (Apple Silicon optimized)")
            from services.mlx_llm import get_mlx_llm
            self.llm = get_mlx_llm(MLX_MODEL)
            self.backend = "MLX"
        else:
            print("🔧 Using Ollama")
            self.llm = ChatOllama(
                model=model_name,
                temperature=0.1,
                base_url=OLLAMA_BASE_URL,
                num_predict=512,
                num_ctx=4096
            )
            self.backend = "Ollama"
        
        self.model_name = model_name
        
        # Define tools
        self.tools = [
            # Local database tools
            identify_medication_tool,
            search_medication_tool,
            search_by_symptom_tool,
            get_drug_details_tool,
            check_drug_interactions_tool,
            find_alternatives_tool,
            compare_medications_tool,
            check_pregnancy_safety_tool,
            get_database_stats_tool
        ]
        
        # Add MCP tools if enabled
        try:
            from config import USE_MCP
            if USE_MCP:
                self.tools.extend([
                    check_fda_drug_info_tool,
                    search_medical_literature_tool,
                    check_drug_recalls_tool
                ])
                print("✅ MCP tools enabled")
        except:
            # MCP disabled or config not available
            print("⚠️  MCP tools disabled")
            pass
        
        # Add web scraping fallback tool (always enabled)
        self.tools.append(search_web_drug_info_tool)
        print("✅ Web scraping fallback enabled")
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        # Create graph
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Create the agent workflow graph"""
        
        # Define the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def _call_model(self, state: AgentState) -> dict:
        """Call the LLM with current state"""
        messages = state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "end"]:
        """Determine if agent should continue or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If there are tool calls, continue
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"
        
        return "end"
    
    def process_query(self, query: str, image: Optional[Image.Image] = None) -> dict:
        """
        Process a user query with full agentic reasoning
        
        Args:
            query: User's question
            image: Optional medication image
        
        Returns:
            Complete response with reasoning and tool usage
        """
        
        # Prepare initial message
        system_prompt = """Tu es un assistant médical expert avec accès DIRECT à une base de données de 30 médicaments tunisiens.

RÈGLE ABSOLUE: TU DOIS OBLIGATOIREMENT UTILISER LES OUTILS POUR CHAQUE QUESTION.
NE RÉPONDS JAMAIS DIRECTEMENT SANS APPELER UN OUTIL.

IMPORTANT: Les noms de médicaments dans la base incluent le dosage (ex: "Doliprane 1000mg", "Advil 400mg").
Si l'utilisateur demande juste "Doliprane", cherche "Doliprane 1000mg" ou utilise search_medication_tool.

PROCESSUS OBLIGATOIRE:
1. Analyser la question
2. Choisir le(s) outil(s) approprié(s)
3. APPELER L'OUTIL (ne jamais répondre sans outil)
4. Utiliser le résultat de l'outil pour répondre

🔧 OUTILS DISPONIBLES (UTILISE-LES!):

📊 OUTILS LOCAUX (Base de données tunisienne):
- get_drug_details_tool: Obtenir TOUTES les informations d'un médicament (usage, dosage, effets secondaires, précautions, interactions)
- search_by_symptom_tool: Chercher des médicaments par symptôme (ex: "fièvre", "douleur", "rhume") - UTILISE pour "quel médicament pour X?"
- compare_medications_tool: Comparer deux médicaments et vérifier si substitution possible (UTILISE TOUJOURS pour "X au lieu de Y")
- check_pregnancy_safety_tool: Vérifier si un médicament est sûr pendant la grossesse et l'allaitement (UTILISE pour questions grossesse/allaitement)
- search_medication_tool: Rechercher des médicaments par nom
- check_drug_interactions_tool: Vérifier les interactions entre médicaments
- find_alternatives_tool: Trouver des alternatives/génériques
- identify_medication_tool: Identifier un médicament depuis une image (SEULEMENT si image fournie!)
- get_database_stats_tool: Statistiques de la base de données

🌐 OUTILS EXTERNES (MCP - Données internationales):
- check_fda_drug_info_tool: Obtenir informations officielles FDA (warnings, adverse reactions)
- search_medical_literature_tool: Chercher études médicales récentes sur PubMed
- check_drug_recalls_tool: Vérifier si le médicament a des rappels ou alertes de sécurité

🔍 OUTIL WEB (Fallback - Scraping sites médicaux):
- search_web_drug_info_tool: Chercher sur Drugs.com, WebMD, MedlinePlus, RxList
  UTILISE UNIQUEMENT si le médicament n'est PAS trouvé dans la base locale ET PAS trouvé dans FDA!

⚠️ RÈGLES STRICTES - ORDRE DE RECHERCHE:
1. TOUJOURS utiliser get_drug_details_tool quand on te demande des infos sur un médicament
2. Si le médicament N'EST PAS trouvé dans la base locale:
   - ÉTAPE 2: UTILISE check_fda_drug_info_tool pour chercher dans la base FDA internationale
   - Si check_fda_drug_info_tool retourne "found": true, UTILISE CES DONNÉES pour répondre
3. Si le médicament N'EST PAS trouvé dans FDA non plus:
   - ÉTAPE 3: UTILISE search_web_drug_info_tool pour chercher sur les sites médicaux (Drugs.com, WebMD, etc.)
   - Ce tool scrape les sites web médicaux de confiance
   - Si trouvé, utilise ces informations avec le disclaimer approprié
4. NE DIS JAMAIS "non trouvé" si un des tools a retourné des données!
5. UTILISE TOUJOURS les résultats des tools - ne les ignore JAMAIS
6. Pour les questions de COMPARAISON ou SUBSTITUTION (ex: "puis-je utiliser X au lieu de Y?"):
   - UTILISE compare_medications_tool avec les deux médicaments
   - RESPECTE la réponse du tool - ne contredis JAMAIS son verdict
7. Fournis des réponses complètes et détaillées en français
8. Inclus TOUJOURS les avertissements de sécurité

📊 BASE DE DONNÉES: 30 médicaments tunisiens avec informations COMPLÈTES disponibles MAINTENANT.

💡 ASTUCE: Si un médicament n'est pas trouvé directement, utilise search_medication_tool pour trouver des variantes (ex: "Doliprane" → "Doliprane 1000mg").

💡 EXEMPLES DE BONNES RÉPONSES (TOUJOURS AVEC OUTIL):

Question: "Quel médicament pour la fièvre?"
Action: APPELER search_by_symptom_tool(symptom="fièvre")
Réponse: Utiliser le résultat de l'outil

Question: "Info sur doliprane"
Action: APPELER get_drug_details_tool(drug_name="Doliprane 1000mg")
Réponse: Utiliser le résultat de l'outil

Question: "Puis-je utiliser X au lieu de Y?"
Action: APPELER compare_medications_tool(drug1="X", drug2="Y")
Réponse: Utiliser le résultat de l'outil

Question: "Est-ce que Doliprane est sûr pendant la grossesse?"
Action: APPELER check_pregnancy_safety_tool(drug_name="Doliprane")
Réponse: Utiliser le résultat de l'outil

Question: "Tell me about Tylenol" (médicament non-tunisien)
Action 1: APPELER get_drug_details_tool(drug_name="Tylenol") → Pas trouvé
Action 2: APPELER check_fda_drug_info_tool(drug_name="Tylenol") → Trouvé dans FDA!
Réponse: Utiliser les informations FDA

Question: "Info sur Aspégic" (médicament rare)
Action 1: APPELER get_drug_details_tool(drug_name="Aspégic") → Pas trouvé
Action 2: APPELER check_fda_drug_info_tool(drug_name="Aspégic") → Pas trouvé
Action 3: APPELER search_web_drug_info_tool(drug_name="Aspégic") → Trouvé sur Drugs.com!
Réponse: Utiliser les informations web avec disclaimer

⚠️ INTERDIT: Répondre directement sans appeler d'outil!"""

        # Add image data if provided
        image_data = None
        if image:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_data = base64.b64encode(buffered.getvalue()).decode()
            
            messages = [
                HumanMessage(content=f"{system_prompt}\n\nQuestion de l'utilisateur: {query}\n\nNote: L'utilisateur a fourni une image de médicament. Utilise identify_medication_tool avec l'image_base64 fournie dans le contexte.")
            ]
        else:
            messages = [
                HumanMessage(content=f"{system_prompt}\n\nQuestion de l'utilisateur: {query}")
            ]
        
        # Initialize state
        initial_state = {
            "messages": messages,
            "image_data": image_data
        }
        
        # Run the agent with XAI tracing
        from services.explainable_ai import get_xai
        xai = get_xai()
        xai.start_trace(query, "agent_query")
        
        try:
            xai.add_reasoning_step("Query Analysis", f"Processing query: '{query[:50]}...'", 0.9)
            
            final_state = self.graph.invoke(initial_state)
            
            # Extract results
            messages = final_state["messages"]
            final_message = messages[-1]
            
            # Collect tool calls and add to XAI
            tool_calls = []
            for msg in messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls.append({
                            "tool": tc["name"],
                            "args": tc["args"]
                        })
                        # Add tool decision to XAI
                        xai.add_tool_decision(
                            tc["name"], 
                            True, 
                            f"Called with args: {list(tc['args'].keys())}", 
                            0.85,
                            list(tc["args"].values())[:2] if tc["args"] else []
                        )
            
            # Get tool results
            tool_results = []
            for msg in messages:
                if isinstance(msg, ToolMessage):
                    tool_results.append({
                        "tool": msg.name if hasattr(msg, "name") else "unknown",
                        "result": msg.content
                    })
            
            # Add final reasoning step
            if tool_results:
                xai.add_reasoning_step("Response Generation", f"Generated response using {len(tool_calls)} tool(s)", 0.9)
            else:
                xai.add_reasoning_step("Direct Response", "LLM generated response without tools", 0.6)
            
            # Finalize XAI trace
            xai_trace = xai.finalize_trace(success=True)
            
            return {
                "answer": final_message.content,
                "tool_calls": tool_calls,
                "tool_results": tool_results,
                "reasoning": f"Used {len(tool_calls)} tool(s) to answer",
                "confidence": "high" if tool_results else "medium",
                "success": True,
                "xai": xai_trace
            }
        
        except Exception as e:
            xai.add_reasoning_step("Error", f"Processing failed: {str(e)}", 0.1)
            xai_trace = xai.finalize_trace(success=False)
            return {
                "answer": f"Erreur lors du traitement: {str(e)}",
                "error": str(e),
                "success": False,
                "confidence": "low",
                "xai": xai_trace
            }
    
    def stream_response(self, query: str, image: Optional[Image.Image] = None):
        """Stream the agent's response in real-time"""
        
        messages = [HumanMessage(content=query)]
        
        if image:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_data = base64.b64encode(buffered.getvalue()).decode()
        
        initial_state = {
            "messages": messages,
            "image_data": image_data if image else None
        }
        
        for event in self.graph.stream(initial_state):
            yield event


# Global agent instance
_agent_instance = None

def get_agent(model_name: str = None) -> MedicationAgent:
    """
    Get or create agent instance
    
    Args:
        model_name: Ollama model name (default: from config.py)
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = MedicationAgent(model_name)
    return _agent_instance


def ask_langgraph_agent(query: str, image: Optional[Image.Image] = None) -> dict:
    """
    Convenience function to ask the agent
    Uses model from config.py (default: qwen2.5:1.5b for speed)
    
    Args:
        query: User's question
        image: Optional medication image
    """
    agent = get_agent()
    return agent.process_query(query, image)
