# Behavioral Metrics Analysis Framework

## Overview

The AI Interview system uses a sophisticated **behavioral metrics framework** to analyze candidate performance. This approach goes beyond simple event counting to infer **thinking patterns from behavioral data**.

The framework combines:
- **Behavioral Psychology** - Understanding work patterns
- **Problem-Solving Analysis** - Tracking approach evolution
- **Event-Driven Metrics** - Quantifying behaviors mathematically

---

## Core Philosophy

> **We don't summarize logs. We infer thinking patterns from behavior math.**

Every insight must be backed by:
1. **Quantitative Metric** - A calculated score
2. **Behavioral Evidence** - Patterns observed
3. **Plain Language Explanation** - What it means for hiring

---

## 9 Core Behavioral Metrics

### 1️⃣ Exploration Score

**What it measures:** Whether candidate understood the data before attempting to solve the problem.

**Formula:**
```
ExplorationScore = (SCHEMA_EXPLORED + TABLE_PREVIEWED + DATA_QUALITY_CHECKED) / (SQL_RUN + 1)
```

**Interpretation:**
- **High (> 0.5):** Thinks before querying, examines data structure first
- **Low (< 0.3):** Query-first approach, blind attempts

**Maps to:** Problem Understanding, Data Exploration Skill

---

### 2️⃣ Iteration Quality Score

**What it measures:** Quality of iterative thinking and refinement.

**Formula:**
```
IterationScore = (QUERY_MODIFIED + APPROACH_CHANGED + BACKTRACKED + VALIDATION_ATTEMPT) / SQL_RUN
```

**Interpretation:**
- **High (> 0.3):** Iterative thinker, refines solutions progressively
- **Low (< 0.2):** One-shot attempts, doesn't refine work

**Maps to:** Iterative Thinking, Analytical Thinking

---

### 3️⃣ Debugging Effectiveness

**What it measures:** Ability to resolve errors when encountered.

**Formula:**
```
DebugScore = ERROR_RESOLVED / (ERROR_OCCURRED + 1)
```

**Interpretation:**
- **Strong (> 0.7):** Resolves most errors successfully
- **Weak (< 0.5):** Gets stuck, struggles with debugging

**Maps to:** Debugging Ability, Error Handling

---

### 4️⃣ Analytical Validation Score

**What it measures:** Real analyst mindset - validates results, looks for anomalies.

**Formula:**
```
ValidationScore = (RESULT_VALIDATED + RESULT_COMPARED + OUTLIER_DETECTED + NULL_HANDLED) / (SQL_RUN + 1)
```

**Interpretation:**
- **High (> 0.4):** Analyst mindset, scrutinizes outputs
- **Low (< 0.2):** Accepts results blindly, no validation

**Maps to:** Analytical Thinking, Data Quality Awareness

---

### 5️⃣ SQL Complexity Score

**What it measures:** Query sophistication level.

**Weights:**
- **Basic** (SELECT, FROM, WHERE): 1 point
- **Intermediate** (JOIN, GROUP BY, ORDER BY): 2 points
- **Advanced** (SUBQUERY, UNION, CASE, WITH): 3 points
- **Expert** (WINDOW, PARTITION BY, RECURSIVE): 4 points

**Formula:**
```
SQLComplexity = Σ(QueryComplexityWeights) / TotalQueries
```

**Interpretation:**
- **3.0+:** Expert-level SQL
- **2.0-2.9:** Solid intermediate skills
- **1.0-1.9:** Basic queries only

**Maps to:** Code/Query Quality, Technical Capability

---

### 6️⃣ AI Reliance Ratio

**What it measures:** Dependency on AI assistance.

**Formula:**
```
AIReliance = (AI_CODE_COPIED + AI_RESPONSE_USED) / (AI_PROMPT + 1)
```

**Interpretation:**
- **Low (< 0.4):** Uses AI strategically
- **High (> 0.7):** Heavy dependency

**Maps to:** Independence vs AI Reliance

---

### 7️⃣ AI Collaboration Quality

**What it measures:** Quality of AI usage - thinking WITH AI vs copying FROM AI.

**Formula:**
```
AICollaboration = (AI_CODE_MODIFIED + AI_HINT_REQUESTED + VALIDATION_ATTEMPT) / (AI_RESPONSE_USED + 1)
```

**Interpretation:**
- **High (> 0.5):** Modifies AI suggestions, collaborates thoughtfully
- **Low (< 0.3):** Copies AI responses directly

**Maps to:** Quality of AI Collaboration

---

### 8️⃣ Cognitive Resilience Score

**What it measures:** Ability to recover from errors and setbacks.

**Formula:**
```
Resilience = (ERROR_RESOLVED + APPROACH_CHANGED + BACKTRACKED + BREAKTHROUGH) / (DEAD_END_REACHED + ERROR_OCCURRED + 1)
```

**Interpretation:**
- **High (> 1.0):** Resilient, adapts to challenges
- **Low (< 0.5):** Struggles to recover

**Maps to:** Error Handling, Problem-Solving Adaptability

---

### 9️⃣ Independence Score

**What it measures:** Working autonomously without constant AI help.

