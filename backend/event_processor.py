from sqlalchemy.orm import Session
from models import Event, AIInteraction, Feature, FEATURE_DIMENSIONS
from typing import Dict, List, Any
from datetime import datetime, timedelta
import statistics
import json

class EventProcessor:
    """Process behavioral events into recruiter insights"""
    
    def __init__(self):
        self.feature_processors = {
            "Problem Understanding": self._compute_problem_understanding,
            "Analytical Thinking": self._compute_analytical_thinking,
            "Debugging Ability": self._compute_debugging_ability,
            "Independence vs AI Reliance": self._compute_ai_reliance,
            "Quality of AI Collaboration": self._compute_ai_collaboration,
            "Iterative Thinking": self._compute_iterative_thinking,
            "Code Quality": self._compute_code_quality,
            "Error Handling": self._compute_error_handling,
            "Data Exploration Skills": self._compute_data_exploration,
            "Communication Clarity": self._compute_communication_clarity
        }
    
    async def compute_features(self, session_id: str, db: Session) -> Dict[str, float]:
        """Compute all behavioral features for a session"""
        # Get all events and AI interactions for the session
        events = db.query(Event).filter(
            Event.session_id == session_id
        ).order_by(Event.sequence_number).all()
        
        ai_interactions = db.query(AIInteraction).filter(
            AIInteraction.session_id == session_id
        ).order_by(AIInteraction.timestamp).all()
        
        # Compute each feature
        computed_features = {}
        
        for feature_name, processor in self.feature_processors.items():
            try:
                feature_data = processor(events, ai_interactions)
                
                # Store feature in database
                feature = Feature(
                    session_id=session_id,
                    feature_name=feature_name,
                    feature_value=feature_data["value"],
                    confidence_score=feature_data["confidence"],
                    evidence=feature_data["evidence"]
                )
                db.add(feature)
                computed_features[feature_name] = feature_data["value"]
                
            except Exception as e:
                print(f"Error computing {feature_name}: {e}")
                computed_features[feature_name] = 0.0
        
        db.commit()
        return computed_features
    
    def _compute_problem_understanding(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Measure how well candidate understands the problem"""
        evidence = []
        
        # Look for early exploration patterns
        early_events = [e for e in events if e.sequence_number <= 10]
        data_exploration_early = len([e for e in early_events if e.event_type == "DATA_VIEW"])
        
        # Check for clarifying questions about problem
        concept_help_requests = len([
            ai for ai in ai_interactions 
            if ai.intent_label == "CONCEPT_HELP"
        ])
        
        # Measure code structure quality
        code_edits = [e for e in events if e.event_type == "CODE_EDIT"]
        structured_approach = len(code_edits) > 5  # Multiple iterative edits
        
        # Calculate score (0-1 scale)
        score = 0.0
        
        if data_exploration_early > 0:
            score += 0.3
            evidence.append(f"Explored data early ({data_exploration_early} views)")
        
        if concept_help_requests <= 2:  # Not too many concept questions
            score += 0.3
            evidence.append("Minimal concept clarification needed")
        
        if structured_approach:
            score += 0.4
            evidence.append("Showed structured coding approach")
        
        return {
            "value": min(score, 1.0),
            "confidence": 0.8,
            "evidence": evidence
        }
    
    def _compute_analytical_thinking(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Measure analytical and logical thinking patterns"""
        evidence = []
        
        # Look for systematic data exploration
        data_views = [e for e in events if e.event_type == "DATA_VIEW"]
        systematic_exploration = len(data_views) >= 3
        
        # Check for hypothesis testing patterns (run -> analyze -> iterate)
        run_events = [e for e in events if e.event_type == "CODE_RUN"]
        analysis_pattern = len(run_events) >= 2
        
        # Look for validation requests
        validation_requests = len([
            ai for ai in ai_interactions 
            if ai.intent_label == "VALIDATION"
        ])
        
        score = 0.0
        
        if systematic_exploration:
            score += 0.4
            evidence.append(f"Systematic data exploration ({len(data_views)} views)")
        
        if analysis_pattern:
            score += 0.3
            evidence.append(f"Iterative testing approach ({len(run_events)} runs)")
        
        if validation_requests > 0:
            score += 0.3
            evidence.append(f"Sought validation ({validation_requests} times)")
        
        return {
            "value": min(score, 1.0),
            "confidence": 0.7,
            "evidence": evidence
        }
    
    def _compute_debugging_ability(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Measure debugging and problem-solving skills"""
        evidence = []
        
        # Count errors and resolutions
        errors = [e for e in events if e.event_type == "ERROR_OCCURRED"]
        resolutions = [e for e in events if e.event_type == "ERROR_RESOLVED"]
        resolution_rate = len(resolutions) / max(len(errors), 1)
        
        # Check for independent debugging vs AI help
        debug_help_requests = len([
            ai for ai in ai_interactions 
            if ai.intent_label == "DEBUG_HELP"
        ])
        
        # Look for systematic debugging approach
        code_edits_after_errors = 0
        for error in errors:
            subsequent_edits = len([
                e for e in events 
                if e.event_type == "CODE_EDIT" and e.sequence_number > error.sequence_number
                and e.sequence_number <= error.sequence_number + 5
            ])
            code_edits_after_errors += subsequent_edits
        
        score = 0.0
        
        if resolution_rate >= 0.7:
            score += 0.4
            evidence.append(f"High error resolution rate ({resolution_rate:.1%})")
        
        if debug_help_requests <= len(errors) * 0.5:  # Didn't ask for help on every error
            score += 0.3
            evidence.append("Showed independent debugging effort")
        
        if code_edits_after_errors > 0:
            score += 0.3
            evidence.append("Made systematic code changes after errors")
        
        return {
            "value": min(score, 1.0),
            "confidence": 0.9,
            "evidence": evidence
        }
    
    def _compute_ai_reliance(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Measure balance between independence and AI assistance"""
        evidence = []
        
        total_ai_requests = len(ai_interactions)
        total_events = len(events)
        ai_request_ratio = total_ai_requests / max(total_events, 1)
        
        # Check for direct solution requests (negative indicator)
        solution_requests = len([
            ai for ai in ai_interactions 
            if ai.intent_label == "DIRECT_SOLUTION"
        ])
        
        # Check if AI responses were actually used
        used_responses = len([
            ai for ai in ai_interactions 
            if ai.response_used
        ])
        usage_rate = used_responses / max(total_ai_requests, 1)
        
        # Calculate independence score (higher is more independent)
        score = 1.0
        
        if ai_request_ratio > 0.3:  # Too many AI requests relative to actions
            score -= 0.4
            evidence.append(f"High AI request frequency ({ai_request_ratio:.1%})")
        
        if solution_requests > 2:
            score -= 0.3
            evidence.append(f"Frequent direct solution requests ({solution_requests})")
        
        if usage_rate < 0.5 and total_ai_requests > 0:  # Asking but not using responses
            score -= 0.2
            evidence.append(f"Low AI response utilization ({usage_rate:.1%})")
        
        # Bonus for strategic AI use
        if 0.1 <= ai_request_ratio <= 0.2 and usage_rate > 0.7:
            score += 0.2
            evidence.append("Strategic and effective AI collaboration")
        
        return {
            "value": max(score, 0.0),
            "confidence": 0.8,
            "evidence": evidence
        }
    
    def _compute_ai_collaboration(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Measure quality of AI collaboration"""
        evidence = []
        
        if not ai_interactions:
            return {"value": 0.0, "confidence": 1.0, "evidence": ["No AI interactions"]}
        
        # Check for good collaboration patterns
        approach_help = len([ai for ai in ai_interactions if ai.intent_label == "APPROACH_HELP"])
        validation_requests = len([ai for ai in ai_interactions if ai.intent_label == "VALIDATION"])
        
        # Quality indicators
        total_requests = len(ai_interactions)
        constructive_requests = approach_help + validation_requests
        constructive_ratio = constructive_requests / total_requests
        
        # Check for context-rich prompts (longer, more detailed)
        detailed_prompts = len([
            ai for ai in ai_interactions 
            if len(ai.user_prompt) > 50  # Detailed questions
        ])
        detail_ratio = detailed_prompts / total_requests
        
        score = 0.0
        
        if constructive_ratio >= 0.5:
            score += 0.4
            evidence.append(f"High ratio of constructive requests ({constructive_ratio:.1%})")
        
        if detail_ratio >= 0.6:
            score += 0.3
            evidence.append(f"Provided detailed context in prompts ({detail_ratio:.1%})")
        
        if approach_help > 0:
            score += 0.3
            evidence.append(f"Sought strategic guidance ({approach_help} times)")
        
        return {
            "value": min(score, 1.0),
            "confidence": 0.7,
            "evidence": evidence
        }
    
    def _compute_iterative_thinking(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Measure iterative and incremental approach"""
        evidence = []
        
        # Look for iterative patterns: edit -> run -> analyze -> repeat
        code_runs = [e for e in events if e.event_type == "CODE_RUN"]
        result_evaluations = [e for e in events if e.event_type == "RESULT_EVALUATED"]
        
        iteration_cycles = min(len(code_runs), len(result_evaluations))
        
        # Check for incremental code changes
        code_edits = [e for e in events if e.event_type == "CODE_EDIT"]
        incremental_pattern = len(code_edits) > 3  # Multiple small changes
        
        score = 0.0
        
        if iteration_cycles >= 2:
            score += 0.5
            evidence.append(f"Multiple iteration cycles ({iteration_cycles})")
        
        if incremental_pattern:
            score += 0.3
            evidence.append(f"Incremental code development ({len(code_edits)} edits)")
        
        if len(code_runs) >= 3:
            score += 0.2
            evidence.append(f"Frequent testing approach ({len(code_runs)} runs)")
        
        return {
            "value": min(score, 1.0),
            "confidence": 0.8,
            "evidence": evidence
        }
    
    # Placeholder implementations for remaining features
    def _compute_code_quality(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Placeholder for code quality assessment"""
        return {"value": 0.5, "confidence": 0.3, "evidence": ["Code quality assessment not implemented"]}
    
    def _compute_error_handling(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Placeholder for error handling assessment"""
        return {"value": 0.5, "confidence": 0.3, "evidence": ["Error handling assessment not implemented"]}
    
    def _compute_data_exploration(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Placeholder for data exploration skills assessment"""
        return {"value": 0.5, "confidence": 0.3, "evidence": ["Data exploration assessment not implemented"]}
    
    def _compute_communication_clarity(self, events: List[Event], ai_interactions: List[AIInteraction]) -> Dict[str, Any]:
        """Placeholder for communication clarity assessment"""
        return {"value": 0.5, "confidence": 0.3, "evidence": ["Communication clarity assessment not implemented"]}