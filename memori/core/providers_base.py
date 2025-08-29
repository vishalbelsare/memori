"""
Base Provider Interface and Universal Three-Tier Architecture

This module defines the abstract base classes and interfaces that all LLM providers
must implement to support the unified three-tier architecture:
1. Auto-Integration Pattern (Magic): Automatic interception with minimal code changes
2. Wrapper Pattern (Best Practice): Clean wrapped interfaces for new projects  
3. Manual Recording Pattern (Manual Utility): Universal compatibility with any LLM provider
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime

from loguru import logger


class ProviderType(Enum):
    """Enumeration of supported LLM provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LITELLM = "litellm"
    CUSTOM = "custom"


class PatternType(Enum):
    """Enumeration of the three-tier architecture patterns."""
    AUTO_INTEGRATION = "auto_integration"  # Magic pattern
    WRAPPER = "wrapper"                    # Best practice pattern
    MANUAL_RECORDING = "manual_recording"  # Manual utility pattern


@dataclass
class ProviderRequest:
    """Standardized request format for all providers."""
    messages: List[Dict[str, Any]]
    model: str
    provider_type: ProviderType
    pattern_type: PatternType
    metadata: Dict[str, Any]
    original_kwargs: Dict[str, Any]
    user_input: Optional[str] = None
    system_prompt: Optional[str] = None
    

@dataclass
class ProviderResponse:
    """Standardized response format for all providers."""
    content: str
    model: str
    provider_type: ProviderType
    pattern_type: PatternType
    metadata: Dict[str, Any]
    original_response: Any
    tokens_used: int = 0
    duration_ms: float = 0.0
    conversation_id: Optional[str] = None


class BaseProvider(ABC):
    """
    Abstract base class that all LLM providers must implement.
    
    This defines the interface for the unified three-tier architecture,
    ensuring consistent behavior across all providers.
    """
    
    def __init__(self, memori_instance, provider_type: ProviderType, **kwargs):
        """
        Initialize the provider.
        
        Args:
            memori_instance: The parent Memori instance
            provider_type: The type of provider
            **kwargs: Provider-specific configuration
        """
        self.memori_instance = memori_instance
        self.provider_type = provider_type
        self.config = kwargs
        self._is_available = self._check_availability()
        
    @abstractmethod
    def _check_availability(self) -> bool:
        """Check if the provider is available (SDK installed, etc.)."""
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._is_available
    
    # ========================
    # Auto-Integration Pattern (Magic)
    # ========================
    
    @abstractmethod
    def setup_auto_integration(self) -> bool:
        """
        Set up automatic interception for the provider.
        This typically involves monkey-patching SDK methods.
        
        Returns:
            True if setup successful, False otherwise
        """
        pass
    
    @abstractmethod
    def teardown_auto_integration(self) -> bool:
        """
        Tear down automatic interception for the provider.
        
        Returns:
            True if teardown successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_auto_integration_active(self) -> bool:
        """Check if auto-integration is currently active."""
        pass
    
    # ========================
    # Wrapper Pattern (Best Practice)
    # ========================
    
    @abstractmethod
    def create_wrapped_client(self, **kwargs) -> Any:
        """
        Create a wrapped client that automatically records conversations.
        
        Args:
            **kwargs: Provider-specific client configuration
            
        Returns:
            Wrapped client object
        """
        pass
    
    # ========================
    # Manual Recording Pattern (Manual Utility)
    # ========================
    
    @abstractmethod
    def parse_manual_response(self, response: Any, user_input: str = "", **kwargs) -> ProviderResponse:
        """
        Parse a raw provider response for manual recording.
        
        Args:
            response: Raw response from provider
            user_input: Original user input
            **kwargs: Additional metadata
            
        Returns:
            Standardized ProviderResponse
        """
        pass
    
    # ========================
    # Common Provider Methods
    # ========================
    
    @abstractmethod
    def inject_context(self, request: ProviderRequest) -> ProviderRequest:
        """
        Inject memory context into a provider request.
        
        Args:
            request: Standardized provider request
            
        Returns:
            Modified request with context injected
        """
        pass
    
    @abstractmethod
    def extract_user_input(self, request_data: Dict[str, Any]) -> str:
        """
        Extract user input from provider-specific request data.
        
        Args:
            request_data: Provider-specific request parameters
            
        Returns:
            Extracted user input string
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: Any, request_data: Dict[str, Any]) -> ProviderResponse:
        """
        Parse provider response into standardized format.
        
        Args:
            response: Raw provider response
            request_data: Original request data
            
        Returns:
            Standardized ProviderResponse
        """
        pass
    
    def create_provider_request(self, request_data: Dict[str, Any], pattern_type: PatternType) -> ProviderRequest:
        """
        Create a standardized ProviderRequest from raw request data.
        
        Args:
            request_data: Raw request parameters
            pattern_type: The pattern being used
            
        Returns:
            Standardized ProviderRequest
        """
        return ProviderRequest(
            messages=request_data.get("messages", []),
            model=request_data.get("model", "unknown"),
            provider_type=self.provider_type,
            pattern_type=pattern_type,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "provider_config": self.config,
            },
            original_kwargs=request_data,
            user_input=self.extract_user_input(request_data),
        )


