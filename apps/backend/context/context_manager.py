from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

from agent.agent_state import AgentState


class EscalationTrigger(Enum):
    RETRY_THRESHOLD = "retry_threshold"
    ERROR_PATTERN = "error_pattern"
    COMPLEXITY_SPIKE = "complexity_spike"
    USER_FRUSTRATION = "user_frustration"
    BUSINESS_IMPACT = "business_impact"
    TECHNICAL_LIMITS = "technical_limits"

class ContextLevel(Enum):
    MINIMAL = 0
    WITH_ERROR = 1
    WITH_HISTORY = 2
    WITH_FULL_CONTEXT = 3

@dataclass
class EscalationSignal:
    trigger: EscalationTrigger
    confidence: float
    evidence: Dict[str, Any]
    severity: str  # "low", "medium", "high", "critical"

class AdaptiveContextManager:
    """Intelligent context management with adaptive escalation"""
    
    def __init__(self):
        self.escalation_patterns = self._initialize_escalation_patterns()
        self.conversation_memory = {}  # thread_id -> conversation context
        
        # Adaptive thresholds
        self.base_retry_threshold = 3
        self.complexity_threshold = 0.7
        self.frustration_indicators = ["confused", "frustrated", "not working", "broken"]
    
    def _initialize_escalation_patterns(self) -> Dict[str, Any]:
        """Initialize escalation patterns and thresholds"""
        return {
            "error_patterns": {
                "validation_cascade": {"threshold": 2, "severity": "medium"},
                "identical_repeated": {"threshold": 3, "severity": "high"},
                "timeout_errors": {"threshold": 2, "severity": "high"},
                "connection_errors": {"threshold": 1, "severity": "critical"}
            },
            "complexity_patterns": {
                "multi_entity_extraction": {"threshold": 0.8, "severity": "medium"},
                "complex_relationships": {"threshold": 0.9, "severity": "high"},
                "nested_operations": {"threshold": 0.7, "severity": "medium"}
            },
            "user_frustration": {
                "negative_sentiment": {"threshold": 0.6, "severity": "medium"},
                "repeated_requests": {"threshold": 3, "severity": "high"},
                "explicit_escalation": {"threshold": 1, "severity": "critical"}
            }
        }
    
    def analyze_escalation_signals(self, state: AgentState) -> List[EscalationSignal]:
        """Analyze multiple escalation signals using pattern recognition"""
        signals = []
        
        # Signal 1: Error Pattern Analysis
        error_signal = self._analyze_error_patterns(state["error_history"])
        if error_signal:
            signals.append(error_signal)
        
        # Signal 2: Complexity Analysis
        complexity_signal = self._analyze_complexity_spike(state)
        if complexity_signal:
            signals.append(complexity_signal)
        
        # Signal 3: User Frustration Detection
        frustration_signal = self._detect_user_frustration(state["messages"])
        if frustration_signal:
            signals.append(frustration_signal)
        
        # Signal 4: Business Impact Assessment
        business_signal = self._assess_business_impact(state)
        if business_signal:
            signals.append(business_signal)
        
        return signals
    
    def should_escalate(self, state: AgentState) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Advanced escalation logic with multiple criteria"""
        signals = self.analyze_escalation_signals(state)
        
        if not signals:
            # Fallback to retry count threshold
            if state["retry_count"] >= self._get_adaptive_retry_threshold(state):
                return True, "max_retries_reached", {"retry_count": state["retry_count"]}
            return False, None, None
        
        # Calculate escalation score
        escalation_score = self._calculate_escalation_score(signals)
        escalation_threshold = self._get_escalation_threshold(state)
        
        if escalation_score >= escalation_threshold:
            return True, "adaptive_escalation", {
                "signals": [s.trigger.value for s in signals],
                "score": escalation_score,
                "threshold": escalation_threshold
            }
        
        return False, None, None
    
    def prepare_adaptive_context(self, state: AgentState) -> Dict[str, Any]:
        """Prepare context with adaptive sizing based on situation analysis"""
        base_context = {
            "user_goal": state["user_goal"],
            "current_step": self._get_current_step_description(state),
            "progress": f"{state['current_step_index'] + 1}/{len(state['execution_plan'])}"
        }
        
        # Analyze situation to determine optimal context level
        context_level = self._determine_optimal_context_level(state)
        
        if context_level == ContextLevel.MINIMAL:
            return base_context
        
        elif context_level == ContextLevel.WITH_ERROR:
            return {
                **base_context,
                "last_error": state["last_error"],
                "error_hint": self._generate_targeted_hint(state["last_error"]),
                "quick_fixes": self._suggest_quick_fixes(state["last_error"])
            }
        
        elif context_level == ContextLevel.WITH_HISTORY:
            return {
                **base_context,
                "last_error": state["last_error"],
                "error_pattern_analysis": self._analyze_error_patterns(state["error_history"]),
                "success_patterns": self._find_similar_successful_cases(state),
                "strategic_guidance": self._generate_strategic_guidance(state)
            }
        
        else:  # FULL_CONTEXT
            return {
                **base_context,
                "complete_error_history": state["error_history"],
                "conversation_context": self._get_conversation_context(state),
                "similar_cases": self._find_similar_cases(state),
                "expert_recommendations": self._generate_expert_recommendations(state),
                "escalation_path": self._suggest_escalation_path(state)
            }
    
    def _analyze_error_patterns(self, error_history: List[str]) -> Optional[EscalationSignal]:
        """Analyze error patterns for escalation signals"""
        if len(error_history) < 2:
            return None
        
        # Check for identical repeated errors
        if len(set(error_history[-3:])) == 1:
            return EscalationSignal(
                trigger=EscalationTrigger.ERROR_PATTERN,
                confidence=0.9,
                evidence={"pattern": "identical_repeated", "count": len(error_history)},
                severity="high"
            )
        
        # Check for validation cascade failures
        validation_errors = [e for e in error_history if "validation" in e.lower()]
        if len(validation_errors) >= 2:
            return EscalationSignal(
                trigger=EscalationTrigger.ERROR_PATTERN,
                confidence=0.8,
                evidence={"pattern": "validation_cascade", "count": len(validation_errors)},
                severity="medium"
            )
        
        return None
    
    def _calculate_escalation_score(self, signals: List[EscalationSignal]) -> float:
        """Calculate weighted escalation score"""
        if not signals:
            return 0.0
        
        weights = {
            EscalationTrigger.USER_FRUSTRATION: 0.4,
            EscalationTrigger.BUSINESS_IMPACT: 0.3,
            EscalationTrigger.ERROR_PATTERN: 0.2,
            EscalationTrigger.COMPLEXITY_SPIKE: 0.1
        }
        
        score = 0.0
        for signal in signals:
            weight = weights.get(signal.trigger, 0.1)
            severity_multiplier = {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0}[signal.severity]
            score += signal.confidence * weight * severity_multiplier
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_adaptive_retry_threshold(self, state: AgentState) -> int:
        """Calculate adaptive retry threshold based on context"""
        base_threshold = self.base_retry_threshold
        
        # Adjust based on user type, complexity, etc.
        if self._is_high_value_user(state):
            return base_threshold + 1
        
        if self._is_simple_operation(state):
            return base_threshold - 1
        
        return base_threshold
