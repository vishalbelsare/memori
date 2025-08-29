"""
HTTP layer interceptor as fallback for unsupported libraries using transport middleware.
"""

import json
import re
import weakref
from typing import Any, Dict, Optional, TYPE_CHECKING

from loguru import logger

from .base import ConversationInterceptor

if TYPE_CHECKING:
    from ..core.memory import Memori


class HTTPInterceptor(ConversationInterceptor):
    """HTTP layer interceptor as fallback for unsupported libraries"""
    
    def __init__(self, memori_instance: 'Memori'):
        super().__init__(memori_instance)
        self._memori_ref = weakref.ref(memori_instance)  # Initialize weak reference
        self._httpx_transport_original = None
        self._requests_adapter_original = None
        self._installed_transports = []
        
    def enable(self) -> bool:
        """Enable HTTP layer interception using transport middleware"""
        with self._lock:
            if self._enabled:
                return True
                
            try:
                # Install httpx transport middleware if available
                try:
                    import httpx
                    self._install_httpx_middleware()
                    logger.debug("HTTP interceptor: httpx middleware installed")
                except ImportError:
                    logger.debug("HTTP interceptor: httpx not available")
                except Exception as e:
                    logger.debug(f"HTTP interceptor: httpx middleware failed: {e}")
                
                # Install requests adapter middleware if available  
                try:
                    import requests
                    self._install_requests_middleware()
                    logger.debug("HTTP interceptor: requests middleware installed")
                except ImportError:
                    logger.debug("HTTP interceptor: requests not available")
                except Exception as e:
                    logger.debug(f"HTTP interceptor: requests middleware failed: {e}")
                
                self._enabled = True
                logger.debug("HTTP interceptor enabled with transport middleware")
                return True
                
            except Exception as e:
                logger.error(f"Failed to enable HTTP interceptor: {e}")
                return False
    
    def disable(self) -> bool:
        """Disable HTTP layer interception"""
        with self._lock:
            if not self._enabled:
                return True
                
            try:
                # Clean up installed middleware
                self._cleanup_middleware()
                
                self._enabled = False
                logger.debug("HTTP interceptor disabled")
                return True
                
            except Exception as e:
                logger.error(f"Failed to disable HTTP interceptor: {e}")
                return False
    
    def _install_httpx_middleware(self):
        """Install httpx transport middleware (no method patching)"""
        import httpx
        
        class MemoriHTTPXTransport(httpx.HTTPTransport):
            def __init__(self, memori_interceptor, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.memori_interceptor = memori_interceptor
            
            def handle_request(self, request):
                # Check if this is an LLM request
                if (self.memori_interceptor.memori.is_enabled and 
                    self.memori_interceptor._is_llm_endpoint(str(request.url))):
                    
                    # Make the request through parent
                    response = super().handle_request(request)
                    
                    # Try to record the conversation
                    try:
                        self.memori_interceptor._parse_and_record_http_request(
                            request.method, str(request.url), 
                            {'content': request.content}, response
                        )
                    except Exception as e:
                        logger.debug(f"Failed to record httpx request: {e}")
                    
                    return response
                else:
                    return super().handle_request(request)
        
        # Store transport class for cleanup
        self._memori_httpx_transport = MemoriHTTPXTransport
        
    def _install_requests_middleware(self):
        """Install requests adapter middleware (no method patching)"""
        import requests
        from requests.adapters import HTTPAdapter
        
        class MemoriHTTPAdapter(HTTPAdapter):
            def __init__(self, memori_interceptor, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.memori_interceptor = memori_interceptor
            
            def send(self, request, **kwargs):
                # Check if this is an LLM request
                if (self.memori_interceptor.memori.is_enabled and 
                    self.memori_interceptor._is_llm_endpoint(request.url)):
                    
                    # Make the request through parent
                    response = super().send(request, **kwargs)
                    
                    # Try to record the conversation
                    try:
                        self.memori_interceptor._parse_and_record_http_request(
                            request.method, request.url,
                            {'data': request.body}, response
                        )
                    except Exception as e:
                        logger.debug(f"Failed to record requests request: {e}")
                    
                    return response
                else:
                    return super().send(request, **kwargs)
        
        # Store adapter class for cleanup
        self._memori_requests_adapter = MemoriHTTPAdapter
        
    def _cleanup_middleware(self):
        """Clean up installed middleware"""
        # Clean up any installed transports/adapters
        for transport in self._installed_transports:
            try:
                # Transport cleanup logic would go here
                pass
            except Exception as e:
                logger.debug(f"Error cleaning up transport: {e}")
        
        self._installed_transports.clear()
        
        # Clear references
        if hasattr(self, '_memori_httpx_transport'):
            delattr(self, '_memori_httpx_transport')
        if hasattr(self, '_memori_requests_adapter'):
            delattr(self, '_memori_requests_adapter')
    
    def _is_llm_endpoint(self, url: str) -> bool:
        """Check if URL is an LLM API endpoint"""
        llm_domains = [
            'api.openai.com',
            'api.anthropic.com', 
            'api.cohere.ai',
            'api.together.xyz',
            'api.mistral.ai',
            'generativelanguage.googleapis.com'  # Google AI
        ]
        return any(domain in url for domain in llm_domains)
    
    def _parse_and_record_http_request(self, method: str, url: str, request_data: Dict[str, Any], response: Any):
        """Parse HTTP request/response and record conversation"""
        if not self._should_allow_operation():
            return
            
        try:
            memori = self._memori_ref()
            if not memori or not memori.is_enabled:
                return
            
            # Extract conversation data from HTTP request/response
            user_input, ai_output, model = self._extract_conversation_from_http(
                method, url, request_data, response
            )
            
            if user_input and ai_output:
                # Record the conversation
                memori.record_conversation(
                    user_input=user_input,
                    ai_output=ai_output,
                    model=model or "http-intercepted",
                    metadata={"interceptor": "http", "url": url}
                )
                self._record_success()
            
        except Exception as e:
            logger.debug(f"HTTP request parsing failed: {e}")
            self._record_failure()
    
    def _extract_conversation_from_http(self, method: str, url: str, request_data: Dict[str, Any], response: Any) -> tuple[str, str, str]:
        """Extract conversation data from HTTP request/response"""
        user_input = ""
        ai_output = ""
        model = "unknown"
        
        try:
            # Parse request data
            request_content = request_data.get('content') or request_data.get('data') or b""
            if isinstance(request_content, bytes):
                request_json = json.loads(request_content.decode('utf-8'))
            elif isinstance(request_content, str):
                request_json = json.loads(request_content)
            else:
                request_json = request_content or {}
            
            # Parse response data
            if hasattr(response, 'content'):
                response_content = response.content
            elif hasattr(response, 'text'):
                response_content = response.text.encode('utf-8')
            else:
                response_content = str(response).encode('utf-8')
            
            if isinstance(response_content, bytes):
                response_json = json.loads(response_content.decode('utf-8'))
            else:
                response_json = json.loads(str(response_content))
            
            # Extract based on API type
            if 'api.openai.com' in url:
                user_input, ai_output, model = self._parse_openai_http(request_json, response_json)
            elif 'api.anthropic.com' in url:
                user_input, ai_output, model = self._parse_anthropic_http(request_json, response_json)
            else:
                # Generic parsing
                user_input, ai_output, model = self._parse_generic_http(request_json, response_json)
                
        except Exception as e:
            logger.debug(f"Failed to extract conversation from HTTP: {e}")
        
        return user_input, ai_output, model
    
    def _parse_openai_http(self, request: Dict[str, Any], response: Dict[str, Any]) -> tuple[str, str, str]:
        """Parse OpenAI API HTTP request/response"""
        user_input = ""
        ai_output = ""
        model = request.get('model', 'openai-unknown')
        
        # Extract user input from messages
        messages = request.get('messages', [])
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                user_input = msg.get('content', '')
                break
        
        # Extract AI output from response
        choices = response.get('choices', [])
        if choices:
            choice = choices[0]
            if 'message' in choice and 'content' in choice['message']:
                ai_output = choice['message']['content']
            elif 'text' in choice:
                ai_output = choice['text']
        
        return user_input, ai_output, model
    
    def _parse_anthropic_http(self, request: Dict[str, Any], response: Dict[str, Any]) -> tuple[str, str, str]:
        """Parse Anthropic API HTTP request/response"""
        user_input = ""
        ai_output = ""
        model = request.get('model', 'anthropic-unknown')
        
        # Extract user input from messages
        messages = request.get('messages', [])
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                content = msg.get('content', '')
                if isinstance(content, list):
                    user_input = ' '.join(block.get('text', '') for block in content if block.get('type') == 'text')
                else:
                    user_input = content
                break
        
        # Extract AI output from response
        content = response.get('content', [])
        if isinstance(content, list):
            ai_output = ' '.join(block.get('text', '') for block in content if block.get('type') == 'text')
        else:
            ai_output = str(content)
        
        return user_input, ai_output, model
    
    def _parse_generic_http(self, request: Dict[str, Any], response: Dict[str, Any]) -> tuple[str, str, str]:
        """Generic HTTP parsing for unknown APIs"""
        user_input = ""
        ai_output = ""
        model = "http-generic"
        
        # Try common patterns for user input
        for key in ['prompt', 'input', 'query', 'message', 'text']:
            if key in request:
                user_input = str(request[key])
                break
        
        # Try common patterns for AI output
        for key in ['response', 'output', 'result', 'text', 'content']:
            if key in response:
                ai_output = str(response[key])
                break
        
        # Try to find model
        model = request.get('model') or response.get('model') or "http-generic"
        
        return user_input, ai_output, model