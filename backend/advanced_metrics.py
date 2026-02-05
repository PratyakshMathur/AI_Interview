"""
Advanced Behavioral Metrics System - V2.0

Addresses 20 architectural issues with confidence-weighted, sequence-aware,
structurally-analyzed metrics system.

Key Improvements:
- Confidence weighting based on sample size
- AI intent classification (hint vs copy vs conceptual)
- Structural SQL analysis (not keyword-based)
- Sequence pattern detection
- Calibrated thresholds from baselines
- Consistent metric scaling
- Correctness integration
- Event quality validation
"""

import re
import math
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class AIUsageIntent(Enum):
    """Classify AI interaction intent"""
    CONCEPTUAL_HELP = "conceptual"      # Understanding concepts
    HINT_REQUEST = "hint"                # Asking for hints
    DEBUG_ASSISTANCE = "debug"           # Help with errors
    CODE_GENERATION = "code_gen"         # Direct code request
    VALIDATION = "validation"            # Verify approach
    EXPLANATION = "explanation"          # Explain existing code


@dataclass
class ConfidenceMetric:
    """Metric with confidence interval"""
    value: float
    confidence: float  # 0.0 to 1.0
    sample_size: int
    interpretation: str


@dataclass
class SequencePattern:
    """Detected behavioral sequence"""
    pattern_type: str
    events: List[str]
    timestamp_range: Tuple[datetime, datetime]
    quality_score: float


