"""
LLM Service for structured output generation with Pydantic validation.
Provides abstraction layer for LLM interactions with multiple providers.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_ollama.llms import OllamaLLM
from config.config import get_config


class ModelConfig:
    """Configuration for LLM model"""
    def __init__(
        self,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0
    ):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty


class LLMResponse(BaseModel):
    """Standardized LLM response"""
    success: bool
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class LLMService:
    """Service for LLM interactions with structured outputs"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        self._models: Dict[str, BaseLanguageModel] = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize available LLM models"""
        try:
            llm_config = self.config.llm_config
            provider = self.config.llm_provider
            
            if provider == "deepseek":
                deepseek_config = llm_config.get("deepseek", {})
                self._models["deepseek"] = ChatOpenAI(
                    api_key=deepseek_config.get("api_key"),
                    base_url=deepseek_config.get("api_url"),
                    model=deepseek_config.get("model", "deepseek-chat"),
                    temperature=0.1,
                    max_tokens=4000
                )
                self.logger.info("Initialized DeepSeek model")
            
            elif provider == "ollama":
                ollama_config = llm_config.get("ollama", {})
                self._models["ollama"] = OllamaLLM(
                    base_url=ollama_config.get("base_url"),
                    model=ollama_config.get("model", "gpt-oss:20b"),
                    temperature=0.1
                )
                self.logger.info("Initialized Ollama model")
            
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM models: {e}")
            raise
    
    def get_model(self, provider: Optional[str] = None) -> BaseLanguageModel:
        """Get LLM model instance"""
        if provider is None:
            provider = self.config.get_llm_provider()
        
        if provider not in self._models:
            raise ValueError(f"Model provider '{provider}' not available")
        
        return self._models[provider]
    
    async def generate_structured_output(
        self,
        prompt_template: str,
        output_schema: Type[BaseModel],
        context: Dict[str, Any],
        model_config: Optional[ModelConfig] = None,
        provider: Optional[str] = None
    ) -> BaseModel:
        """
        Generate structured output conforming to Pydantic schema
        
        Args:
            prompt_template: Jinja2 template for prompt
            output_schema: Pydantic model class for output validation
            context: Variables for prompt template
            model_config: Optional model configuration overrides
            provider: Optional model provider override
            
        Returns:
            Validated instance of output_schema
        """
        try:
            # Format prompt with context
            formatted_prompt = self._format_prompt(prompt_template, context)
            
            # Get model
            model = self.get_model(provider)
            
            # Create messages
            system_prompt = self._create_system_prompt(output_schema)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=formatted_prompt)
            ]
            
            # Generate response
            response = await model.ainvoke(messages, config={"callbacks": [get_config().langfuse_handler]})
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response
            try:
                json_data = json.loads(content)
            except json.JSONDecodeError as e:
                # Try to extract JSON from response
                json_data = self._extract_json_from_response(content)
            
            # Validate with Pydantic schema
            validated_data = output_schema(**json_data)
            
            self.logger.debug(f"Generated structured output: {validated_data}")
            return validated_data
            
        except ValidationError as e:
            self.logger.error(f"Pydantic validation failed: {e}")
            raise ValueError(f"Generated data doesn't match schema: {e}")
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            raise
    
    async def generate_text(
        self,
        prompt_template: str,
        context: Dict[str, Any],
        model_config: Optional[ModelConfig] = None,
        provider: Optional[str] = None
    ) -> LLMResponse:
        """Generate free-form text response"""
        try:
            # Format prompt with context
            formatted_prompt = self._format_prompt(prompt_template, context)
            
            # Get model
            model = self.get_model(provider)
            
            # Generate response
            response = await model.ainvoke([HumanMessage(content=formatted_prompt)], config={"callbacks": [get_config().langfuse_handler]})
            content = response.content if hasattr(response, 'content') else str(response)
            
            return LLMResponse(
                success=True,
                content=content,
                usage=getattr(response, 'usage_metadata', None)
            )
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return LLMResponse(
                success=False,
                content="",
                error=str(e)
            )
    
    async def analyze_sentiment(
        self,
        text: str,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment for escalation detection"""
        prompt = f"""
        Analyze the sentiment of the following text and classify it as one of: positive, neutral, negative, frustrated, confused.
        
        Text: "{text}"
        
        Respond with JSON in this format:
        {{
            "sentiment": "classification",
            "confidence": 0.0-1.0,
            "indicators": ["list", "of", "indicators"],
            "escalation_risk": "low|medium|high"
        }}
        """
        
        try:
            response = await self.generate_text(prompt, {})
            if response.success:
                return json.loads(response.content)
            else:
                return {"sentiment": "neutral", "confidence": 0.5, "escalation_risk": "low"}
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            return {"sentiment": "neutral", "confidence": 0.5, "escalation_risk": "low"}
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all configured LLM providers"""
        status = {}
        for provider, model in self._models.items():
            try:
                # Basic health check
                status[provider] = {
                    "available": True,
                    "model_type": type(model).__name__,
                    "config": getattr(model, 'model_kwargs', {})
                }
            except Exception as e:
                status[provider] = {
                    "available": False,
                    "error": str(e)
                }
        return status
    
    def _format_prompt(self, template: str, context: Dict[str, Any]) -> str:
        """Format prompt template with context variables"""
        try:
            return template.format(**context)
        except KeyError as e:
            self.logger.error(f"Missing context variable: {e}")
            raise ValueError(f"Missing required context variable: {e}")
    
    def _create_system_prompt(self, output_schema: Type[BaseModel]) -> str:
        """Create system prompt for structured output generation"""
        schema_name = output_schema.__name__
        schema_fields = output_schema.model_fields
        
        field_descriptions = []
        for field_name, field_info in schema_fields.items():
            field_type = field_info.annotation
            description = field_info.description or f"Field {field_name}"
            field_descriptions.append(f"- {field_name}: {description} (type: {field_type})")
        
        return f"""
        You are an AI assistant that generates structured data. 
        
        You must respond with valid JSON that matches the {schema_name} schema exactly.
        
        Schema fields:
        {chr(10).join(field_descriptions)}
        
        Rules:
        1. Always respond with valid JSON
        2. Include all required fields
        3. Use correct data types
        4. Follow the field descriptions precisely
        5. If a field is optional and not provided, omit it from the JSON
        6. Do not include any text outside the JSON response
        """
    
    def _extract_json_from_response(self, content: str) -> Dict[str, Any]:
        """Extract JSON from LLM response that might contain extra text"""
        import re
        
        # Try to find JSON in the response
        json_pattern = r'\{.*\}'
        matches = re.findall(json_pattern, content, re.DOTALL)
        
        if matches:
            # Try the largest match first
            for match in sorted(matches, key=len, reverse=True):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError("No valid JSON found in response")


# Global instance
_llm_service: Optional[LLMService] = None

def get_llm_service() -> LLMService:
    """Get global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
