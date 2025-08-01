"""
OpenAI Integration - Automatic conversation recording for OpenAI API calls
"""

import openai
import json
from typing import Optional, Dict, Any, Callable
from loguru import logger
from datetime import datetime

# Global registry for Memori instances
_memori_instances = []
_original_openai_functions = {}
_hooks_installed = False


def install_openai_hooks():
    """Install hooks to intercept OpenAI API calls"""
    global _hooks_installed, _original_openai_functions
    
    if _hooks_installed:
        return
    
    # Store original functions
    _original_openai_functions['chat_completions_create'] = openai.resources.chat.completions.Completions.create
    _original_openai_functions['completions_create'] = openai.resources.completions.Completions.create
    
    # Replace with our wrapped versions
    openai.resources.chat.completions.Completions.create = _wrapped_chat_completions_create
    openai.resources.completions.Completions.create = _wrapped_completions_create
    
    _hooks_installed = True
    logger.info("OpenAI hooks installed for auto-recording")


def uninstall_openai_hooks():
    """Uninstall OpenAI hooks and restore original functions"""
    global _hooks_installed, _original_openai_functions
    
    if not _hooks_installed:
        return
    
    # Restore original functions
    if 'chat_completions_create' in _original_openai_functions:
        openai.resources.chat.completions.Completions.create = _original_openai_functions['chat_completions_create']
    
    if 'completions_create' in _original_openai_functions:
        openai.resources.completions.Completions.create = _original_openai_functions['completions_create']
    
    _hooks_installed = False
    _original_openai_functions.clear()
    logger.info("OpenAI hooks uninstalled")


def register_memori_instance(memori_instance):
    """Register a Memori instance for auto-recording"""
    global _memori_instances
    if memori_instance not in _memori_instances:
        _memori_instances.append(memori_instance)
        logger.debug(f"Registered Memori instance: {memori_instance.namespace}")


def unregister_memori_instance(memori_instance):
    """Unregister a Memori instance"""
    global _memori_instances
    if memori_instance in _memori_instances:
        _memori_instances.remove(memori_instance)
        logger.debug(f"Unregistered Memori instance: {memori_instance.namespace}")


def _wrapped_chat_completions_create(self, **kwargs):
    """Wrapped version of OpenAI chat completions create"""
    # Call original function
    response = _original_openai_functions['chat_completions_create'](self, **kwargs)
    
    # Record conversation for all active Memori instances
    _record_chat_conversation(kwargs, response)
    
    return response


def _wrapped_completions_create(self, **kwargs):
    """Wrapped version of OpenAI completions create"""
    # Call original function
    response = _original_openai_functions['completions_create'](self, **kwargs)
    
    # Record conversation for all active Memori instances
    _record_completion_conversation(kwargs, response)
    
    return response


def _record_chat_conversation(request_kwargs: Dict[str, Any], response):
    """Record a chat completion conversation"""
    global _memori_instances
    
    try:
        # Extract conversation details
        messages = request_kwargs.get('messages', [])
        model = request_kwargs.get('model', 'unknown')
        
        # Find user input (last user message)
        user_input = ""
        for message in reversed(messages):
            if message.get('role') == 'user':
                user_input = message.get('content', '')
                break
        
        # Extract AI response
        ai_output = ""
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and choice.message:
                ai_output = choice.message.content or ""
        
        # Calculate tokens used
        tokens_used = 0
        if hasattr(response, 'usage') and response.usage:
            tokens_used = getattr(response.usage, 'total_tokens', 0)
        
        # Record for all active instances
        for memori_instance in _memori_instances:
            if memori_instance.is_enabled:
                try:
                    memori_instance.record_conversation(
                        user_input=user_input,
                        ai_output=ai_output,
                        model=model,
                        metadata={
                            'integration': 'openai',
                            'api_type': 'chat_completions',
                            'tokens_used': tokens_used,
                            'auto_recorded': True
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to record conversation for instance {memori_instance.namespace}: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to record OpenAI chat conversation: {e}")


def _record_completion_conversation(request_kwargs: Dict[str, Any], response):
    """Record a completion conversation"""
    global _memori_instances
    
    try:
        # Extract conversation details
        prompt = request_kwargs.get('prompt', '')
        model = request_kwargs.get('model', 'unknown')
        
        # Extract AI response
        ai_output = ""
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'text'):
                ai_output = choice.text or ""
        
        # Calculate tokens used
        tokens_used = 0
        if hasattr(response, 'usage') and response.usage:
            tokens_used = getattr(response.usage, 'total_tokens', 0)
        
        # Record for all active instances
        for memori_instance in _memori_instances:
            if memori_instance.is_enabled:
                try:
                    memori_instance.record_conversation(
                        user_input=prompt,
                        ai_output=ai_output,
                        model=model,
                        metadata={
                            'integration': 'openai',
                            'api_type': 'completions',
                            'tokens_used': tokens_used,
                            'auto_recorded': True
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to record conversation for instance {memori_instance.namespace}: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to record OpenAI completion conversation: {e}")


def get_stats() -> Dict[str, Any]:
    """Get integration statistics"""
    return {
        'integration': 'openai',
        'hooks_installed': _hooks_installed,
        'active_instances': len(_memori_instances),
        'instance_namespaces': [instance.namespace for instance in _memori_instances]
    }
