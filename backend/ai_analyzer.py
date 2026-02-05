"""
AI Analyzer - Backend AI for analyzing candidate behavior and generating recruiter insights.
This AI never interacts with candidates directly.

V2.0: Advanced metrics system with confidence weighting, sequence analysis, and structural SQL evaluation.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models import Event, AIInteraction, Session as SessionModel, EVENT_CATEGORIES
from langchain_config import get_ai_engine
from advanced_metrics import AdvancedMetricsCalculator
import logging

logger = logging.getLogger(__name__)


class BehaviorAnalyzer:
    """Analyzes candidate events and generates recruiter insights using AI"""
    
    def __init__(self):
        self.ai_engine = None
        try:
            self.ai_engine = get_ai_engine()
        except Exception as e:
            logger.warning(f"AI engine not initialized for BehaviorAnalyzer: {e}")
    
    async def analyze_session(
        self, 
        session_id: str, 
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze complete interview session and generate insights
        
        Args:
            session_id: Session to analyze
            db: Database session
        
        Returns:
            Comprehensive analysis with scores, insights, and recommendations
        """
        # Fetch session data
        session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
        if not session:
            return {"error": "Session not found"}
        
        # Fetch all events and AI interactions
        events = db.query(Event).filter(
            Event.session_id == session_id
        ).order_by(Event.sequence_number).all()
        
        ai_interactions = db.query(AIInteraction).filter(
            AIInteraction.session_id == session_id
        ).order_by(AIInteraction.timestamp).all()
        
        # Build analysis context
        analysis_context = self._build_analysis_context(
            session, events, ai_interactions
        )
        
        # Generate AI insights
        insights = await self._generate_insights(analysis_context)
        
        return insights
    
    def _build_analysis_context(
        self,
        session: SessionModel,
        events: List[Event],
        ai_interactions: List[AIInteraction]
    ) -> Dict[str, Any]:
        """Build structured context for AI analysis with advanced metrics"""
        
        # Prepare events for advanced calculator
        event_data = [
            {
                "type": e.event_type,
                "timestamp": e.timestamp,
                "metadata": e.event_metadata or {}
            }
            for e in events
        ]
        
        # Prepare AI interactions
        ai_data = [
            {
                "user_prompt": ai.user_prompt,
                "ai_response": ai.ai_response,
                "intent_label": ai.intent_label,
                "response_used": ai.response_used,
                "timestamp": ai.timestamp
            }
            for ai in ai_interactions
        ]
        
        # Determine problem difficulty (you can enhance this based on problem metadata)
        problem_difficulty = 1.0  # Default medium difficulty
        if session.problem_id:
            # TODO: Look up problem difficulty from problems database
            # For now, use default
            pass
        
        # Calculate advanced metrics
        calculator = AdvancedMetricsCalculator(
            events=event_data,
            ai_interactions=ai_data,
            problem_difficulty=problem_difficulty
        )
        advanced_metrics = calculator.calculate_all_metrics()
        
        # Categorize events for context
        event_summary = {}
        for category, event_types in EVENT_CATEGORIES.items():
            event_summary[category] = [
                {
                    "type": e.event_type,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "metadata": e.event_metadata
                }
                for e in events if e.event_type in event_types
            ]
        
        # Extract SQL queries with full context
        sql_queries = []
        for e in events:
            if e.event_type == "SQL_RUN" and e.event_metadata:
                sql_queries.append({
                    "query": e.event_metadata.get("query", ""),
                    "result": e.event_metadata.get("result"),
                    "error": e.event_metadata.get("error"),
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                })
        
        # Calculate session metrics
        duration = None
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds() / 60
        
        # Interview phase data
        interview_qa = []
        if session.phase in ["interview", "completed"]:
            interview_qa = [
                {
                    "type": e.event_type,
                    "content": e.event_metadata.get("question") or e.event_metadata.get("answer", ""),
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                }
                for e in events 
                if e.event_type in ["INTERVIEW_QUESTION", "INTERVIEW_ANSWER"]
            ]
        
        return {
            "candidate_name": session.candidate_name,
            "session_duration_minutes": duration,
            "phase": session.phase,
            "total_events": len(events),
            "event_categories": event_summary,
            "sql_queries": sql_queries,
            "ai_interactions_count": len(ai_interactions),
            "interview_qa": interview_qa,
            "problem_id": session.problem_id,
            "advanced_metrics": advanced_metrics  # New!
        }
    
    async def _generate_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to generate deep insights from advanced metrics"""
        
        if not self.ai_engine:
            return self._generate_fallback_insights(context)
        
        # Extract advanced metrics
        metrics = context.get('advanced_metrics', {})
        
        system_prompt = """You are an Expert Technical Interview Analyst AI (V2.0).

