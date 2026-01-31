import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from models import AI_INTENT_LABELS

class AIHelper:
    """AI Assistant helper using local Ollama"""
    
    def __init__(self, model_name: str = "mistral", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Controlled system prompt for behavioral evaluation"""
        return """
You are an AI assistant helping candidates in a behavioral interview for data roles.

IMPORTANT RULES:
1. You can EXPLAIN concepts and help debug code
2. You can GUIDE the candidate's thinking process
3. You can SUGGEST approaches and methodologies
4. You CANNOT provide complete solutions
5. You CANNOT write full code implementations
6. Always encourage candidates to think through problems themselves

Your responses should:
- Be concise and helpful
- Ask clarifying questions when needed
- Focus on teaching concepts, not giving answers
- Help identify debugging approaches
- Suggest relevant data analysis techniques

Remember: This is evaluating how candidates collaborate with AI, not testing their ability to copy solutions.
"""
    
    async def process_prompt(self, user_prompt: str, context_data: Optional[Dict[str, Any]] = None) -> str:
        """Process user prompt with Ollama"""
        try:
            # Build context-aware prompt
            full_prompt = self._build_context_prompt(user_prompt, context_data)
            
            # Make request to Ollama
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                }
                
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "Sorry, I couldn't process that request.")
                    else:
                        return "I'm having trouble connecting right now. Please try again."
                        
        except Exception as e:
            print(f"AI Helper error: {e}")
            return "I encountered an error. Please rephrase your question."
    
    def _build_context_prompt(self, user_prompt: str, context_data: Optional[Dict[str, Any]]) -> str:
        """Build context-aware prompt with relevant information"""
        context_parts = [self.system_prompt]
        
        if context_data:
            if "code" in context_data:
                context_parts.append(f"\n\nCandidate's current code:\n```\n{context_data['code']}\n```")
            
            if "error" in context_data:
                context_parts.append(f"\n\nCurrent error:\n{context_data['error']}")
            
            if "data_preview" in context_data:
                context_parts.append(f"\n\nData preview:\n{context_data['data_preview']}")
        
        context_parts.append(f"\n\nCandidate question: {user_prompt}")
        context_parts.append("\n\nYour response:")
        
        return "\n".join(context_parts)
    
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
    
    async def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except:
            return False
    
    async def get_available_models(self) -> list:
        """Get list of available Ollama models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        return [model["name"] for model in result.get("models", [])]
        except:
            return []
        return []