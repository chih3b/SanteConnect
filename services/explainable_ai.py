"""
Explainable AI Module for SanteConnect
Provides transparency into AI decision-making for medication queries
"""
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ReasoningStep:
    step_number: int
    action: str
    reasoning: str
    confidence: float
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDecision:
    tool_name: str
    selected: bool
    confidence: float
    reasoning: str
    input_factors: List[str] = field(default_factory=list)


class MedicationXAI:
    """Explainable AI for medication identification and queries"""
    
    def __init__(self):
        self.current_trace = None
        self.traces_history = []
        self.step_counter = 0
        self.start_time = None
        
        self.metrics = {
            "total_queries": 0,
            "avg_confidence": 0.0,
            "tool_usage": {},
            "query_types": {}
        }
        
        # Tool descriptions for explanations
        self.tool_info = {
            "get_drug_details_tool": {
                "name": "Drug Database Lookup",
                "icon": "💊",
                "description": "Searches local Tunisian medication database"
            },
            "search_medication_tool": {
                "name": "Fuzzy Search",
                "icon": "🔍",
                "description": "Finds similar drug names using fuzzy matching"
            },
            "check_drug_interactions_tool": {
                "name": "Interaction Checker",
                "icon": "⚠️",
                "description": "Checks for dangerous drug combinations"
            },
            "check_pregnancy_safety_tool": {
                "name": "Pregnancy Safety",
                "icon": "🤰",
                "description": "Checks medication safety during pregnancy"
            },
            "find_alternatives_tool": {
                "name": "Alternative Finder",
                "icon": "🔄",
                "description": "Finds generic or equivalent medications"
            },
            "search_by_symptom_tool": {
                "name": "Symptom Search",
                "icon": "🩺",
                "description": "Finds medications for specific symptoms"
            },
            "compare_medications_tool": {
                "name": "Drug Comparison",
                "icon": "⚖️",
                "description": "Compares two medications"
            },
            "identify_medication_tool": {
                "name": "Image Recognition",
                "icon": "📷",
                "description": "Identifies medication from image using OCR"
            },
            "search_web_drug_info_tool": {
                "name": "Web Search",
                "icon": "🌐",
                "description": "Searches medical websites for drug info"
            }
        }
        
        # Query type patterns
        self.query_patterns = {
            "drug_info": ["what is", "tell me about", "information", "c'est quoi"],
            "interaction": ["interaction", "together", "combine", "avec"],
            "pregnancy": ["pregnancy", "pregnant", "grossesse", "enceinte", "breastfeeding"],
            "alternative": ["alternative", "generic", "substitute", "remplacer"],
            "symptom": ["for headache", "for pain", "for fever", "pour la", "contre"],
            "comparison": ["vs", "versus", "compare", "difference", "ou"],
            "identification": ["identify", "what medication", "quel médicament"]
        }
    
    def start_trace(self, query: str, query_type: str = "chat") -> str:
        """Start a new XAI trace for a query"""
        self.current_trace = {
            "trace_id": str(uuid.uuid4())[:8],
            "query": query,
            "query_type": query_type,
            "timestamp": datetime.now().isoformat(),
            "reasoning_steps": [],
            "tool_decisions": [],
            "final_confidence": 0.0,
            "confidence_level": "medium",
            "detected_intent": "",
            "entities": [],
            "duration_ms": 0
        }
        self.step_counter = 0
        self.start_time = time.time()
        
        # Classify intent
        self._classify_intent(query)
        
        return self.current_trace["trace_id"]
    
    def _classify_intent(self, query: str):
        """Classify the user's intent"""
        query_lower = query.lower()
        
        for intent, patterns in self.query_patterns.items():
            if any(p in query_lower for p in patterns):
                self.current_trace["detected_intent"] = intent
                self.add_reasoning_step(
                    "Intent Detection",
                    f"Detected query type: {intent.replace('_', ' ').title()}",
                    0.85
                )
                return
        
        self.current_trace["detected_intent"] = "general"
        self.add_reasoning_step(
            "Intent Detection",
            "General medication query detected",
            0.7
        )
    
    def add_reasoning_step(self, action: str, reasoning: str, confidence: float, metadata: Dict = None):
        """Add a reasoning step to the trace"""
        if not self.current_trace:
            return
        
        self.step_counter += 1
        step = {
            "step": self.step_counter,
            "action": action,
            "reasoning": reasoning,
            "confidence": round(confidence, 3),
            "duration_ms": round((time.time() - self.start_time) * 1000, 2)
        }
        if metadata:
            step["metadata"] = metadata
        
        self.current_trace["reasoning_steps"].append(step)
    
    def add_tool_decision(self, tool_name: str, selected: bool, reasoning: str, 
                          confidence: float, input_factors: List[str] = None):
        """Record a tool selection decision"""
        if not self.current_trace:
            return
        
        tool_info = self.tool_info.get(tool_name, {"name": tool_name, "icon": "🔧"})
        
        decision = {
            "tool": tool_name,
            "display_name": tool_info.get("name", tool_name),
            "icon": tool_info.get("icon", "🔧"),
            "selected": selected,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "factors": input_factors or []
        }
        self.current_trace["tool_decisions"].append(decision)
        
        # Also add as reasoning step
        self.add_reasoning_step(
            f"Tool: {tool_info.get('name', tool_name)}",
            reasoning,
            confidence
        )
    
    def add_ocr_result(self, extracted_text: str, confidence: float, method: str):
        """Record OCR extraction results"""
        self.add_reasoning_step(
            "OCR Extraction",
            f"Extracted text using {method} with {confidence:.0%} confidence",
            confidence,
            {"text_length": len(extracted_text), "method": method}
        )
    
    def add_drug_match(self, query: str, matched_drug: str, similarity: float, is_exact: bool):
        """Record drug matching decision"""
        if is_exact:
            self.add_reasoning_step(
                "Drug Match",
                f"Exact match found: '{matched_drug}'",
                0.95
            )
        else:
            self.add_reasoning_step(
                "Fuzzy Match",
                f"Best match for '{query}' → '{matched_drug}' ({similarity:.0f}% similar)",
                similarity / 100,
                {"original_query": query, "similarity_score": similarity}
            )
    
    def add_database_search(self, query: str, results_count: int, top_match: str = None):
        """Record database search results"""
        if results_count > 0:
            self.add_reasoning_step(
                "Database Search",
                f"Found {results_count} matching medications" + (f", best: '{top_match}'" if top_match else ""),
                0.8 if results_count > 0 else 0.3
            )
        else:
            self.add_reasoning_step(
                "Database Search",
                f"No matches found for '{query}' in local database",
                0.3
            )
    
    def finalize_trace(self, success: bool = True) -> Dict:
        """Finalize the trace and calculate final metrics"""
        if not self.current_trace:
            return {}
        
        self.current_trace["duration_ms"] = round((time.time() - self.start_time) * 1000, 2)
        
        # Calculate final confidence
        if self.current_trace["reasoning_steps"]:
            confidences = [s["confidence"] for s in self.current_trace["reasoning_steps"]]
            self.current_trace["final_confidence"] = round(sum(confidences) / len(confidences), 3)
        
        # Set confidence level
        conf = self.current_trace["final_confidence"]
        if conf >= 0.8:
            self.current_trace["confidence_level"] = "high"
        elif conf >= 0.5:
            self.current_trace["confidence_level"] = "medium"
        else:
            self.current_trace["confidence_level"] = "low"
        
        # Generate summary
        self.current_trace["summary"] = self._generate_summary(success)
        
        # Update metrics
        self._update_metrics()
        
        # Store in history
        self.traces_history.append(self.current_trace.copy())
        if len(self.traces_history) > 50:
            self.traces_history = self.traces_history[-50:]
        
        return self.current_trace
    
    def _generate_summary(self, success: bool) -> str:
        """Generate human-readable summary"""
        trace = self.current_trace
        tools_used = [d["display_name"] for d in trace["tool_decisions"] if d["selected"]]
        
        summary = f"Query type: {trace['detected_intent'].replace('_', ' ').title()}. "
        if tools_used:
            summary += f"Used: {', '.join(tools_used)}. "
        summary += f"Confidence: {trace['confidence_level']} ({trace['final_confidence']:.0%})."
        
        if not success:
            summary += " ⚠️ Query could not be fully resolved."
        
        return summary
    
    def _update_metrics(self):
        """Update global metrics"""
        self.metrics["total_queries"] += 1
        
        # Update tool usage
        for decision in self.current_trace["tool_decisions"]:
            if decision["selected"]:
                tool = decision["tool"]
                self.metrics["tool_usage"][tool] = self.metrics["tool_usage"].get(tool, 0) + 1
        
        # Update query types
        intent = self.current_trace["detected_intent"]
        self.metrics["query_types"][intent] = self.metrics["query_types"].get(intent, 0) + 1
        
        # Update average confidence
        if self.traces_history:
            confs = [t["final_confidence"] for t in self.traces_history]
            self.metrics["avg_confidence"] = round(sum(confs) / len(confs), 3)
    
    def get_trace(self) -> Dict:
        """Get current trace as dictionary"""
        return self.current_trace or {}
    
    def get_metrics(self) -> Dict:
        """Get XAI metrics"""
        return self.metrics


# Singleton instance
_xai_instance = None

def get_xai() -> MedicationXAI:
    """Get or create XAI instance"""
    global _xai_instance
    if _xai_instance is None:
        _xai_instance = MedicationXAI()
    return _xai_instance
