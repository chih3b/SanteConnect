from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from services.vision import identify_medication
from services.drug_db import get_drug_info
from services.auth import (
    register_user, login_user, verify_token,
    create_conversation, get_conversations, get_conversation_messages,
    add_message, delete_conversation
)
from PIL import Image
import io
from typing import Optional


# Pydantic models for auth
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class MessageRequest(BaseModel):
    content: str
    conversation_id: Optional[int] = None


def get_current_user(authorization: str = Header(None)):
    """Dependency to get current user from token"""
    if not authorization:
        return None
    
    token = authorization.replace("Bearer ", "")
    return verify_token(token)

app = FastAPI(
    title="SanteConnect API",
    description="AI-powered medication identification and information system for Tunisia",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/identify")
async def identify(file: UploadFile = File(...)):
    """Identify medication from uploaded image with confidence scoring"""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Identify medication using vision
        result = identify_medication(image)
        
        # Get drug information with multiple candidates
        if result.get("drug_name"):
            from services.drug_db import search_similar_drugs
            
            # Get exact match
            drug_info = get_drug_info(result["drug_name"])
            result["drug_info"] = drug_info
            
            # Get similar drugs as alternatives
            similar = search_similar_drugs(result["drug_name"])
            if similar and len(similar) > 1:
                result["similar_drugs"] = similar[:3]  # Top 3 matches
            
            # Add match confidence
            if drug_info:
                result["match_confidence"] = "high"
            elif similar:
                result["match_confidence"] = "medium"
            else:
                result["match_confidence"] = "low"
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============== AUTH ENDPOINTS ==============

@app.post("/auth/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    result = register_user(request.email, request.password, request.name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    result = login_user(request.email, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@app.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user}

# ============== CONVERSATION ENDPOINTS ==============

@app.get("/conversations")
async def list_conversations(user: dict = Depends(get_current_user)):
    """Get all conversations for current user"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"conversations": get_conversations(user["id"])}

@app.post("/conversations")
async def new_conversation(user: dict = Depends(get_current_user)):
    """Create a new conversation"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return create_conversation(user["id"])

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int, user: dict = Depends(get_current_user)):
    """Get messages in a conversation"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    messages = get_conversation_messages(conversation_id, user["id"])
    return {"messages": messages}

@app.delete("/conversations/{conversation_id}")
async def remove_conversation(conversation_id: int, user: dict = Depends(get_current_user)):
    """Delete a conversation"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = delete_conversation(conversation_id, user["id"])
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

class SaveMessageRequest(BaseModel):
    role: str
    content: str

@app.post("/conversations/{conversation_id}/messages")
async def save_message(conversation_id: int, request: SaveMessageRequest, user: dict = Depends(get_current_user)):
    """Save a message to conversation (no AI response)"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    add_message(conversation_id, user["id"], request.role, request.content)
    return {"success": True}

@app.post("/conversations/{conversation_id}/message")
async def send_message(conversation_id: int, request: MessageRequest, user: dict = Depends(get_current_user)):
    """Send a message and get AI response"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Save user message
    add_message(conversation_id, user["id"], "user", request.content)
    
    # Get AI response
    from fast_query import fast_query, should_use_fast_path
    from agent_langgraph import ask_langgraph_agent
    
    if should_use_fast_path(request.content):
        result = fast_query(request.content)
        if not result:
            result = ask_langgraph_agent(request.content)
    else:
        result = ask_langgraph_agent(request.content)
    
    # Save AI response
    ai_content = result.get("answer", "Sorry, I couldn't process your request.")
    add_message(conversation_id, user["id"], "assistant", ai_content, {
        "tool_calls": result.get("tool_calls", []),
        "confidence": result.get("confidence")
    })
    
    return result

# ============== DRUG ENDPOINTS ==============

@app.get("/drug/{name}")
async def get_drug(name: str):
    """Get drug information by name"""
    drug_info = get_drug_info(name)
    if not drug_info:
        raise HTTPException(status_code=404, detail="Drug not found")
    return drug_info

@app.get("/")
async def root():
    print("🏠 ROOT ENDPOINT CALLED")
    return {
        "name": "SanteConnect API",
        "version": "2.0.0",
        "status": "running",
        "description": "AI-powered medication identification system"
    }

@app.get("/test")
async def test():
    print("🧪 TEST ENDPOINT CALLED")
    from fast_query import should_use_fast_path, fast_query
    query = "doliprane"
    should_fast = should_use_fast_path(query)
    print(f"   Should use fast path for '{query}': {should_fast}")
    if should_fast:
        result = fast_query(query)
        print(f"   Fast query result: {result is not None}")
        return {"fast_path": True, "result": result}
    return {"fast_path": False}

@app.get("/stats")
async def get_stats():
    """Get database and cache statistics"""
    from services.drug_db import get_database_stats
    from cache_manager import get_cache
    
    db_stats = get_database_stats()
    cache_stats = get_cache().stats()
    
    return {
        "database": db_stats,
        "cache": cache_stats
    }

@app.post("/cache/clear")
async def clear_cache():
    """Clear the response cache"""
    from cache_manager import get_cache
    get_cache().clear()
    return {"message": "Cache cleared successfully"}

@app.get("/search/{query}")
async def search_drugs(query: str, limit: int = 10):
    """Search for drugs by name with tolerant fuzzy matching"""
    from services.drug_db import search_similar_drugs
    
    # Get more results with lower threshold
    all_results = search_similar_drugs(query, limit=limit)
    
    # Filter to show results with at least 30% similarity (very tolerant)
    filtered_results = [r for r in all_results if r['similarity_score'] >= 30]
    
    return {
        "query": query,
        "results": filtered_results,
        "count": len(filtered_results),
        "showing": f"{len(filtered_results)} of {len(all_results)} total matches"
    }

@app.get("/fast/{query}")
async def fast_drug_query(query: str):
    """Ultra-fast drug lookup (no AI, instant response)"""
    from fast_query import fast_query
    result = fast_query(query)
    if result:
        return result
    return {
        "success": False,
        "answer": "Query too complex for fast path. Use /agent/query instead.",
        "method": "fast_path_rejected"
    }

@app.get("/agent/query")
async def agent_query(query: str):
    """
    Ask the intelligent agent a question using Qwen2.5
    Uses fast path for simple queries (10x faster!)
    
    Args:
        query: User's question
    """
    print(f"\n🔍 AGENT QUERY ENDPOINT CALLED: {query}")
    try:
        from cache_manager import get_cache
        from fast_query import fast_query, should_use_fast_path
        from agent_langgraph import ask_langgraph_agent
        
        cache = get_cache()
        
        # Try fast path FIRST for simple queries (instant!)
        should_fast = should_use_fast_path(query)
        print(f"   Should use fast path: {should_fast}")
        
        if should_fast:
            # Check cache for fast path
            cached_response = cache.get(query)
            if cached_response:
                print(f"✅ Cache hit (fast path): {query[:50]}")
                return cached_response
            
            print(f"   Calling fast_query...")
            result = fast_query(query)
            print(f"   Fast query returned: {result is not None}")
            if result:
                print(f"⚡ Fast path used - instant response!")
                cache.set(query, result)
                return result
            else:
                print(f"   Fast query returned None, using agent")
        
        # Check cache for agent responses
        cached_response = cache.get(query)
        if cached_response:
            print(f"✅ Cache hit (agent): {query[:50]}")
            return cached_response
        
        # Use full agent for complex queries
        print(f"🤖 Using full agent for complex query...")
        result = ask_langgraph_agent(query)
        
        # Cache successful responses
        if result.get("success", True):
            cache.set(query, result)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "answer": f"Error: {str(e)}",
            "confidence": "low",
            "error": str(e)
        }

