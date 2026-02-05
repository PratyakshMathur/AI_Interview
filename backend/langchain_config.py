"""
LangChain configuration for multi-model AI setup with fallback support.
Supports: Mistral Ollama (primary), Google Gemini (fallback)
"""

import os
from typing import Optional, Dict, Any, List
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import logging

logger = logging.getLogger(__name__)


class MultiModelAI:
    """Multi-model AI with automatic fallback support"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize multi-model AI system
        
        Args:
            gemini_api_key: Google Gemini API key (free tier: 15 RPM)
        """
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.models = []
        self.current_model_index = 0
        
        # Initialize available models
        self._init_models()
    
    def _init_models(self):
        """Initialize AI models in priority order"""
        
        # Get Ollama base URL from environment (for Docker) or use localhost
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # 1. Mistral Ollama (Primary) - Local, fast, free
        try:
            mistral = Ollama(
                model="mistral",
                base_url=ollama_base_url,
                temperature=0.3
            )
            # Test connection
            mistral.invoke("test")
            self.models.append({
                "name": "Mistral (Ollama)",
                "client": mistral,
                "type": "ollama"
            })
            logger.info(f"✅ Mistral Ollama initialized at {ollama_base_url}")
        except Exception as e:
            logger.warning(f"⚠️  Mistral Ollama initialization failed: {e}")
        
        # 2. Google Gemini (Fallback) - Free tier, 1M tokens context
        if self.gemini_api_key:
            try:
                gemini = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=self.gemini_api_key,
                    temperature=0.3,
                    max_tokens=1000
                )
                self.models.append({
                    "name": "Gemini 1.5 Flash",
                    "client": gemini,
                    "type": "gemini"
                })
                logger.info("✅ Gemini 1.5 Flash initialized (fallback)")
            except Exception as e:
                logger.warning(f"⚠️  Gemini initialization failed: {e}")
        
        # Fallback: Log if no models available
        if not self.models:
            logger.error("❌ No AI models available. Install Ollama or set GEMINI_API_KEY")
    
    async def generate(
        self, 
        system_prompt: str, 
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_retries: int = 2
    ) -> str:
        """
        Generate AI response with automatic fallback
        
        Args:
            system_prompt: System instructions for the AI
            user_message: User's question/prompt
            conversation_history: Previous messages (for context)
            max_retries: Number of retries per model
        
        Returns:
            AI generated response
        """
        if not self.models:
            return "AI service unavailable. Please contact support."
        
        # Try each model in order
        for model_idx, model_info in enumerate(self.models):
            logger.info(f"🔍 Trying model: {model_info['name']}")
            for attempt in range(max_retries):
                try:
                    # Build message chain
                    messages = [SystemMessage(content=system_prompt)]
                    
                    # Add conversation history
                    if conversation_history:
                        for msg in conversation_history:
                            if msg["role"] == "user":
                                messages.append(HumanMessage(content=msg["content"]))
                            elif msg["role"] == "assistant":
                                messages.append(AIMessage(content=msg["content"]))
                    
                    # Add current user message
                    messages.append(HumanMessage(content=user_message))
                    
                    logger.info(f"🔍 Invoking {model_info['name']} with {len(messages)} messages")
                    
                    # Generate response (handle different model types)
                    if model_info["type"] == "ollama":
                        # Ollama doesn't use chat format, combine messages
                        full_prompt = f"{system_prompt}\n\nUser: {user_message}"
                        response_text = model_info["client"].invoke(full_prompt)
                        logger.info(f"✅ Response from {model_info['name']}: {response_text[:100]}")
                        return response_text
                    else:
                        # ChatGoogleGenerativeAI uses messages
                        response = model_info["client"].invoke(messages)
                        logger.info(f"✅ Response from {model_info['name']}: {response.content[:100]}")
                        return response.content
                
                except Exception as e:
                    logger.warning(
                        f"⚠️  {model_info['name']} attempt {attempt + 1} failed: {str(e)[:200]}"
                    )
                    
                    # If last attempt with this model, try next model
                    if attempt == max_retries - 1:
                        break
        
        # All models failed
        return "I'm experiencing technical difficulties. Please try again in a moment."
    
    async def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        response_format: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response
        
        Args:
            system_prompt: System instructions
            user_message: User prompt
            response_format: Expected JSON structure
        
        Returns:
            Structured response as dictionary
        """
        # Enhance system prompt with JSON structure
        enhanced_prompt = f"""{system_prompt}

You must respond ONLY with valid JSON matching this structure:
{response_format}

Do not include any explanation outside the JSON. Just the JSON object."""

        response = await self.generate(enhanced_prompt, user_message)
        
        # Try to parse JSON
        try:
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {response[:200]} - Error: {e}")
            return {"error": "Invalid JSON response", "raw": response}
    
    def get_active_model_name(self) -> str:
        """Get name of currently active model"""
        if not self.models:
            return "None"
        return self.models[self.current_model_index]["name"]
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return [m["name"] for m in self.models]


# Global instance (initialized in main.py)
ai_engine: Optional[MultiModelAI] = None


def init_ai_engine(gemini_api_key: Optional[str] = None):
    """Initialize global AI engine"""
    global ai_engine
    ai_engine = MultiModelAI(gemini_api_key=gemini_api_key)
    return ai_engine


def get_ai_engine() -> MultiModelAI:
    """Get global AI engine instance"""
    if ai_engine is None:
        raise RuntimeError("AI engine not initialized. Call init_ai_engine() first.")
    return ai_engine
