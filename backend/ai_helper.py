"""
AI Helper - Candidate-facing AI assistant with coding and interview modes.
Uses LangChain with Gemini for intelligent, context-aware responses.
"""

from typing import Dict, Any, Optional, List
from langchain_config import get_ai_engine
import logging

logger = logging.getLogger(__name__)


class AIHelper:
    """AI Assistant helper using Gemini via LangChain"""
    
    def __init__(self):
        self.ai_engine = None
        try:
            self.ai_engine = get_ai_engine()
        except Exception as e:
            logger.warning(f"AI engine not initialized for AIHelper: {e}")
        
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    def _get_coding_system_prompt(self, schema_info: Optional[Dict] = None, problem_context: Optional[Dict] = None) -> str:
        """System prompt for coding assistance mode"""
        schema_text = ""
        if schema_info:
            schema_text = f"\n\nAvailable Tables:\n{schema_info}"
        
        problem_text = ""
        if problem_context:
            problem_text = "\n\nProblem Context:"
            if problem_context.get('title'):
                problem_text += f"\nTitle: {problem_context['title']}"
            if problem_context.get('description'):
                problem_text += f"\nDescription: {problem_context['description']}"
            if problem_context.get('tables'):
                problem_text += "\n\nTables Available:"
                for table in problem_context['tables']:
                    problem_text += f"\n- {table['name']} ({table.get('row_count', '?')} rows)"
                    if table.get('schema'):
                        # Schema might be dict or list
                        if isinstance(table['schema'], dict):
                            columns = ', '.join(table['schema'].keys())
                        elif isinstance(table['schema'], list):
                            columns = ', '.join([str(c) for c in table['schema']])
                        else:
                            columns = str(table['schema'])
                        problem_text += f"\n  Columns: {columns}"
        
        return f"""You are an AI assistant helping a candidate in a SQL coding interview.{schema_text}{problem_text}

IMPORTANT RULES:
1. You can EXPLAIN SQL concepts and syntax
2. You can GUIDE their thinking process
3. You can SUGGEST approaches and query structures
4. You can HELP DEBUG errors
5. You CANNOT write complete solutions
6. You CANNOT provide full working queries
7. Always encourage independent problem-solving

Your responses should:
- Be concise (2-4 sentences max)
- Ask clarifying questions
- Provide hints, not answers
- Explain errors clearly
- Suggest SQL syntax when needed
- Encourage best practices
- Help them learn, not copy

Example Good Response:
"To find the top customers, you'll want to use GROUP BY on customer_id and COUNT() or SUM() for their activity. Try ordering the results with ORDER BY DESC and LIMIT. What metric are you using to define 'top'?"

Example Bad Response:
"Here's the query: SELECT customer_id, COUNT(*) as orders FROM orders GROUP BY customer_id ORDER BY orders DESC LIMIT 5"

Remember: This evaluates how they collaborate with AI, not their ability to copy code."""
    
    def _get_interview_system_prompt(self, problem_context: Optional[Dict] = None) -> str:
        """System prompt for interview mode"""
        problem_text = ""
        if problem_context:
            problem_text = "\n\nProblem Context:"
            if problem_context.get('title'):
                problem_text += f"\nProblem: {problem_context['title']}"
            if problem_context.get('description'):
                problem_text += f"\nDescription: {problem_context['description']}"
            if problem_context.get('tables'):
                tables_list = ', '.join([t['name'] for t in problem_context['tables']])
                problem_text += f"\nTables Used: {tables_list}"
        
        return f"""You are an AI interviewer conducting a post-coding interview for a data analyst role.{problem_text}

Your task: Ask ONE SHORT follow-up question about their SQL approach and problem-solving.

CRITICAL RULES:
1. Ask ONLY ONE question - never ask multiple questions
2. Keep questions SHORT (1-2 sentences maximum)
3. Focus on ONE specific aspect of their work
4. Don't dig too deep - stay high-level and practical
5. Questions should assess thinking, not demand perfect answers

Question Types (pick ONE):
- "Why did you choose [specific approach]?"
- "What was the most challenging part?"
- "How would you improve this for production?"
- "What patterns did you notice in the data?"
- "What would you do differently next time?"

Your tone: Conversational, encouraging, curious (not interrogating)

Example GOOD questions:
- "Why did you use a LEFT JOIN instead of INNER JOIN here?"
- "What was your strategy for handling the date calculations?"
- "How would this query perform with millions of rows?"

Example BAD questions:
- "Walk me through your thought process. Also, what patterns did you see? And how would you optimize it?" (TOO LONG, MULTIPLE QUESTIONS)
- "Explain in detail every decision you made in your query structure." (TOO VAGUE, TOO DEMANDING)

Remember: ONE short, specific question. No follow-ups. No multi-part questions."""
    
    async def process_prompt(
        self, 
        user_prompt: str, 
        context_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        mode: str = "coding",
        problem_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process user prompt with context-aware AI
        
        Args:
            user_prompt: User's question
            context_data: Additional context (code, errors, schema)
            session_id: Session ID for conversation history
            mode: 'coding' or 'interview'
            problem_context: Problem details (title, description, tables)
        
        Returns:
            AI response
        """
        if not self.ai_engine:
            return "AI service temporarily unavailable. Please try again."
        
        # Get appropriate system prompt
        if mode == "interview":
            system_prompt = self._get_interview_system_prompt(problem_context)
        else:
            schema_info = context_data.get("schema") if context_data else None
            system_prompt = self._get_coding_system_prompt(schema_info, problem_context)
        
        # Build enhanced user message with context
        enhanced_message = self._build_context_message(user_prompt, context_data)
        
        # Get conversation history for this session
        history = self.conversation_history.get(session_id, []) if session_id else None
        
        try:
            # Generate response
            logger.info(f"🔍 AI Helper calling engine: mode={mode}, session={session_id}, prompt_len={len(user_prompt)}")
            response = await self.ai_engine.generate(
                system_prompt=system_prompt,
                user_message=enhanced_message,
                conversation_history=history
            )
            logger.info(f"✅ AI Helper got response: {response[:100]}...")
            
            # Update conversation history
            if session_id:
                if session_id not in self.conversation_history:
                    self.conversation_history[session_id] = []
                
                self.conversation_history[session_id].append({
                    "role": "user",
                    "content": user_prompt
                })
                self.conversation_history[session_id].append({
                    "role": "assistant",
                    "content": response
                })
                
                # Keep only last 10 exchanges
                if len(self.conversation_history[session_id]) > 20:
                    self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
            
            return response
        
        except Exception as e:
            logger.error(f"AI Helper error: {e}")
            return "I encountered an error processing your request. Please try rephrasing your question."
    
    def _build_context_message(self, user_prompt: str, context_data: Optional[Dict[str, Any]]) -> str:
        """Build context-enhanced user message"""
        parts = []
        
        if context_data:
            if "code" in context_data and context_data["code"]:
                parts.append(f"Current SQL Query:\n```sql\n{context_data['code']}\n```\n")
            
            if "error" in context_data and context_data["error"]:
                parts.append(f"Error Message:\n{context_data['error']}\n")
            
            if "query_result" in context_data:
                parts.append(f"Query Result: {context_data['query_result']}\n")
        
        parts.append(f"Question: {user_prompt}")
        
        return "\n".join(parts)
    
    async def generate_interview_question(
        self,
        session_id: str,
        query_history: List[str],
        question_number: int = 1,
        problem_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate interview question based on candidate's queries
        
        Args:
            session_id: Session ID
            query_history: List of SQL queries executed
            question_number: Which question number (1-5)
            problem_context: Problem details for context
        
        Returns:
            Interview question (short and focused)
        """
        if not self.ai_engine:
            return "What was your approach to solving this problem?"
        
        system_prompt = self._get_interview_system_prompt(problem_context)
        
        context_text = ""
        if problem_context:
            context_text = f"\nProblem: {problem_context.get('title', 'SQL Analysis Task')}"
        
        # Vary the focus based on question number
        focus_areas = [
            "their overall approach and strategy",
            "a specific SQL technique or JOIN they used",
            "how they would handle edge cases or scale this",
            "what insights or patterns they discovered",
            "what they learned or would do differently"
        ]
        focus = focus_areas[min(question_number - 1, len(focus_areas) - 1)]
        
        user_message = f"""This is question #{question_number} of 5 in the interview.{context_text}

Candidate's Recent SQL Queries:
{chr(10).join([f"{i+1}. {q[:150]}..." for i, q in enumerate(query_history[-3:])])}

Generate ONE SHORT question (1-2 sentences max) focusing on: {focus}

Do not ask multiple questions. Do not ask for detailed explanations. Keep it conversational."""

        try:
            question = await self.ai_engine.generate(
                system_prompt=system_prompt,
                user_message=user_message
            )
            # Truncate if too long (safety check)
            if len(question) > 200:
                question = question[:197] + "..."
            return question
        except Exception as e:
            logger.error(f"Failed to generate interview question: {e}")
            # Generic fallback
            simple_questions = [
                "What was your overall approach to this problem?",
                "Why did you choose that SQL technique?",
                "How would this work with a larger dataset?",
                "What patterns did you notice in the data?",
                "What would you improve if you had more time?"
            ]
            return simple_questions[min(question_number - 1, len(simple_questions) - 1)]
    
    def classify_intent(self, user_prompt: str) -> str:
        """Classify the intent of user's prompt"""
        prompt_lower = user_prompt.lower()
        
        # Intent classification rules
        if any(word in prompt_lower for word in ["what is", "explain", "define", "how does", "concept"]):
            return "CONCEPT_HELP"
        
        elif any(word in prompt_lower for word in ["error", "bug", "debug", "fix", "wrong", "not working"]):
            return "DEBUG_HELP"
        
        elif any(word in prompt_lower for word in ["approach", "strategy", "how to", "method", "technique"]):
            return "APPROACH_HELP"
        
        elif any(word in prompt_lower for word in ["check", "validate", "correct", "verify", "review"]):
            return "VALIDATION"
        
        elif any(word in prompt_lower for word in ["solve", "solution", "answer", "complete", "finish"]):
            return "DIRECT_SOLUTION"
        
        else:
            return "EXPLANATION"
    
    def clear_history(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
