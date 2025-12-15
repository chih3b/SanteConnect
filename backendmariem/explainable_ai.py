"""
explainable_ai.py - Explainable AI Module
Provides transparency into agent decision-making process
"""
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    TOOL_SELECTION = "tool_selection"
    RESPONSE_GENERATION = "response_generation"
    INTENT_CLASSIFICATION = "intent_classification"
    ENTITY_EXTRACTION = "entity_extraction"


class ConfidenceLevel(Enum):
    HIGH = "high"      # > 0.85
    MEDIUM = "medium"  # 0.6 - 0.85
    LOW = "low"        # < 0.6


@dataclass
class ReasoningStep:
    step_id: str
    step_number: int
    action: str
    reasoning: str
    timestamp: str
    duration_ms: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDecision:
    tool_name: str
    selected: bool
    confidence: float
    reasoning: str
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    input_factors: List[str] = field(default_factory=list)


@dataclass 
class DecisionTrace:
    trace_id: str
    query: str
    timestamp: str
    total_duration_ms: float
    reasoning_steps: List[ReasoningStep]
    tool_decisions: List[ToolDecision]
    final_confidence: float
    confidence_level: str
    intent: str
    entities: Dict[str, Any]
    explanation_summary: str


class ExplainableAI:
    def __init__(self):
        self.current_trace: Optional[DecisionTrace] = None
        self.traces_history: List[DecisionTrace] = []
        self.step_counter = 0
        self.start_time = None
        
        self.metrics = {
            "total_queries": 0,
            "avg_confidence": 0.0,
            "tool_usage_count": {},
            "intent_distribution": {},
            "avg_response_time_ms": 0.0
        }
        
        self.tool_descriptions = {
            "extract_document_text": {
                "purpose": "Extract text from medical documents using OCR",
                "triggers": ["upload", "document", "scan", "read", "extract", "pdf", "image"],
                "category": "Document Processing"
            },
            "send_email": {
                "purpose": "Send email to patient via Gmail API",
                "triggers": ["email", "send", "notify", "contact", "message patient"],
                "category": "Communication"
            },
            "manage_appointment": {
                "purpose": "Check schedule or create appointments",
                "triggers": ["schedule", "appointment", "book", "free", "busy", "calendar", "available"],
                "category": "Calendar Management"
            }
        }
        
        self.intent_patterns = {
            "schedule_check": ["free", "busy", "schedule", "appointments today", "this week"],
            "appointment_create": ["add appointment", "book", "schedule with", "create appointment"],
            "email_send": ["send email", "email to", "notify", "contact patient"],
            "document_process": ["upload", "document", "scan", "extract", "summarize"],
            "general_query": ["what", "how", "explain", "help"]
        }
    
    def start_trace(self, query: str) -> str:
        self.current_trace = DecisionTrace(
            trace_id=str(uuid.uuid4())[:8],
            query=query,
            timestamp=datetime.now().isoformat(),
            total_duration_ms=0,
            reasoning_steps=[],
            tool_decisions=[],
            final_confidence=0.0,
            confidence_level="",
            intent="",
            entities={},
            explanation_summary=""
        )
        self.step_counter = 0
        self.start_time = time.time()
        self._classify_intent(query)
        self._extract_entities(query)
        return self.current_trace.trace_id
    
    def _classify_intent(self, query: str):
        query_lower = query.lower()
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for p in patterns if p in query_lower) / len(patterns)
            intent_scores[intent] = score
        
        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = max(intent_scores.values())
        
        if confidence > 0:
            confidence = min(0.95, confidence + 0.3)
        else:
            confidence = 0.5
            best_intent = "general_query"
        
        self.current_trace.intent = best_intent
        self.add_reasoning_step(
            action="Intent Classification",
            reasoning=f"Detected intent: '{best_intent}' with {confidence:.0%} confidence.",
            confidence=confidence,
            metadata={"intent_scores": intent_scores}
        )
    
    def _extract_entities(self, query: str):
        import re
        entities = {}
        
        date_patterns = [
            (r'\d{4}-\d{2}-\d{2}', 'iso_date'),
            (r'tomorrow', 'relative_date'),
            (r'today', 'relative_date'),
            (r'next\s+\w+', 'relative_date'),
            (r'this\s+week', 'relative_date'),
        ]
        
        for pattern, date_type in date_patterns:
            matches = re.findall(pattern, query.lower())
            if matches:
                entities['date'] = {'value': matches[0], 'type': date_type}
                break
        
        time_match = re.search(r'(\d{1,2})\s*(am|pm|:\d{2})', query.lower())
        if time_match:
            entities['time'] = time_match.group(0)
        
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
        if email_match:
            entities['email'] = email_match.group(0)
        
        self.current_trace.entities = entities
        self.add_reasoning_step(
            action="Entity Extraction",
            reasoning=f"Extracted {len(entities)} entities: {list(entities.keys())}",
            confidence=0.9 if entities else 0.7,
            metadata={"entities": entities}
        )
    
    def add_reasoning_step(self, action: str, reasoning: str, confidence: float, metadata: Dict = None):
        if not self.current_trace:
            return
        
        self.step_counter += 1
        step = ReasoningStep(
            step_id=f"step_{self.step_counter}",
            step_number=self.step_counter,
            action=action,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat(),
            duration_ms=(time.time() - self.start_time) * 1000,
            confidence=confidence,
            metadata=metadata or {}
        )
        self.current_trace.reasoning_steps.append(step)
    
    def add_tool_decision(self, tool_name: str, selected: bool, reasoning: str, 
                          confidence: float, input_factors: List[str] = None):
        if not self.current_trace:
            return
        
        decision = ToolDecision(
            tool_name=tool_name,
            selected=selected,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=[],
            input_factors=input_factors or []
        )
        self.current_trace.tool_decisions.append(decision)
        
        self.add_reasoning_step(
            action=f"Tool Selection: {tool_name}",
            reasoning=reasoning,
            confidence=confidence
        )
    
    def finalize_trace(self, response: str) -> DecisionTrace:
        if not self.current_trace:
            return None
        
        self.current_trace.total_duration_ms = (time.time() - self.start_time) * 1000
        
        if self.current_trace.reasoning_steps:
            confidences = [s.confidence for s in self.current_trace.reasoning_steps]
            self.current_trace.final_confidence = sum(confidences) / len(confidences)
        
        conf = self.current_trace.final_confidence
        if conf > 0.85:
            self.current_trace.confidence_level = ConfidenceLevel.HIGH.value
        elif conf > 0.6:
            self.current_trace.confidence_level = ConfidenceLevel.MEDIUM.value
        else:
            self.current_trace.confidence_level = ConfidenceLevel.LOW.value
        
        self.current_trace.explanation_summary = self._generate_summary()
        self.traces_history.append(self.current_trace)
        if len(self.traces_history) > 100:
            self.traces_history = self.traces_history[-100:]
        
        self._update_metrics()
        return self.current_trace
    
    def _update_metrics(self):
        self.metrics["total_queries"] += 1
        if self.traces_history:
            confidences = [t.final_confidence for t in self.traces_history]
            self.metrics["avg_confidence"] = sum(confidences) / len(confidences)
        
        for decision in self.current_trace.tool_decisions:
            if decision.selected:
                tool = decision.tool_name
                self.metrics["tool_usage_count"][tool] = self.metrics["tool_usage_count"].get(tool, 0) + 1
        
        intent = self.current_trace.intent
        self.metrics["intent_distribution"][intent] = self.metrics["intent_distribution"].get(intent, 0) + 1
        
        times = [t.total_duration_ms for t in self.traces_history]
        self.metrics["avg_response_time_ms"] = sum(times) / len(times)
    
    def _generate_summary(self) -> str:
        trace = self.current_trace
        tools_used = [d.tool_name for d in trace.tool_decisions if d.selected]
        
        summary = f"Request type: '{trace.intent.replace('_', ' ')}'. "
        if trace.entities:
            entity_str = ", ".join([f"{k}: {v}" for k, v in trace.entities.items()])
            summary += f"Key details: {entity_str}. "
        if tools_used:
            summary += f"Tools used: {', '.join(tools_used)}. "
        summary += f"Confidence: {trace.confidence_level} ({trace.final_confidence:.0%})."
        return summary
    
    def get_trace_dict(self) -> Dict:
        if not self.current_trace:
            return {}
        
        return {
            "trace_id": self.current_trace.trace_id,
            "query": self.current_trace.query,
            "timestamp": self.current_trace.timestamp,
            "duration_ms": round(self.current_trace.total_duration_ms, 2),
            "intent": self.current_trace.intent,
            "entities": self.current_trace.entities,
            "confidence": {
                "score": round(self.current_trace.final_confidence, 3),
                "level": self.current_trace.confidence_level
            },
            "reasoning_chain": [
                {
                    "step": s.step_number,
                    "action": s.action,
                    "reasoning": s.reasoning,
                    "confidence": round(s.confidence, 3),
                    "duration_ms": round(s.duration_ms, 2)
                }
                for s in self.current_trace.reasoning_steps
            ],
            "tool_decisions": [
                {
                    "tool": d.tool_name,
                    "selected": d.selected,
                    "confidence": round(d.confidence, 3),
                    "reasoning": d.reasoning
                }
                for d in self.current_trace.tool_decisions
            ],
            "summary": self.current_trace.explanation_summary,
            "metrics": self.get_metrics()
        }
    
    def get_metrics(self) -> Dict:
        return {
            "total_queries": self.metrics["total_queries"],
            "avg_confidence": round(self.metrics["avg_confidence"], 3),
            "avg_response_time_ms": round(self.metrics["avg_response_time_ms"], 2),
            "tool_usage": self.metrics["tool_usage_count"],
            "intent_distribution": self.metrics["intent_distribution"]
        }
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        recent = self.traces_history[-limit:]
        return [
            {
                "trace_id": t.trace_id,
                "query": t.query[:50] + "..." if len(t.query) > 50 else t.query,
                "timestamp": t.timestamp,
                "intent": t.intent,
                "confidence": round(t.final_confidence, 3),
                "duration_ms": round(t.total_duration_ms, 2)
            }
            for t in reversed(recent)
        ]


_xai_instance = None

def get_xai() -> ExplainableAI:
    global _xai_instance
    if _xai_instance is None:
        _xai_instance = ExplainableAI()
    return _xai_instance