**Formula:**
```
Independence = 1 - AIReliance
```

**Interpretation:**
- **High (> 0.7):** Independent thinker
- **Medium (0.4-0.7):** Balanced collaboration
- **Low (< 0.4):** AI dependent

**Maps to:** Independence vs AI Reliance

---

## Behavioral Profiles

Based on `Independence` and `AICollaboration` scores, candidates are classified:

### 🟢 Independent Thinker
- **Independence:** > 0.7
- **Characteristics:** Solves problems autonomously, minimal AI usage
- **Assessment:** Strong independent problem-solver

### 🟡 Healthy AI Collaborator
- **Independence:** 0.4-0.7
- **AICollaboration:** > 0.5
- **Characteristics:** Uses AI strategically, modifies suggestions, thinks critically
- **Assessment:** Modern balanced approach

### 🔴 AI Dependent
- **Independence:** < 0.4
- **AICollaboration:** < 0.5
- **Characteristics:** Heavy reliance on AI, copies without understanding
- **Assessment:** Lacks independent problem-solving ability

---

## Feature Dimensions Mapping

| Recruiter Feature | Derived From Metrics |
|------------------|---------------------|
| Problem Understanding | ExplorationScore |
| Analytical Thinking | ValidationScore + IterationScore |
| Debugging Ability | DebugScore |
| Independence vs AI Reliance | Independence |
| Quality of AI Collaboration | AICollaboration |
| Iterative Thinking | IterationScore |
| Code/Query Quality | SQLComplexity |
| Error Handling | DebugScore + Resilience |
| Data Exploration Skill | ExplorationScore |
| Communication Clarity | INTERVIEW_ANSWER + INSIGHT_SHARED counts |

---

## Analysis Output Structure

The AI Analyzer generates insights in 7 sections:

### SECTION 1: Candidate Summary
Brief overview of working style and behavioral profile.

### SECTION 2: Problem-Solving Behavior
- Uses: ExplorationScore, IterationScore, ValidationScore
- Explains: Approach to understanding and solving problems

### SECTION 3: SQL & Technical Capability
- Uses: SQLComplexity, query evolution patterns
- Explains: Technical skill level and progression

### SECTION 4: AI Usage Assessment
- Uses: AIReliance, AICollaboration, Independence
- Provides: Behavioral profile classification
- Explains: How candidate leverages AI assistance

### SECTION 5: Strength Signals
- Bullet points with metric-based evidence
- Each strength backed by specific behavioral patterns

### SECTION 6: Risk/Concern Signals
- Only included if metrics show weak patterns
- Evidence-based red flags

### SECTION 7: Final Verdict
- Holistic assessment based on combined metric profile
- Hire recommendation with justification

---

## Implementation Details

### Location
- **File:** `backend/ai_analyzer.py`
- **Method:** `_calculate_behavioral_metrics()`
- **System Prompt:** Embedded in `_generate_insights()`

### Event Taxonomy
- **File:** `backend/models.py`
- **Lines:** 85-271
- **Total Events:** 83 types across 10 categories

### AI Model Instructions
The analyzer AI receives:
1. Pre-calculated metrics (not formulas)
2. System prompt with analysis framework
3. Raw event context for verification
4. Instructions to provide behavioral evidence for every insight

### Rules for AI Analysis
1. ❌ Never expose formulas in recruiter-facing output
2. ✅ Use metrics only for reasoning
3. ❌ No event name references (e.g., "SCHEMA_EXPLORED")
4. ❌ No log language
5. ✅ Every insight must have behavioral evidence
6. ✅ Use plain language explanations

---

## Example Analysis Pattern

### ❌ Wrong Approach
"The candidate executed 15 SQL_RUN events and 3 SCHEMA_EXPLORED events."

### ✅ Correct Approach
"The candidate demonstrated a structured, data-first approach.

**Why we believe this:**
- High ExplorationScore (0.67) → examined schema and previewed tables before writing queries
- Strong IterationScore (0.53) → refined queries multiple times instead of one-shot attempts

This indicates thoughtful problem decomposition rather than trial-and-error guessing."

---

## Testing the System

### View Metrics for a Session
The metrics are included in the analysis response under the `metrics` key (when using fallback mode).

### Validate Metric Calculations
Check `raw_counts` in the metrics output to verify event counting.

### Test Different Profiles

**Independent Thinker Test:**
- Many SQL_RUN with few AI_PROMPT
- Should show high Independence score

**AI Dependent Test:**
- Many AI_CODE_COPIED events
- Should show low Independence, low AICollaboration

**Healthy Collaborator Test:**
- Moderate AI_PROMPT with high AI_CODE_MODIFIED
- Should show medium Independence, high AICollaboration

---

## Future Enhancements

Potential metric additions:
- **Time Pressure Score** - Performance under time constraints
- **Communication Quality** - Interview response depth
- **Learning Velocity** - Improvement over session duration
- **Query Efficiency** - Performance optimization awareness

---

## Credits

**Framework Design:** Behavioral psychology + problem-solving analysis + event-driven metrics

**Implementation:** AI Interview System v2.0

**Last Updated:** February 3, 2026