You analyze confidence-weighted behavioral metrics from an AI-assisted data interview.

KEY PRINCIPLES:
1. Every insight must cite CONFIDENCE LEVEL - low confidence = uncertain
2. Distinguish AI usage types: hints (good) vs code copying (concerning)
3. Focus on SEQUENCES not just counts (thinking patterns)
4. Factor in PROBLEM DIFFICULTY normalization
5. Use CALIBRATED thresholds from real candidate baselines
6. Never hallucinate - if confidence is low, state uncertainty

⸻

YOU RECEIVE ADVANCED METRICS:

Each metric includes:
- value: The calculated score
- confidence: 0.0-1.0 (based on sample size)
- sample_size: Number of observations
- interpretation: Calibrated category

Metrics:
• exploration: Data-first approach quality (weighted by timing)
• iteration: Meaningful iteration (filters superficial edits)
• debugging: Error resolution effectiveness (paired error→resolution)
• ai_reliance: Weighted by intent (code gen > hints > validation)
• ai_collaboration: Modification quality (not just count)
• sql_complexity: Structural analysis (joins, nesting, CTEs)
• independence: 1 - ai_reliance
• thinking_sequences: Detected behavioral patterns
• ai_intent_breakdown: Classified by intent type

⸻

AI USAGE CLASSIFICATION:

HEALTHY AI USAGE (low reliance score):
- Validation requests
- Hint requests  
- Concept explanations
- Approach verification

CONCERNING AI USAGE (high reliance score):
- Direct code generation requests
- Copy without modification
- Repeated similar help requests

⸻

CONFIDENCE HANDLING:

- confidence > 0.7: "We observed..."
- confidence 0.4-0.7: "Evidence suggests..."
- confidence < 0.4: "Limited data indicates..." or omit

Never make strong claims on low-confidence metrics.

⸻

OUTPUT STRUCTURE:

**CANDIDATE SUMMARY**
- Overall profile with confidence caveats
- Behavioral classification

**PROBLEM-SOLVING APPROACH**
- Exploration quality (cite: value, confidence, interpretation)
- Iteration quality (meaningful vs superficial)
- Sequence patterns detected

**TECHNICAL CAPABILITY**
- SQL structural complexity (not keyword-based)
- Join depth, nesting, aggregations
- Progression from simple → complex

**AI COLLABORATION ASSESSMENT**
- Intent breakdown (what types of help?)
- Reliance score WITH confidence
- Behavioral profile: Independent | Healthy Collaborator | Dependent
- Causality: AI used before or after struggle?

**INTERVIEW PERFORMANCE ANALYSIS**
- Response quality: coherent vs nonsensical
- Technical articulation: can they explain their SQL?
- Self-reflection: awareness of their process
- Communication red flags: gibberish, evasion, contradictions
- Overall interview competence score

**STRENGTHS** (confidence-weighted)
- Only include if confidence > 0.5
- Cite metric + confidence

**CONCERNS** (confidence-weighted)
- Red flags with evidence
- Note if low sample size limits conclusions

**RECOMMENDATION**
- Overall assessment
- Confidence in recommendation
- What additional data would improve confidence

⚠️ RULES:
- NO invented psychology
- NO claims beyond data
- CITE confidence for every insight
- ACKNOWLEDGE when data is insufficient
- Use plain language (no event names, no formulas)"""

        user_message = f"""Analyze this interview session using advanced confidence-weighted metrics:

=== SESSION CONTEXT ===
Candidate: {context['candidate_name']}
Duration: {context.get('session_duration_minutes', 'N/A')} minutes
Phase: {context['phase']}
Problem Difficulty: {metrics.get('problem_difficulty', 1.0)}x (1.0 = medium)