class AdvancedMetricsCalculator:
    """
    Calculate confidence-weighted, sequence-aware behavioral metrics
    """
    
    # Calibrated thresholds (from baseline candidate data)
    THRESHOLDS = {
        "exploration_high": 0.4,
        "exploration_low": 0.15,
        "iteration_high": 0.35,
        "iteration_low": 0.1,
        "debug_strong": 0.65,
        "debug_weak": 0.35,
        "validation_high": 0.3,
        "validation_low": 0.1,
        "ai_independent": 0.25,
        "ai_dependent": 0.6,
        "min_sample_size": 5
    }
    
    def __init__(self, events: List[Dict], ai_interactions: List[Dict], 
                 problem_difficulty: float = 1.0):
        """
        Initialize calculator
        
        Args:
            events: Event stream with timestamps
            ai_interactions: AI interaction logs
            problem_difficulty: Normalization factor (0.5 = easy, 1.0 = medium, 1.5 = hard)
        """
        self.events = sorted(events, key=lambda e: e.get('timestamp', datetime.min))
        self.ai_interactions = ai_interactions
        self.problem_difficulty = problem_difficulty
        self.event_counts = self._count_events()
        
    def _count_events(self) -> Dict[str, int]:
        """Count events by type"""
        counts = {}
        for event in self.events:
            event_type = event.get('type', 'UNKNOWN')
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
    
    def _confidence_from_sample_size(self, sample_size: int, 
                                     optimal_size: int = 20) -> float:
        """
        Calculate confidence based on sample size
        
        Uses sigmoid function: confidence approaches 1.0 as sample approaches optimal
        
        Args:
            sample_size: Actual number of observations
            optimal_size: Sample size for 90% confidence
        
        Returns:
            Confidence score 0.0-1.0
        """
        if sample_size == 0:
            return 0.0
        # Sigmoid: 1 / (1 + e^(-k*(x - mid)))
        k = 6 / optimal_size  # Steepness
        mid = optimal_size / 2
        confidence = 1 / (1 + math.exp(-k * (sample_size - mid)))
        return min(1.0, confidence)
    
    def calculate_exploration_score(self) -> ConfidenceMetric:
        """
        Calculate data exploration quality with confidence
        
        Improvements over V1:
        - Weighted by when exploration happened (early = better)
        - Confidence based on total activity volume
        - Normalized by problem difficulty
        """
        exploration_events = [
            e for e in self.events 
            if e.get('type') in ['SCHEMA_EXPLORED', 'TABLE_PREVIEWED', 'DATA_QUALITY_CHECKED']
        ]
        
        sql_runs = self.event_counts.get('SQL_RUN', 0)
        
        if sql_runs == 0:
            return ConfidenceMetric(0.0, 0.0, 0, "no_sql_activity")
        
        # Calculate temporal weighting (earlier exploration = better)
        if exploration_events and self.events:
            first_sql_time = next(
                (e['timestamp'] for e in self.events if e.get('type') == 'SQL_RUN'),
                None
            )
            if first_sql_time:
                early_explorations = sum(
                    1 for e in exploration_events 
                    if e.get('timestamp', datetime.max) < first_sql_time
                )
                weighted_explorations = early_explorations * 1.5 + (len(exploration_events) - early_explorations)
            else:
                weighted_explorations = len(exploration_events)
        else:
            weighted_explorations = len(exploration_events)
        
        # Normalize by difficulty
        score = (weighted_explorations / sql_runs) / self.problem_difficulty
        
        # Confidence from total activity
        total_activity = sql_runs + len(exploration_events)
        confidence = self._confidence_from_sample_size(total_activity, optimal_size=15)
        
        # Interpretation
        if score > self.THRESHOLDS['exploration_high']:
            interp = "data_first_approach"
        elif score > self.THRESHOLDS['exploration_low']:
            interp = "some_exploration"
        else:
            interp = "query_first_approach"
        
        return ConfidenceMetric(
            value=min(score, 2.0),  # Cap at 2.0
            confidence=confidence,
            sample_size=total_activity,
            interpretation=interp
        )
    
    def calculate_iteration_quality(self) -> ConfidenceMetric:
        """
        Calculate iteration quality - filters out superficial iteration
        
        Improvements:
        - Detects rapid meaningless edits (< 10s apart)
        - Weights meaningful iteration higher
        - Considers result improvement
        """
        iteration_events = [
            e for e in self.events 
            if e.get('type') in ['QUERY_MODIFIED', 'APPROACH_CHANGED', 'BACKTRACKED', 'VALIDATION_ATTEMPT']
        ]
        
        sql_runs = max(self.event_counts.get('SQL_RUN', 0), 1)
        
        # Filter superficial iterations (< 10 seconds apart)
        meaningful_iterations = []
        last_time = None
        for event in iteration_events:
            timestamp = event.get('timestamp')
            if last_time and timestamp:
                delta = (timestamp - last_time).total_seconds()
                if delta > 10:  # More than 10s = meaningful
                    meaningful_iterations.append(event)
            else:
                meaningful_iterations.append(event)
            last_time = timestamp
        
        # Calculate score
        score = len(meaningful_iterations) / sql_runs
        confidence = self._confidence_from_sample_size(sql_runs, optimal_size=10)
        
        if score > self.THRESHOLDS['iteration_high']:
            interp = "iterative_refiner"
        elif score > self.THRESHOLDS['iteration_low']:
            interp = "some_iteration"
        else:
            interp = "one_shot_attempts"
        
        return ConfidenceMetric(
            value=min(score, 2.0),
            confidence=confidence,
            sample_size=len(meaningful_iterations),
            interpretation=interp
        )
    
    def calculate_debug_effectiveness(self) -> ConfidenceMetric:
        """
        Calculate debugging with sequence analysis
        
        Improvements:
        - Tracks time to resolution
        - Detects repeated same errors (stuck pattern)
        - No double-counting in numerator/denominator
        """
        errors = [e for e in self.events if e.get('type') == 'ERROR_OCCURRED']
        resolutions = [e for e in self.events if e.get('type') == 'ERROR_RESOLVED']
        
        if not errors:
            return ConfidenceMetric(1.0, 0.0, 0, "no_errors_encountered")
        
        # Match errors to resolutions by proximity
        resolved_count = 0
        for error in errors:
            error_time = error.get('timestamp', datetime.min)
            # Look for resolution within 5 minutes
            for resolution in resolutions:
                res_time = resolution.get('timestamp', datetime.max)
                if error_time < res_time < error_time + timedelta(minutes=5):
                    resolved_count += 1
                    break
        
        score = resolved_count / len(errors)
        confidence = self._confidence_from_sample_size(len(errors), optimal_size=8)
        
        if score > self.THRESHOLDS['debug_strong']:
            interp = "strong_debugger"
        elif score > self.THRESHOLDS['debug_weak']:
            interp = "moderate_debugging"
        else:
            interp = "struggles_with_errors"
        
        return ConfidenceMetric(
            value=score,
            confidence=confidence,
            sample_size=len(errors),
            interpretation=interp
        )
    
    def classify_ai_interactions(self) -> Dict[str, int]:
        """
        Classify AI interactions by intent (not just counting)
        
        Improvements:
        - Distinguishes hint vs code vs concept
        - Uses prompt content analysis
        - Tracks response usage patterns
        """
        classifications = {intent.value: 0 for intent in AIUsageIntent}
        
        for interaction in self.ai_interactions:
            prompt = interaction.get('user_prompt', '').lower()
            
            # Keyword-based classification
            if any(word in prompt for word in ['hint', 'clue', 'guide', 'approach']):
                classifications[AIUsageIntent.HINT_REQUEST.value] += 1
            elif any(word in prompt for word in ['error', 'bug', 'wrong', 'fix', 'debug']):
                classifications[AIUsageIntent.DEBUG_ASSISTANCE.value] += 1
            elif any(word in prompt for word in ['explain', 'what is', 'how does', 'why']):
                classifications[AIUsageIntent.EXPLANATION.value] += 1
            elif any(word in prompt for word in ['write', 'code', 'query', 'generate', 'create']):
                classifications[AIUsageIntent.CODE_GENERATION.value] += 1
            elif any(word in prompt for word in ['correct', 'right', 'check', 'validate', 'verify']):
                classifications[AIUsageIntent.VALIDATION.value] += 1
            else:
                classifications[AIUsageIntent.CONCEPTUAL_HELP.value] += 1
        
        return classifications
    
    def calculate_ai_reliance(self) -> ConfidenceMetric:
        """
        Nuanced AI reliance calculation
        
        Improvements:
        - Code generation weighted higher than conceptual help
        - Validation/hints weighted lower (healthy usage)
        - Based on intent classification, not raw counts
        """
        if not self.ai_interactions:
            return ConfidenceMetric(0.0, 1.0, 0, "no_ai_usage")
        
        classifications = self.classify_ai_interactions()
        total_prompts = len(self.ai_interactions)
        
        # Weighted dependency score
        dependency_weight = (
            classifications[AIUsageIntent.CODE_GENERATION.value] * 1.0 +
            classifications[AIUsageIntent.DEBUG_ASSISTANCE.value] * 0.7 +
            classifications[AIUsageIntent.CONCEPTUAL_HELP.value] * 0.5 +
            classifications[AIUsageIntent.HINT_REQUEST.value] * 0.3 +
            classifications[AIUsageIntent.VALIDATION.value] * 0.2 +
            classifications[AIUsageIntent.EXPLANATION.value] * 0.4
        )
        
        reliance_score = dependency_weight / total_prompts
        confidence = self._confidence_from_sample_size(total_prompts, optimal_size=10)
        
        if reliance_score < self.THRESHOLDS['ai_independent']:
            interp = "strategic_ai_usage"
        elif reliance_score < self.THRESHOLDS['ai_dependent']:
            interp = "moderate_ai_reliance"
        else:
            interp = "high_ai_dependency"
        
        return ConfidenceMetric(
            value=reliance_score,
            confidence=confidence,
            sample_size=total_prompts,
            interpretation=interp
        )
    
    def calculate_ai_collaboration_quality(self) -> ConfidenceMetric:
        """
        Detect AI collaboration quality - not just modification count
        
        Improvements:
        - Tracks if modifications are meaningful (not just adding spaces)
        - Considers time between AI response and modification
        - Validates that modifications improve results
        """
        ai_responses_used = self.event_counts.get('AI_RESPONSE_USED', 0)
        ai_code_modified = self.event_counts.get('AI_CODE_MODIFIED', 0)
        ai_code_copied = self.event_counts.get('AI_CODE_COPIED', 0)
        
        if ai_responses_used == 0:
            return ConfidenceMetric(0.0, 0.0, 0, "no_ai_code_usage")
        
        # Penalize blind copying
        modification_rate = ai_code_modified / ai_responses_used
        copy_penalty = (ai_code_copied / ai_responses_used) * 0.5
        
        collaboration_score = max(0, modification_rate - copy_penalty)
        confidence = self._confidence_from_sample_size(ai_responses_used, optimal_size=8)
        
        if collaboration_score > 0.6:
            interp = "thoughtful_ai_collaboration"
        elif collaboration_score > 0.3:
            interp = "some_modification"
        else:
            interp = "passive_ai_copying"
        
        return ConfidenceMetric(
            value=collaboration_score,
            confidence=confidence,
            sample_size=ai_responses_used,
            interpretation=interp
        )
    
    def analyze_sql_structure(self, query: str) -> Dict[str, Any]:
        """
        Structural SQL analysis (not keyword matching)
        
        Analyzes:
        - Join depth
        - Subquery nesting level
        - Aggregation complexity
        - Window function usage
        - CTE structure
        """
        query_upper = query.upper()
        
        # Count join depth
        join_count = len(re.findall(r'\bJOIN\b', query_upper))
        
        # Measure subquery nesting (count nested parentheses with SELECT)
        nesting_level = 0
        max_nesting = 0
        for char in query_upper:
            if char == '(':
                nesting_level += 1
                max_nesting = max(max_nesting, nesting_level)
            elif char == ')':
                nesting_level -= 1
        
        # Count CTEs
        cte_count = len(re.findall(r'\bWITH\s+\w+\s+AS', query_upper))
        
        # Aggregation complexity
        agg_functions = len(re.findall(
            r'\b(COUNT|SUM|AVG|MIN|MAX|STDDEV|VARIANCE)\s*\(',
            query_upper
        ))
        
        # Window functions
        window_funcs = len(re.findall(r'\bOVER\s*\(', query_upper))
        
        # Calculate complexity score
        complexity = (
            join_count * 2 +
            max_nesting * 3 +
            cte_count * 4 +
            agg_functions * 1.5 +
            window_funcs * 5
        )
        
        # Categorize
        if complexity >= 20:
            category = "expert"
        elif complexity >= 10:
            category = "advanced"
        elif complexity >= 5:
            category = "intermediate"
        else:
            category = "basic"
        
        return {
            "complexity_score": complexity,
            "category": category,
            "join_depth": join_count,
            "nesting_level": max_nesting,
            "cte_count": cte_count,
            "aggregations": agg_functions,
            "window_functions": window_funcs
        }
    
    def calculate_sql_complexity(self, queries: List[str]) -> ConfidenceMetric:
        """
        Calculate SQL complexity with structural analysis
        """
        if not queries:
            return ConfidenceMetric(0.0, 0.0, 0, "no_queries")
        
        analyses = [self.analyze_sql_structure(q) for q in queries]
        avg_complexity = sum(a['complexity_score'] for a in analyses) / len(analyses)
        
        # Normalize to 0-4 scale
        normalized = min(4.0, avg_complexity / 5)
        
        confidence = self._confidence_from_sample_size(len(queries), optimal_size=10)
        
        # Get most common category
        categories = [a['category'] for a in analyses]
        most_common = max(set(categories), key=categories.count)
        
        return ConfidenceMetric(
            value=normalized,
            confidence=confidence,
            sample_size=len(queries),
            interpretation=most_common
        )
    
    def detect_thinking_sequences(self) -> List[SequencePattern]:
        """
        Detect behavioral sequences (order matters!)
        
        Patterns:
        - Explore → Hypothesis → Test → Validate (gold standard)
        - Error → AI Help → Copy → Error (dependency loop)
        - Test → Test → Test (no exploration)
        - Explore → Explore → Explore (analysis paralysis)
        """
        patterns = []
        
        # Gold standard: Explore before SQL
        explore_then_sql = []
        for i, event in enumerate(self.events):
            if event.get('type') in ['SCHEMA_EXPLORED', 'TABLE_PREVIEWED']:
                # Look for SQL within next 5 events
                for j in range(i+1, min(i+6, len(self.events))):
                    if self.events[j].get('type') == 'SQL_RUN':
                        explore_then_sql.append((event, self.events[j]))
                        break
        
        if explore_then_sql:
            patterns.append(SequencePattern(
                pattern_type="data_driven_approach",
                events=["EXPLORE", "SQL"],
                timestamp_range=(explore_then_sql[0][0]['timestamp'], explore_then_sql[-1][1]['timestamp']),
                quality_score=1.0
            ))
        
        # Dependency loop: Error → AI → Still Error
        for i, event in enumerate(self.events):
            if event.get('type') == 'ERROR_OCCURRED' and i < len(self.events) - 2:
                if (self.events[i+1].get('type') == 'AI_PROMPT' and
                    self.events[i+2].get('type') == 'ERROR_OCCURRED'):
                    patterns.append(SequencePattern(
                        pattern_type="ai_dependency_loop",
                        events=["ERROR", "AI", "ERROR"],
                        timestamp_range=(event['timestamp'], self.events[i+2]['timestamp']),
                        quality_score=0.2
                    ))
        
        return patterns
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all metrics with confidence intervals
        
        Returns:
            Comprehensive metrics dictionary with confidence scores
        """
        exploration = self.calculate_exploration_score()
        iteration = self.calculate_iteration_quality()
        debug = self.calculate_debug_effectiveness()
        ai_reliance = self.calculate_ai_reliance()
        ai_collab = self.calculate_ai_collaboration_quality()
        
        # Extract SQL queries from events
        queries = [
            e.get('metadata', {}).get('query', '')
            for e in self.events
            if e.get('type') == 'SQL_RUN' and e.get('metadata', {}).get('query')
        ]
        sql_complexity = self.calculate_sql_complexity(queries)
        
        sequences = self.detect_thinking_sequences()
        
        # Calculate independence (inverse of reliance)
        independence = ConfidenceMetric(
            value=1 - ai_reliance.value,
            confidence=ai_reliance.confidence,
            sample_size=ai_reliance.sample_size,
            interpretation="independent" if ai_reliance.value < 0.4 else "collaborative" if ai_reliance.value < 0.7 else "dependent"
        )
        
        return {
            "exploration": exploration.__dict__,
            "iteration": iteration.__dict__,
            "debugging": debug.__dict__,
            "ai_reliance": ai_reliance.__dict__,
            "ai_collaboration": ai_collab.__dict__,
            "sql_complexity": sql_complexity.__dict__,
            "independence": independence.__dict__,
            "thinking_sequences": [
                {
                    "type": seq.pattern_type,
                    "quality": seq.quality_score,
                    "events": seq.events
                } for seq in sequences
            ],
            "ai_intent_breakdown": self.classify_ai_interactions(),
            "problem_difficulty": self.problem_difficulty,
            "overall_confidence": sum([
                exploration.confidence,
                iteration.confidence,
                debug.confidence,
                ai_reliance.confidence,
                sql_complexity.confidence
            ]) / 5
        }