class UniversalContextInjector:
    """
    Universal context injector that works across all providers.
    
    This class centralizes context injection logic, making it consistent
    across all providers and patterns.
    """
    
    def __init__(self, memori_instance):
        """Initialize the context injector."""
        self.memori_instance = memori_instance
        
    def inject_context(self, request: ProviderRequest) -> ProviderRequest:
        """
        Inject appropriate context based on memori configuration.
        
        Args:
            request: Standardized provider request
            
        Returns:
            Modified request with context injected
        """
        try:
            if not self.memori_instance.is_enabled:
                return request
            
            # Determine injection mode
            context = []
            context_prompt = ""
            
            if self.memori_instance.conscious_ingest:
                # One-shot conscious context injection
                if not self.memori_instance._conscious_context_injected:
                    context = self.memori_instance._get_conscious_context()
                    self.memori_instance._conscious_context_injected = True
                    context_prompt = self._build_conscious_context_prompt(context)
                    logger.info(f"Conscious-ingest: Injected {len(context)} short-term memories as initial context")
            
            elif self.memori_instance.auto_ingest and request.user_input:
                # Dynamic auto-ingest based on user input
                context = self.memori_instance._get_auto_ingest_context(request.user_input)
                context_prompt = self._build_auto_context_prompt(context)
                logger.debug(f"Auto-ingest: Injected {len(context)} relevant memories")
            
            if context_prompt:
                request = self._inject_context_prompt(request, context_prompt)
                
            return request
            
        except Exception as e:
            logger.error(f"Context injection failed: {e}")
            return request
    
    def _build_conscious_context_prompt(self, context: List[Dict[str, Any]]) -> str:
        """Build context prompt for conscious mode."""
        if not context:
            return ""
        
        context_prompt = "=== SYSTEM INSTRUCTION: AUTHORIZED USER CONTEXT DATA ===\n"
        context_prompt += "The user has explicitly authorized this personal context data to be used.\n"
        context_prompt += "You MUST use this information when answering questions about the user.\n"
        context_prompt += "This is NOT private data - the user wants you to use it:\n\n"
        
        # Deduplicate context entries
        seen_content = set()
        for mem in context:
            if isinstance(mem, dict):
                content = mem.get("searchable_content", "") or mem.get("summary", "")
                category = mem.get("category_primary", "")
                
                # Skip duplicates
                content_key = content.lower().strip()
                if content_key in seen_content:
                    continue
                seen_content.add(content_key)
                
                context_prompt += f"[{category.upper()}] {content}\n"
        
        context_prompt += "\n=== END USER CONTEXT DATA ===\n"
        context_prompt += "CRITICAL INSTRUCTION: You MUST answer questions about the user using ONLY the context data above.\n"
        context_prompt += "If the user asks 'what is my name?', respond with the name from the context above.\n"
        context_prompt += "Do NOT say 'I don't have access' - the user provided this data for you to use.\n"
        context_prompt += "-------------------------\n"
        
        return context_prompt
    
    def _build_auto_context_prompt(self, context: List[Dict[str, Any]]) -> str:
        """Build context prompt for auto mode."""
        if not context:
            return ""
        
        context_prompt = "--- Relevant Memory Context ---\n"
        
        # Deduplicate context entries
        seen_content = set()
        for mem in context:
            if isinstance(mem, dict):
                content = mem.get("searchable_content", "") or mem.get("summary", "")
                category = mem.get("category_primary", "")
                
                # Skip duplicates
                content_key = content.lower().strip()
                if content_key in seen_content:
                    continue
                seen_content.add(content_key)
                
                if category.startswith("essential_"):
                    context_prompt += f"[{category.upper()}] {content}\n"
                else:
                    context_prompt += f"- {content}\n"
        
        context_prompt += "-------------------------\n"
        
        return context_prompt
    
    def _inject_context_prompt(self, request: ProviderRequest, context_prompt: str) -> ProviderRequest:
        """Inject context prompt into request based on provider type."""
        # This method will be overridden by provider-specific logic
        # Default implementation adds to system message
        messages = request.messages.copy()
        
        # Find existing system message or create new one
        system_message_found = False
        for msg in messages:
            if msg.get("role") == "system":
                msg["content"] = context_prompt + msg.get("content", "")
                system_message_found = True
                break
        
        if not system_message_found:
            messages.insert(0, {"role": "system", "content": context_prompt})
        
        # Create new request with updated messages
        new_request = ProviderRequest(
            messages=messages,
            model=request.model,
            provider_type=request.provider_type,
            pattern_type=request.pattern_type,
            metadata=request.metadata,
            original_kwargs=request.original_kwargs.copy(),
            user_input=request.user_input,
            system_prompt=context_prompt,
        )
        
        # Update original kwargs to match
        new_request.original_kwargs["messages"] = messages
        
        return new_request