=== ADVANCED BEHAVIORAL METRICS ===
{json.dumps(metrics, indent=2)}

=== SQL ACTIVITY ===
Total Queries: {len(context.get('sql_queries', []))}
Query Examples (first 3):
{json.dumps(context.get('sql_queries', [])[:3], indent=2)}

=== AI INTERACTION ANALYSIS ===
Total Interactions: {context.get('ai_interactions_count', 0)}
Intent Classification: {json.dumps(metrics.get('ai_intent_breakdown', {}), indent=2)}

=== THINKING SEQUENCES DETECTED ===
{json.dumps(metrics.get('thinking_sequences', []), indent=2)}

=== OVERALL CONFIDENCE ===
Analysis Confidence: {metrics.get('overall_confidence', 0.0):.2f} / 1.0
(Based on sample sizes across all metrics)

=== INTERVIEW ENGAGEMENT ===
Q&A Exchanges: {len(context.get('interview_qa', []))}

Interview Responses (evaluate quality):
{json.dumps(context.get('interview_qa', [])[:10], indent=2)}

CRITICAL: Analyze interview responses for:
- Coherence and relevance (vs gibberish/random text)
- Depth of technical understanding
- Ability to explain their SQL decisions
- Self-awareness about strengths/weaknesses
- Communication clarity

Red flags in responses:
- Incoherent or nonsensical answers
- Copy-pasted code without explanation
- Unable to explain their own queries
- Vague answers with no specifics
- Contradictory statements

⸻

Generate comprehensive recruiter-friendly analysis with confidence-weighted insights.

Return both:
1. Narrative analysis (following structure in system prompt)
2. JSON summary:

{{
  "overall_score": <0-100>,
  "confidence_in_score": <0.0-1.0>,
  "hire_recommendation": "<strong_yes|yes|maybe|no|strong_no>",
  "recommendation_confidence": <0.0-1.0>,
  "behavioral_profile": "<Independent Thinker|Healthy AI Collaborator|AI Dependent>",
  
  "key_strengths": [
    {{"strength": "...", "confidence": 0.0-1.0, "evidence": "..."}}
  ],
  
  "concerns": [
    {{"concern": "...", "confidence": 0.0-1.0, "evidence": "..."}}
  ],
  
  "dimension_scores": {{
    "problem_understanding": {{"score": 0-100, "confidence": 0.0-1.0}},
    "analytical_thinking": {{"score": 0-100, "confidence": 0.0-1.0}},
    "debugging_ability": {{"score": 0-100, "confidence": 0.0-1.0}},
    "ai_collaboration_quality": {{"score": 0-100, "confidence": 0.0-1.0}},
    "sql_complexity": {{"score": 0-100, "confidence": 0.0-1.0}},
    "independence": {{"score": 0-100, "confidence": 0.0-1.0}}
  }},
  
  "detailed_narrative": "Full analysis with sections...",
  
  "data_quality_notes": [
    "Sample size limitations...",
    "Missing data points..."
  ]
}}"""

        try:
            response = await self.ai_engine.generate(system_prompt, user_message)
            
            # Parse JSON response
            insights = json.loads(response)
            insights["generated_at"] = datetime.utcnow().isoformat()
            insights["ai_model"] = self.ai_engine.get_active_model_name()
            insights["advanced_metrics"] = metrics
            
            return insights
        
        except Exception as e:
            logger.error(f"AI insight generation failed: {e}")
            return self._generate_fallback_insights(context)
    
    def _generate_fallback_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metrics-based insights without AI using advanced metrics"""
        
        # Use advanced metrics directly
        metrics = context.get('advanced_metrics', {})
        
        if not metrics:
            return {
                "overall_score": 50,
                "confidence_in_score": 0.0,
                "hire_recommendation": "maybe",
                "recommendation_confidence": 0.0,
                "behavioral_profile": "Unknown",
                "detailed_narrative": "Insufficient data for analysis. Advanced metrics calculation failed.",
                "generated_at": datetime.utcnow().isoformat(),
                "ai_model": "Fallback (No Data)"
            }
        
        # Extract metric values with confidence
        exploration = metrics.get('exploration', {})
        iteration = metrics.get('iteration', {})
        debugging = metrics.get('debugging', {})
        ai_reliance = metrics.get('ai_reliance', {})
        ai_collab = metrics.get('ai_collaboration', {})
        sql_complexity = metrics.get('sql_complexity', {})
        independence = metrics.get('independence', {})
        
        # Calculate dimension scores (0-100) with confidence
        def to_score_with_confidence(metric_dict: Dict, scale: float = 1.0) -> Dict:
            value = metric_dict.get('value', 0.0)
            confidence = metric_dict.get('confidence', 0.0)
            score = min(100, max(0, int(value * 100 / scale)))
            return {"score": score, "confidence": round(confidence, 2)}
        
        dimension_scores = {
            "problem_understanding": to_score_with_confidence(exploration, 1.0),
            "analytical_thinking": to_score_with_confidence(iteration, 1.0),
            "debugging_ability": to_score_with_confidence(debugging, 1.0),
            "ai_collaboration_quality": to_score_with_confidence(ai_collab, 1.0),
            "sql_complexity": to_score_with_confidence(sql_complexity, 4.0),
            "independence": to_score_with_confidence(independence, 1.0)
        }
        
        # Calculate overall score weighted by confidence
        total_score = 0
        total_weight = 0
        for dim, score_data in dimension_scores.items():
            weight = score_data['confidence']
            total_score += score_data['score'] * weight
            total_weight += weight
        
        overall_score = int(total_score / total_weight) if total_weight > 0 else 50
        overall_confidence = metrics.get('overall_confidence', 0.0)
        
        # Determine behavioral profile
        ai_rel_value = ai_reliance.get('value', 0.5)
        ai_col_value = ai_collab.get('value', 0.5)
        
        if ai_rel_value < 0.3:
            profile = "Independent Thinker"
        elif ai_rel_value < 0.6 and ai_col_value > 0.4:
            profile = "Healthy AI Collaborator"
        else:
            profile = "AI Dependent"
        
        # Generate strengths (high confidence only)
        strengths = []
        if exploration.get('confidence', 0) > 0.5 and exploration.get('value', 0) > 0.4:
            strengths.append({
                "strength": f"Strong data exploration approach ({exploration.get('interpretation')})",
                "confidence": exploration.get('confidence'),
                "evidence": f"ExplorationScore: {exploration.get('value'):.2f}, {exploration.get('sample_size')} observations"
            })
        
        if iteration.get('confidence', 0) > 0.5 and iteration.get('value', 0) > 0.35:
            strengths.append({
                "strength": f"Iterative problem solver ({iteration.get('interpretation')})",
                "confidence": iteration.get('confidence'),
                "evidence": f"IterationScore: {iteration.get('value'):.2f}, {iteration.get('sample_size')} meaningful iterations"
            })
        
        if debugging.get('confidence', 0) > 0.5 and debugging.get('value', 0) > 0.65:
            strengths.append({
                "strength": f"Effective debugging ({debugging.get('interpretation')})",
                "confidence": debugging.get('confidence'),
                "evidence": f"DebugScore: {debugging.get('value'):.2f}, {debugging.get('sample_size')} error encounters"
            })
        
        if sql_complexity.get('value', 0) > 2.5:
            strengths.append({
                "strength": f"Advanced SQL capability ({sql_complexity.get('interpretation')})",
                "confidence": sql_complexity.get('confidence'),
                "evidence": f"SQL Complexity: {sql_complexity.get('value'):.2f}, {sql_complexity.get('sample_size')} queries analyzed"
            })
        
        # Generate concerns
        concerns = []
        if ai_reliance.get('confidence', 0) > 0.5 and ai_rel_value > 0.6:
            concerns.append({
                "concern": f"High AI dependency ({ai_reliance.get('interpretation')})",
                "confidence": ai_reliance.get('confidence'),
                "evidence": f"AI Reliance: {ai_rel_value:.2f}, {ai_reliance.get('sample_size')} AI interactions"
            })
        
        if exploration.get('confidence', 0) > 0.5 and exploration.get('value', 0) < 0.15:
            concerns.append({
                "concern": f"Limited data exploration ({exploration.get('interpretation')})",
                "confidence": exploration.get('confidence'),
                "evidence": f"ExplorationScore: {exploration.get('value'):.2f}"
            })
        
        if debugging.get('confidence', 0) > 0.5 and debugging.get('value', 0) < 0.35:
            concerns.append({
                "concern": f"Struggles with debugging ({debugging.get('interpretation')})",
                "confidence": debugging.get('confidence'),
                "evidence": f"DebugScore: {debugging.get('value'):.2f}"
            })
        
        # Check for low confidence issues
        data_quality_notes = []
        if overall_confidence < 0.4:
            data_quality_notes.append(f"Overall analysis confidence is low ({overall_confidence:.2f}) - limited sample size")
        
        for metric_name, metric_data in metrics.items():
            if isinstance(metric_data, dict) and metric_data.get('confidence', 1.0) < 0.3:
                data_quality_notes.append(
                    f"{metric_name}: Low confidence ({metric_data.get('confidence'):.2f}) "
                    f"due to small sample ({metric_data.get('sample_size', 0)} observations)"
                )
        
        # Recommendation
        if overall_score >= 80 and overall_confidence > 0.6:
            recommendation = "strong_yes"
            rec_confidence = overall_confidence
        elif overall_score >= 70 and overall_confidence > 0.5:
            recommendation = "yes"
            rec_confidence = overall_confidence
        elif overall_score >= 50:
            recommendation = "maybe"
            rec_confidence = overall_confidence * 0.8
        elif overall_score >= 30:
            recommendation = "no"
            rec_confidence = overall_confidence
        else:
            recommendation = "strong_no"
            rec_confidence = overall_confidence
        
        # If confidence is very low, downgrade to "maybe"
        if overall_confidence < 0.4 and recommendation in ["strong_yes", "yes", "strong_no", "no"]:
            recommendation = "maybe"
            rec_confidence = overall_confidence
        
        # Generate narrative
        narrative = f"""**Metrics-Based Analysis (AI unavailable)**

**Candidate Summary:**
Behavioral Profile: {profile}
Overall Confidence: {overall_confidence:.2f} / 1.0

**Problem-Solving Approach:**
• Exploration: {exploration.get('interpretation', 'unknown')} (score: {exploration.get('value', 0):.2f}, confidence: {exploration.get('confidence', 0):.2f})
• Iteration: {iteration.get('interpretation', 'unknown')} (score: {iteration.get('value', 0):.2f}, confidence: {iteration.get('confidence', 0):.2f})

**Technical Capability:**
• SQL Complexity: {sql_complexity.get('interpretation', 'unknown')} (score: {sql_complexity.get('value', 0):.2f}, confidence: {sql_complexity.get('confidence', 0):.2f})
• Debugging: {debugging.get('interpretation', 'unknown')} (score: {debugging.get('value', 0):.2f}, confidence: {debugging.get('confidence', 0):.2f})

**AI Usage:**
• Profile: {profile}
• Reliance: {ai_reliance.get('value', 0):.2f} ({ai_reliance.get('interpretation', 'unknown')})
• Collaboration Quality: {ai_collab.get('value', 0):.2f} ({ai_collab.get('interpretation', 'unknown')})
• Intent Breakdown: {json.dumps(metrics.get('ai_intent_breakdown', {}), indent=2)}

**Thinking Sequences Detected:**
{json.dumps(metrics.get('thinking_sequences', []), indent=2)}

**Data Quality:**
{chr(10).join('• ' + note for note in data_quality_notes) if data_quality_notes else '• Sufficient data for analysis'}

**Recommendation:**
{recommendation.upper()} (confidence: {rec_confidence:.2f})
"""
        
        return {
            "overall_score": overall_score,
            "confidence_in_score": round(overall_confidence, 2),
            "hire_recommendation": recommendation,
            "recommendation_confidence": round(rec_confidence, 2),
            "behavioral_profile": profile,
            "key_strengths": strengths,
            "concerns": concerns,
            "dimension_scores": dimension_scores,
            "detailed_narrative": narrative,
            "data_quality_notes": data_quality_notes,
            "advanced_metrics": metrics,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_model": "Fallback (Advanced Metrics)"
        }


# Global analyzer instance
_analyzer: Optional[BehaviorAnalyzer] = None


def get_analyzer() -> BehaviorAnalyzer:
    """Get global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = BehaviorAnalyzer()
    return _analyzer