@app.post("/agent/query")
async def agent_query_post(query: str):
    """POST version of agent query"""
    return await agent_query(query)

@app.post("/agent/identify")
async def agent_identify(
    file: UploadFile = File(...), 
    query: str = "Identifie ce médicament et donne-moi toutes les informations importantes"
):
    """
    Identify medication using vision + intelligent agent with Qwen2.5
    
    Args:
        file: Image file of medication
        query: Question about the medication
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Step 1: Use vision to identify the medication
        vision_result = identify_medication(image)
        
        # Step 2: If medication identified, get detailed info using FAST PATH
        if vision_result.get("drug_name"):
            from fast_query import fast_query
            from services.drug_db import get_drug_info, search_similar_drugs
            
            drug_name = vision_result.get("drug_name")
            
            # Try exact match first
            drug_info = get_drug_info(drug_name)
            
            # Get all similar medications (might be multiple variants like "Inflamyl" and "Inflamyl Fort")
            similar = search_similar_drugs(drug_name, limit=5)
            
            # If not found, try fuzzy search
            if not drug_info and similar and similar[0]["similarity_score"] >= 50:
                # Use the best match
                drug_name = similar[0]["drug_name"]
                drug_info = similar[0]["info"]
                print(f"✅ Fuzzy match: '{vision_result.get('drug_name')}' → '{drug_name}' (score: {similar[0]['similarity_score']})")
            
            if drug_info:
                # Found the drug - use fast path for formatting
                fast_result = fast_query(drug_name)
                
                # Build response with alternatives if multiple similar drugs found
                response_base = {
                    "success": True,
                    "drug_name": drug_name,
                    "ocr_text": vision_result.get("extracted_text", ""),
                    "vision_confidence": vision_result.get("confidence", 0),
                }
                
                # Only show similar medications if:
                # 1. OCR confidence is low (<70%) AND there are multiple close matches
                # 2. OR there are multiple matches with same similarity score (genuine ambiguity)
                ocr_confidence = vision_result.get("confidence", 1.0)
                show_alternatives = False
                
                if similar and len(similar) > 1:
                    # Check if there are multiple matches with very similar scores (within 5 points)
                    top_score = similar[0]["similarity_score"]
                    close_matches = [s for s in similar if abs(s["similarity_score"] - top_score) <= 5 and s["similarity_score"] >= 70]
                    
                    # Show alternatives only if OCR confidence is low AND there are close matches
                    if ocr_confidence < 0.7 and len(close_matches) > 1:
                        show_alternatives = True
                        response_base["similar_medications"] = [
                            {
                                "name": s["drug_name"],
                                "dosage": s["info"].get("dosage"),
                                "similarity": s["similarity_score"]
                            }
                            for s in close_matches[:3]
                        ]
                        response_base["note"] = f"⚠️ Image quality is low. Multiple medications match '{vision_result.get('original_ocr', drug_name)}'. Please verify which one you have."
                
                # Add fuzzy match info if applicable
                if vision_result.get("fuzzy_match"):
                    response_base["fuzzy_match_info"] = {
                        "original_ocr": vision_result.get("original_ocr"),
                        "matched_to": drug_name,
                        "confidence": vision_result.get("fuzzy_score", 0)
                    }
                
                if fast_result and fast_result.get("success"):
                    response_base.update({
                        "answer": fast_result.get("answer"),
                        "tool_calls": fast_result.get("tool_calls", []),
                        "reasoning": f"Vision OCR + Fast database lookup",
                        "confidence": fast_result.get("confidence", "high"),
                        "method": "vision + fast_path"
                    })
                    return response_base
                else:
                    from fast_query import format_drug_response
                    answer = format_drug_response(drug_name, drug_info)
                    response_base.update({
                        "answer": answer,
                        "tool_calls": [{"tool": "get_drug_info", "args": {"drug_name": drug_name}}],
                        "reasoning": "Vision OCR + Direct database lookup",
                        "confidence": "high",
                        "method": "vision + database"
                    })
                    return response_base
            else:
                # Drug not found in database
                return {
                    "success": False,
                    "drug_name": drug_name,
                    "ocr_text": vision_result.get("extracted_text", ""),
                    "vision_confidence": vision_result.get("confidence", 0),
                    "answer": f"Médicament '{drug_name}' identifié mais non trouvé dans la base de données.",
                    "confidence": "low",
                    "method": "vision_only"
                }
        else:
            # No medication identified
            return {
                "success": False,
                "answer": "Je n'ai pas pu identifier le médicament dans l'image. Veuillez fournir une image plus claire montrant le nom du médicament.",
                "ocr_text": vision_result.get("ocr_text", ""),
                "confidence": "low",
                "tool_calls": [{"tool": "identify_medication", "args": {}}],
                "reasoning": "Vision OCR did not detect medication name"
            }
        
    except Exception as e:
        return {
            "success": False,
            "answer": f"Erreur lors de l'identification: {str(e)}",
            "error": str(e),
            "confidence": "low"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