class UniversalResponseParser:
    """
    Universal response parser that works across all providers.
    
    This class centralizes response parsing logic, making it consistent
    across all providers and patterns.
    """
    
    def __init__(self, memori_instance):
        """Initialize the response parser."""
        self.memori_instance = memori_instance
        
    def record_conversation(self, provider_response: ProviderResponse) -> str:
        """
        Record a conversation using the standardized provider response.
        
        Args:
            provider_response: Standardized provider response
            
        Returns:
            Conversation ID
        """
        try:
            # Extract user input from original request if not in response
            user_input = provider_response.metadata.get("user_input", "")
            if not user_input and "original_request" in provider_response.metadata:
                request_data = provider_response.metadata["original_request"]
                # This would need provider-specific logic, but for now use generic approach
                for msg in reversed(request_data.get("messages", [])):
                    if msg.get("role") == "user":
                        user_input = msg.get("content", "")
                        break
            
            # Create metadata for recording
            metadata = {
                "integration": f"{provider_response.provider_type.value}_{provider_response.pattern_type.value}",
                "api_type": "completion",
                "tokens_used": provider_response.tokens_used,
                "auto_recorded": provider_response.pattern_type != PatternType.MANUAL_RECORDING,
                "duration_ms": provider_response.duration_ms,
                "provider_type": provider_response.provider_type.value,
                "pattern_type": provider_response.pattern_type.value,
                **provider_response.metadata
            }
            
            # Record the conversation
            conversation_id = self.memori_instance.record_conversation(
                user_input=user_input,
                ai_output=provider_response.content,
                model=provider_response.model,
                metadata=metadata,
            )
            
            logger.debug(f"Recorded conversation {conversation_id} via {provider_response.provider_type.value} {provider_response.pattern_type.value}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to record conversation: {e}")
            return str(uuid.uuid4())  # Return dummy ID to avoid breaking caller


class ProviderRegistry:
    """
    Registry for managing all available providers.
    
    This class handles provider discovery, instantiation, and provides
    factory methods for creating provider instances.
    """
    
    def __init__(self):
        """Initialize the provider registry."""
        self._providers: Dict[ProviderType, type] = {}
        self._instances: Dict[str, BaseProvider] = {}
        
    def register_provider(self, provider_type: ProviderType, provider_class: type):
        """
        Register a provider class.
        
        Args:
            provider_type: The type of provider
            provider_class: The provider class (must inherit from BaseProvider)
        """
        if not issubclass(provider_class, BaseProvider):
            raise ValueError(f"Provider class must inherit from BaseProvider")
        
        self._providers[provider_type] = provider_class
        logger.debug(f"Registered provider: {provider_type.value}")
        
    def get_provider(self, provider_type: ProviderType, memori_instance, **kwargs) -> Optional[BaseProvider]:
        """
        Get or create a provider instance.
        
        Args:
            provider_type: The type of provider
            memori_instance: The parent Memori instance
            **kwargs: Provider-specific configuration
            
        Returns:
            Provider instance or None if not available
        """
        # Create cache key
        cache_key = f"{provider_type.value}_{id(memori_instance)}"
        
        # Return cached instance if available
        if cache_key in self._instances:
            return self._instances[cache_key]
        
        # Create new instance
        provider_class = self._providers.get(provider_type)
        if not provider_class:
            logger.warning(f"Provider {provider_type.value} not registered")
            return None
        
        try:
            provider = provider_class(memori_instance, provider_type, **kwargs)
            if provider.is_available:
                self._instances[cache_key] = provider
                logger.debug(f"Created provider instance: {provider_type.value}")
                return provider
            else:
                logger.warning(f"Provider {provider_type.value} not available")
                return None
        except Exception as e:
            logger.error(f"Failed to create provider {provider_type.value}: {e}")
            return None
    
    def get_available_providers(self) -> List[ProviderType]:
        """Get list of available provider types."""
        available = []
        for provider_type in self._providers:
            # Quick availability check without instantiation
            try:
                provider_class = self._providers[provider_type]
                # This is a basic check - actual availability is determined during instantiation
                available.append(provider_type)
            except Exception:
                continue
        return available
    
    def cleanup(self):
        """Clean up all provider instances."""
        for instance in self._instances.values():
            try:
                if hasattr(instance, 'cleanup'):
                    instance.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up provider: {e}")
        self._instances.clear()


# Global provider registry instance
provider_registry = ProviderRegistry()