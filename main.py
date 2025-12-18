from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import asyncio
from services.vision import identify_medication
from services.drug_db import get_drug_info
from services.auth import (
    register_user, login_user, verify_token,
    create_conversation, get_conversations, get_conversation_messages,
    add_message, delete_conversation, update_user_profile, change_password
)
from PIL import Image
import io
from typing import Optional, List
import cv2
import numpy as np
import base64
import sys
import os

# Add backend folder to path for prescription scan imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Global agent system instance for prescription scanning
_prescription_agent_system = None


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


# ============== PRESCRIPTION SCAN ENDPOINTS ==============

async def get_prescription_agent_system():
    """Get or initialize the prescription agent system."""
    global _prescription_agent_system
    if _prescription_agent_system is None:
        try:
            from backend.agent_system import get_agent_system
            _prescription_agent_system = await get_agent_system()
            print("✅ Prescription Agent System initialized")
        except Exception as e:  
            print(f"⚠️ Failed to initialize Prescription Agent System: {e}")
            return None
    return _prescription_agent_system


@app.post("/prescription/scan") 
async def scan_prescription(
    file: UploadFile = File(...),
    filter_phi: bool = True
):
    """
    Scan a prescription image using the AI agent system.
    
    This endpoint:
    1. Segments the prescription image using SAM2
    2. Extracts text using OCR (Azure Vision API)
    3. Filters PHI (Protected Health Information) if enabled
    4. Extracts medication names and dosages
    5. Queries drug databases for alternatives (RxNorm, FDA, LLaMA)
    
    Args:
        file: Prescription image file
        filter_phi: Whether to redact patient information (default: True)
    
    Returns:
        JSON with extracted text, medications, and drug alternatives
    """
    agent_system = await get_prescription_agent_system()
    
    if agent_system is None:
        raise HTTPException(
            status_code=503, 
            detail="Prescription scanning service is initializing. Please try again in a moment."
        )
    
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Process through agent system
        result = await agent_system.process_image(
            image=image,
            mode="full",
            filter_phi=filter_phi,
            include_regions=False
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Processing failed'))
        
        # Format response for frontend
        data = result.get('data', {})
        
        # Text recognition
        text_data = data.get('text_recognition', {})
        extracted_text = text_data.get('text', '')
        
        # PHI filtering
        phi_data = data.get('phi_filtering', {})
        redacted_text = phi_data.get('redacted_text', extracted_text)
        phi_entities = phi_data.get('phi_entities', [])
        
        # Drug information
        drug_data = data.get('drug_information', {})
        medications = drug_data.get('medications', [])
        drug_alternatives = drug_data.get('drug_alternatives', [])
        
        # Convert image to base64 for display
        _, buffer = cv2.imencode('.png', image)
        image_base64 = base64.b64encode(buffer).decode()
        
        response = {
            "success": True,
            "extracted_text": extracted_text,
            "redacted_text": redacted_text if filter_phi else extracted_text,
            "phi_detected": len(phi_entities) > 0,
            "phi_entities": phi_entities if filter_phi else [],
            "medications": medications,
            "drug_alternatives": drug_alternatives,
            "total_medications": len(medications),
            "original_image": f"data:image/png;base64,{image_base64}",
            "agent_used": result.get('agent_name', 'OCRAgent'),
            "tools_used": result.get('tools_used', [])
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing prescription: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing prescription: {str(e)}")


@app.get("/prescription/status")
async def prescription_status():
    """Check the status of the prescription scanning system."""
    agent_system = await get_prescription_agent_system()
    
    if agent_system is None:
        return {
            "status": "initializing",
            "message": "Agent system is being initialized"
        }
    
    status = agent_system.get_status()
    return {
        "status": "ready" if status.get('initialized') else "initializing",
        "models": status.get('models', {}),
        "agents_available": list(status.get('system', {}).get('agents', {}).keys()) if status.get('system') else []
    }


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


# ============== PROFILE ENDPOINTS ==============

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

@app.put("/auth/profile")
async def update_profile(request: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    """Update user profile"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = update_user_profile(
        user["id"],
        name=request.name,
        phone=request.phone,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        address=request.address
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/auth/profile/image")
async def upload_profile_image(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload profile image"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read and encode image as base64
    contents = await file.read()
    
    # Resize image to max 200x200 for storage efficiency
    image = Image.open(io.BytesIO(contents))
    image.thumbnail((200, 200))
    
    # Convert to base64
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    profile_image = f"data:image/png;base64,{image_base64}"
    
    result = update_user_profile(user["id"], profile_image=profile_image)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/auth/password")
async def change_user_password(request: PasswordChangeRequest, user: dict = Depends(get_current_user)):
    """Change user password"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    result = change_password(user["id"], request.old_password, request.new_password)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


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
    from services.explainable_ai import get_xai
    
    try:
        xai = get_xai()
        xai.start_trace(query, "identification")
        
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Step 1: Use vision to identify the medication
        xai.add_reasoning_step("Image Processing", "Preprocessing image for OCR extraction", 0.9)
        vision_result = identify_medication(image)
        
        # Record OCR result
        ocr_text = vision_result.get("extracted_text", vision_result.get("ocr_text", ""))
        ocr_confidence = vision_result.get("confidence", 0.5)
        xai.add_ocr_result(ocr_text, ocr_confidence, "LLaVA Vision Model")
        
        # Step 2: If medication identified, get detailed info using FAST PATH
        if vision_result.get("drug_name"):
            from fast_query import fast_query
            from services.drug_db import get_drug_info, search_similar_drugs
            
            drug_name = vision_result.get("drug_name")
            xai.add_reasoning_step("Drug Detection", f"Detected medication name: '{drug_name}'", 0.85)
            
            # Try exact match first
            drug_info = get_drug_info(drug_name)
            
            # Get all similar medications (might be multiple variants like "Inflamyl" and "Inflamyl Fort")
            similar = search_similar_drugs(drug_name, limit=5)
            xai.add_database_search(drug_name, len(similar) if similar else 0, similar[0]["drug_name"] if similar else None)
            
            # If not found, try fuzzy search
            if not drug_info and similar and similar[0]["similarity_score"] >= 50:
                # Use the best match
                drug_name = similar[0]["drug_name"]
                drug_info = similar[0]["info"]
                xai.add_drug_match(vision_result.get("drug_name"), drug_name, similar[0]["similarity_score"], False)
                print(f"✅ Fuzzy match: '{vision_result.get('drug_name')}' → '{drug_name}' (score: {similar[0]['similarity_score']})")
            elif drug_info:
                xai.add_drug_match(drug_name, drug_name, 100, True)
            
            if drug_info:
                # Found the drug - use fast path for formatting
                xai.add_tool_decision("get_drug_details_tool", True, "Retrieved drug details from database", 0.9, ["drug_name_matched"])
                fast_result = fast_query(drug_name)
                
                # Build response with alternatives if multiple similar drugs found
                response_base = {
                    "success": True,
                    "drug_name": drug_name,
                    "ocr_text": ocr_text,
                    "vision_confidence": ocr_confidence,
                }
                
                # Only show similar medications if:
                # 1. OCR confidence is low (<70%) AND there are multiple close matches
                # 2. OR there are multiple matches with same similarity score (genuine ambiguity)
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
                        xai.add_reasoning_step("Ambiguity Detection", f"Found {len(close_matches)} similar medications due to low OCR confidence", 0.6)
                
                # Add fuzzy match info if applicable
                if vision_result.get("fuzzy_match"):
                    response_base["fuzzy_match_info"] = {
                        "original_ocr": vision_result.get("original_ocr"),
                        "matched_to": drug_name,
                        "confidence": vision_result.get("fuzzy_score", 0)
                    }
                
                # Finalize XAI trace
                xai_trace = xai.finalize_trace(success=True)
                
                if fast_result and fast_result.get("success"):
                    response_base.update({
                        "answer": fast_result.get("answer"),
                        "tool_calls": fast_result.get("tool_calls", []),
                        "reasoning": f"Vision OCR + Fast database lookup",
                        "confidence": fast_result.get("confidence", "high"),
                        "method": "vision + fast_path",
                        "xai": xai_trace
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
                        "method": "vision + database",
                        "xai": xai_trace
                    })
                    return response_base
            else:
                # Drug not found in database
                xai.add_reasoning_step("Database Lookup", f"Drug '{drug_name}' not found in local database", 0.3)
                xai_trace = xai.finalize_trace(success=False)
                return {
                    "success": False,
                    "drug_name": drug_name,
                    "ocr_text": ocr_text,
                    "vision_confidence": ocr_confidence,
                    "answer": f"Médicament '{drug_name}' identifié mais non trouvé dans la base de données.",
                    "confidence": "low",
                    "method": "vision_only",
                    "xai": xai_trace
                }
        else:
            # No medication identified
            xai.add_reasoning_step("OCR Failed", "Could not detect medication name in image", 0.2)
            xai_trace = xai.finalize_trace(success=False)
            return {
                "success": False,
                "answer": "Je n'ai pas pu identifier le médicament dans l'image. Veuillez fournir une image plus claire montrant le nom du médicament.",
                "ocr_text": vision_result.get("ocr_text", ""),
                "confidence": "low",
                "tool_calls": [{"tool": "identify_medication", "args": {}}],
                "reasoning": "Vision OCR did not detect medication name",
                "xai": xai_trace
            }
        
    except Exception as e:
        return {
            "success": False,
            "answer": f"Erreur lors de l'identification: {str(e)}",
            "error": str(e),
            "confidence": "low"
        }

# ============== STREAMING ENDPOINT ==============

async def stream_response(query: str):
    """Generator that streams the response word by word"""
    from cache_manager import get_cache
    from fast_query import fast_query, should_use_fast_path
    from agent_langgraph import ask_langgraph_agent
    import json
    
    cache = get_cache()
    result = None
    
    # Try fast path first
    if should_use_fast_path(query):
        cached = cache.get(query)
        if cached:
            result = cached
        else:
            result = fast_query(query)
            if result:
                cache.set(query, result)
    
    # Fall back to agent
    if not result:
        cached = cache.get(query)
        if cached:
            result = cached
        else:
            result = ask_langgraph_agent(query)
            if result.get("success", True):
                cache.set(query, result)
    
    # Stream the answer word by word
    answer = result.get("answer", "Sorry, I couldn't process your request.")
    words = answer.split(" ")
    
    # Send metadata first (including XAI)
    metadata = {
        "type": "metadata",
        "confidence": result.get("confidence", "medium"),
        "tool_calls": result.get("tool_calls", []),
        "xai": result.get("xai")  # Include XAI trace
    }
    yield f"data: {json.dumps(metadata)}\n\n"
    
    # Stream words with small delay for effect
    for i, word in enumerate(words):
        chunk = {"type": "content", "content": word + " "}
        yield f"data: {json.dumps(chunk)}\n\n"
        await asyncio.sleep(0.02)  # 20ms delay between words
    
    # Send done signal
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@app.get("/agent/query/stream")
async def agent_query_stream(query: str):
    """
    Streaming version of agent query - returns response word by word
    Uses Server-Sent Events (SSE)
    """
    return StreamingResponse(
        stream_response(query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
