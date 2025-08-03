"""
Main Memori class - Pydantic-based memory interface v1.0
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    from litellm import failure_callback, success_callback

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("LiteLLM not available - native callback system disabled")

from ..agents.memory_agent import MemoryAgent
from ..agents.retrieval_agent import MemorySearchEngine
from ..utils.exceptions import DatabaseError, MemoriError
from ..utils.pydantic_models import ConversationContext
from .database import DatabaseManager


class Memori:
    """
    The main Memori memory layer for AI agents.

    Provides persistent memory storage, categorization, and retrieval
    for AI conversations and agent interactions.
    """

    def __init__(
        self,
        database_connect: str = "sqlite:///memori.db",
        template: str = "basic",
        mem_prompt: Optional[str] = None,
        conscious_ingest: bool = True,
        namespace: Optional[str] = None,
        shared_memory: bool = False,
        memory_filters: Optional[Dict[str, Any]] = None,
        openai_api_key: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize Memori memory system v1.0.

        Args:
            database_connect: Database connection string
            template: Memory template to use ('basic')
            mem_prompt: Optional prompt to guide memory recording
            conscious_ingest: Enable intelligent memory filtering
            namespace: Optional namespace for memory isolation
            shared_memory: Enable shared memory across agents
            memory_filters: Filters for memory ingestion
            openai_api_key: OpenAI API key for memory agent
            user_id: Optional user identifier
        """
        self.database_connect = database_connect
        self.template = template
        self.mem_prompt = mem_prompt
        self.conscious_ingest = conscious_ingest
        self.namespace = namespace or "default"
        self.shared_memory = shared_memory
        self.memory_filters = memory_filters or {}
        self.openai_api_key = openai_api_key
        self.user_id = user_id

        # Initialize database manager
        self.db_manager = DatabaseManager(database_connect, template)

        # Initialize Pydantic-based agents
        self.memory_agent = None
        self.search_engine = None

        if conscious_ingest:
            try:
                # Initialize Pydantic-based agents
                self.memory_agent = MemoryAgent(api_key=openai_api_key, model="gpt-4o")
                self.search_engine = MemorySearchEngine(
                    api_key=openai_api_key, model="gpt-4o"
                )
                logger.info("Pydantic-based memory and search agents initialized")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize OpenAI agents: {e}. Conscious ingestion disabled."
                )
                self.conscious_ingest = False

        # State tracking
        self._enabled = False
        self._session_id = str(uuid.uuid4())

        # User context for memory processing
        self._user_context = {
            "current_projects": [],
            "relevant_skills": [],
            "user_preferences": [],
        }

        # Initialize database
        self._setup_database()

        logger.info(
            f"Memori v1.0 initialized with template: {template}, namespace: {namespace}"
        )

    def _setup_database(self):
        """Setup database tables based on template"""
        try:
            self.db_manager.initialize_schema()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            raise DatabaseError(f"Failed to setup database: {e}")

    def enable(self):
        """
        Enable universal memory recording for ALL LLM providers.

        This automatically sets up recording for:
        - LiteLLM: Native callback system (recommended)
        - OpenAI: Automatic client wrapping when instantiated
        - Anthropic: Automatic client wrapping when instantiated
        - Any other provider: Auto-detected and wrapped
        """
        if self._enabled:
            logger.warning("Memori is already enabled.")
            return

        self._enabled = True
        self._session_id = str(uuid.uuid4())

        # 1. Set up LiteLLM native callbacks (if available)
        litellm_enabled = self._setup_litellm_callbacks()

        # 2. Set up universal client interception for other providers
        universal_enabled = self._setup_universal_interception()

        # 3. Register this instance globally for any provider to use
        self._register_global_instance()

        providers = []
        if litellm_enabled:
            providers.append("LiteLLM (native callbacks)")
        if universal_enabled:
            providers.append("OpenAI/Anthropic (auto-wrapping)")

        logger.info(
            f"Memori enabled for session: {self.session_id}\n"
            f"Active providers: {', '.join(providers) if providers else 'None detected'}\n"
            f"Usage: Simply use any LLM client normally - conversations will be auto-recorded!"
        )

    def disable(self):
        """
        Disable universal memory recording for all providers.
        """
        if not self._enabled:
            return

        # 1. Remove LiteLLM callbacks
        if LITELLM_AVAILABLE:
            try:
                success_callback.remove(self._litellm_success_callback)
            except ValueError:
                pass

        # 2. Disable universal interception
        self._disable_universal_interception()

        # 3. Unregister global instance
        self._unregister_global_instance()

        self._enabled = False
        logger.info("Memori disabled for all providers.")

    def _setup_litellm_callbacks(self) -> bool:
        """Set up LiteLLM native callback system"""
        if not LITELLM_AVAILABLE:
            logger.debug("LiteLLM not available, skipping native callbacks")
            return False

        try:
            success_callback.append(self._litellm_success_callback)
            logger.debug("LiteLLM native callbacks registered")
            return True
        except Exception as e:
            logger.error(f"Failed to setup LiteLLM callbacks: {e}")
            return False

    def _setup_universal_interception(self) -> bool:
        """Set up universal client interception for OpenAI, Anthropic, etc."""
        try:
            # Use Python's import hook system to intercept client creation
            self._install_import_hooks()
            logger.debug("Universal client interception enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to setup universal interception: {e}")
            return False

    def _get_builtin_import(self):
        """Safely get __import__ from __builtins__ (handles both dict and module cases)"""
        if isinstance(__builtins__, dict):
            return __builtins__["__import__"]
        else:
            return __builtins__.__import__

    def _set_builtin_import(self, import_func):
        """Safely set __import__ in __builtins__ (handles both dict and module cases)"""
        if isinstance(__builtins__, dict):
            __builtins__["__import__"] = import_func
        else:
            __builtins__.__import__ = import_func

    def _install_import_hooks(self):
        """Install import hooks to automatically wrap LLM clients"""

        # Store original __import__ if not already done
        if not hasattr(self, "_original_import"):
            self._original_import = self._get_builtin_import()

        def memori_import_hook(name, globals=None, locals=None, fromlist=(), level=0):
            """Custom import hook that wraps LLM clients automatically"""
            module = self._original_import(name, globals, locals, fromlist, level)

            # Only process if memori is enabled and this is an LLM module
            if not self._enabled:
                return module

            # Auto-wrap OpenAI clients
            if name == "openai" or (fromlist and "openai" in name):
                self._wrap_openai_module(module)

            # Auto-wrap Anthropic clients
            elif name == "anthropic" or (fromlist and "anthropic" in name):
                self._wrap_anthropic_module(module)

            return module

        # Install the hook
        self._set_builtin_import(memori_import_hook)

    def _wrap_openai_module(self, module):
        """Automatically wrap OpenAI client when imported"""
        try:
            if hasattr(module, "OpenAI") and not hasattr(
                module.OpenAI, "_memori_wrapped"
            ):
                original_init = module.OpenAI.__init__

                def wrapped_init(self_client, *args, **kwargs):
                    # Call original init
                    result = original_init(self_client, *args, **kwargs)

                    # Wrap the client methods for automatic recording
                    if hasattr(self_client, "chat") and hasattr(
                        self_client.chat, "completions"
                    ):
                        original_create = self_client.chat.completions.create

                        def wrapped_create(*args, **kwargs):
                            # Inject context if conscious ingestion is enabled
                            if self.is_enabled and self.conscious_ingest:
                                kwargs = self._inject_openai_context(kwargs)

                            # Make the call
                            response = original_create(*args, **kwargs)

                            # Record if enabled
                            if self.is_enabled:
                                self._record_openai_conversation(kwargs, response)

                            return response

                        self_client.chat.completions.create = wrapped_create

                    return result

                module.OpenAI.__init__ = wrapped_init
                module.OpenAI._memori_wrapped = True
                logger.debug("OpenAI client auto-wrapping enabled")

        except Exception as e:
            logger.debug(f"Could not wrap OpenAI module: {e}")

    def _wrap_anthropic_module(self, module):
        """Automatically wrap Anthropic client when imported"""
        try:
            if hasattr(module, "Anthropic") and not hasattr(
                module.Anthropic, "_memori_wrapped"
            ):
                original_init = module.Anthropic.__init__

                def wrapped_init(self_client, *args, **kwargs):
                    # Call original init
                    result = original_init(self_client, *args, **kwargs)

                    # Wrap the messages.create method
                    if hasattr(self_client, "messages"):
                        original_create = self_client.messages.create

                        def wrapped_create(*args, **kwargs):
                            # Inject context if conscious ingestion is enabled
                            if self.is_enabled and self.conscious_ingest:
                                kwargs = self._inject_anthropic_context(kwargs)

                            # Make the call
                            response = original_create(*args, **kwargs)

                            # Record if enabled
                            if self.is_enabled:
                                self._record_anthropic_conversation(kwargs, response)

                            return response

                        self_client.messages.create = wrapped_create

                    return result

                module.Anthropic.__init__ = wrapped_init
                module.Anthropic._memori_wrapped = True
                logger.debug("Anthropic client auto-wrapping enabled")

        except Exception as e:
            logger.debug(f"Could not wrap Anthropic module: {e}")

    def _disable_universal_interception(self):
        """Disable universal client interception"""
        try:
            # Restore original import if we modified it
            if hasattr(self, "_original_import"):
                self._set_builtin_import(self._original_import)
                delattr(self, "_original_import")
                logger.debug("Universal interception disabled")
        except Exception as e:
            logger.debug(f"Error disabling universal interception: {e}")

    def _register_global_instance(self):
        """Register this memori instance globally"""
        # Store in a global registry that wrapped clients can access
        if not hasattr(Memori, "_global_instances"):
            Memori._global_instances = []
        Memori._global_instances.append(self)

    def _unregister_global_instance(self):
        """Unregister this memori instance globally"""
        if hasattr(Memori, "_global_instances") and self in Memori._global_instances:
            Memori._global_instances.remove(self)

    def _inject_openai_context(self, kwargs):
        """Inject context for OpenAI calls"""
        try:
            # Extract user input from messages
            user_input = ""
            for msg in reversed(kwargs.get("messages", [])):
                if msg.get("role") == "user":
                    user_input = msg.get("content", "")
                    break

            if user_input:
                context = self.retrieve_context(user_input, limit=3)
                if context:
                    context_prompt = "--- Relevant Memories ---\n"
                    for mem in context:
                        if isinstance(mem, dict):
                            summary = mem.get("summary", "") or mem.get("content", "")
                            context_prompt += f"- {summary}\n"
                        else:
                            context_prompt += f"- {str(mem)}\n"
                    context_prompt += "-------------------------\n"

                    # Inject into system message
                    messages = kwargs.get("messages", [])
                    for msg in messages:
                        if msg.get("role") == "system":
                            msg["content"] = context_prompt + msg.get("content", "")
                            break
                    else:
                        messages.insert(
                            0, {"role": "system", "content": context_prompt}
                        )

                    logger.debug(f"Injected context: {len(context)} memories")
        except Exception as e:
            logger.error(f"Context injection failed: {e}")
        return kwargs

    def _inject_anthropic_context(self, kwargs):
        """Inject context for Anthropic calls"""
        try:
            # Extract user input from messages
            user_input = ""
            for msg in reversed(kwargs.get("messages", [])):
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        user_input = " ".join(
                            [
                                block.get("text", "")
                                for block in content
                                if isinstance(block, dict)
                                and block.get("type") == "text"
                            ]
                        )
                    else:
                        user_input = content
                    break

            if user_input:
                context = self.retrieve_context(user_input, limit=3)
                if context:
                    context_prompt = "--- Relevant Memories ---\n"
                    for mem in context:
                        if isinstance(mem, dict):
                            summary = mem.get("summary", "") or mem.get("content", "")
                            context_prompt += f"- {summary}\n"
                        else:
                            context_prompt += f"- {str(mem)}\n"
                    context_prompt += "-------------------------\n"

                    # Inject into system parameter
                    if kwargs.get("system"):
                        kwargs["system"] = context_prompt + kwargs["system"]
                    else:
                        kwargs["system"] = context_prompt

                    logger.debug(f"Injected context: {len(context)} memories")
        except Exception as e:
            logger.error(f"Context injection failed: {e}")
        return kwargs

    def _record_openai_conversation(self, kwargs, response):
        """Record OpenAI conversation"""
        try:
            messages = kwargs.get("messages", [])
            model = kwargs.get("model", "unknown")

            # Extract user input
            user_input = ""
            for message in reversed(messages):
                if message.get("role") == "user":
                    user_input = message.get("content", "")
                    break

            # Extract AI response
            ai_output = ""
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and choice.message:
                    ai_output = choice.message.content or ""

            # Calculate tokens
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                tokens_used = getattr(response.usage, "total_tokens", 0)

            # Record conversation
            self.record_conversation(
                user_input=user_input,
                ai_output=ai_output,
                model=model,
                metadata={
                    "integration": "openai_auto",
                    "api_type": "chat_completions",
                    "tokens_used": tokens_used,
                    "auto_recorded": True,
                },
            )
        except Exception as e:
            logger.error(f"Failed to record OpenAI conversation: {e}")

    def _record_anthropic_conversation(self, kwargs, response):
        """Record Anthropic conversation"""
        try:
            messages = kwargs.get("messages", [])
            model = kwargs.get("model", "claude-unknown")

            # Extract user input
            user_input = ""
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")
                    if isinstance(content, list):
                        user_input = " ".join(
                            [
                                block.get("text", "")
                                for block in content
                                if isinstance(block, dict)
                                and block.get("type") == "text"
                            ]
                        )
                    else:
                        user_input = content
                    break

            # Extract AI response
            ai_output = ""
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, list):
                    ai_output = " ".join(
                        [
                            block.text
                            for block in response.content
                            if hasattr(block, "text")
                        ]
                    )
                else:
                    ai_output = str(response.content)

            # Calculate tokens
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                input_tokens = getattr(response.usage, "input_tokens", 0)
                output_tokens = getattr(response.usage, "output_tokens", 0)
                tokens_used = input_tokens + output_tokens

            # Record conversation
            self.record_conversation(
                user_input=user_input,
                ai_output=ai_output,
                model=model,
                metadata={
                    "integration": "anthropic_auto",
                    "api_type": "messages",
                    "tokens_used": tokens_used,
                    "auto_recorded": True,
                },
            )
        except Exception as e:
            logger.error(f"Failed to record Anthropic conversation: {e}")

    def _litellm_success_callback(self, kwargs, response, start_time, end_time):
        """
        This function is automatically called by LiteLLM after a successful completion.
        """
        try:
            user_input = ""
            # Find the last user message
            for msg in reversed(kwargs.get("messages", [])):
                if msg.get("role") == "user":
                    user_input = msg.get("content", "")
                    break

            ai_output = response.choices[0].message.content
            model = kwargs.get("model", "unknown")

            # Calculate tokens used
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                tokens_used = getattr(response.usage, "total_tokens", 0)

            # Handle timing data safely - convert any time objects to float/string
            duration_ms = 0
            start_time_str = None
            end_time_str = None

            try:
                if start_time is not None and end_time is not None:
                    # Handle different types of time objects
                    if hasattr(start_time, "total_seconds"):  # timedelta
                        duration_ms = start_time.total_seconds() * 1000
                    elif isinstance(start_time, (int, float)) and isinstance(
                        end_time, (int, float)
                    ):
                        duration_ms = (end_time - start_time) * 1000

                    start_time_str = str(start_time)
                    end_time_str = str(end_time)
            except Exception:
                # If timing calculation fails, just skip it
                pass

            self.record_conversation(
                user_input,
                ai_output,
                model,
                metadata={
                    "integration": "litellm",
                    "api_type": "completion",
                    "tokens_used": tokens_used,
                    "auto_recorded": True,
                    "start_time_str": start_time_str,
                    "end_time_str": end_time_str,
                    "duration_ms": duration_ms,
                },
            )
        except Exception as e:
            logger.error(f"Memori callback failed: {e}")

    def record_conversation(
        self,
        user_input: str,
        ai_output: str,
        model: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Manually record a conversation

        Args:
            user_input: The user's input message
            ai_output: The AI's response
            model: Model used for the response
            metadata: Additional metadata

        Returns:
            chat_id: Unique identifier for this conversation
        """
        if not self._enabled:
            raise MemoriError("Memori is not enabled. Call enable() first.")

        chat_id = str(uuid.uuid4())
        timestamp = datetime.now()

        try:
            # Store in chat history
            self.db_manager.store_chat_history(
                chat_id=chat_id,
                user_input=user_input,
                ai_output=ai_output,
                model=model,
                timestamp=timestamp,
                session_id=self._session_id,
                namespace=self.namespace,
                metadata=metadata or {},
            )

            # Process for memory categorization
            if self.conscious_ingest:
                self._process_memory_ingestion(chat_id, user_input, ai_output, model)

            logger.debug(f"Conversation recorded: {chat_id}")
            return chat_id

        except Exception as e:
            raise MemoriError(f"Failed to record conversation: {e}")

    def _process_memory_ingestion(
        self, chat_id: str, user_input: str, ai_output: str, model: str = "unknown"
    ):
        """Process conversation for Pydantic-based memory categorization"""
        if not self.memory_agent:
            logger.warning("Memory agent not available, skipping memory ingestion")
            return

        try:
            # Create conversation context
            context = ConversationContext(
                user_id=self.user_id,
                session_id=self._session_id,
                conversation_id=chat_id,
                model_used=model,
                user_preferences=self._user_context.get("user_preferences", []),
                current_projects=self._user_context.get("current_projects", []),
                relevant_skills=self._user_context.get("relevant_skills", []),
            )

            # Process conversation using Pydantic-based memory agent
            processed_memory = self.memory_agent.process_conversation_sync(
                chat_id=chat_id,
                user_input=user_input,
                ai_output=ai_output,
                context=context,
                mem_prompt=self.mem_prompt,
                filters=self.memory_filters,
            )

            # Store processed memory with entity indexing
            if processed_memory.should_store:
                memory_id = self.db_manager.store_processed_memory(
                    memory=processed_memory, chat_id=chat_id, namespace=self.namespace
                )

                if memory_id:
                    logger.debug(
                        f"Stored processed memory {memory_id} for chat {chat_id}"
                    )
                else:
                    logger.debug(
                        f"Memory not stored for chat {chat_id}: {processed_memory.storage_reasoning}"
                    )
            else:
                logger.debug(
                    f"Memory not stored for chat {chat_id}: {processed_memory.storage_reasoning}"
                )

        except Exception as e:
            logger.error(f"Memory ingestion failed for {chat_id}: {e}")

    def retrieve_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query using Pydantic-based search

        Args:
            query: The query to find context for
            limit: Maximum number of context items to return

        Returns:
            List of relevant memory items with search metadata
        """
        try:
            # Use Pydantic-based search engine for intelligent retrieval
            if self.search_engine:
                context_items = self.search_engine.execute_search(
                    query=query,
                    db_manager=self.db_manager,
                    namespace=self.namespace,
                    limit=limit,
                )
            else:
                # Fallback to database search
                context_items = self.db_manager.search_memories(
                    query=query, namespace=self.namespace, limit=limit
                )

            logger.debug(
                f"Retrieved {len(context_items)} context items for query: {query}"
            )
            return context_items

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []

    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            return self.db_manager.get_chat_history(
                namespace=self.namespace,
                session_id=self._session_id if not self.shared_memory else None,
                limit=limit,
            )
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    def clear_memory(self, memory_type: Optional[str] = None):
        """
        Clear memory data

        Args:
            memory_type: Type of memory to clear ('short_term', 'long_term', 'all')
        """
        try:
            self.db_manager.clear_memory(self.namespace, memory_type)
            logger.info(
                f"Cleared {memory_type or 'all'} memory for namespace: {self.namespace}"
            )
        except Exception as e:
            raise MemoriError(f"Failed to clear memory: {e}")

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            return self.db_manager.get_memory_stats(self.namespace)
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {}

    @property
    def is_enabled(self) -> bool:
        """Check if memory recording is enabled"""
        return self._enabled

    @property
    def session_id(self) -> str:
        """Get current session ID"""
        return self._session_id

    def get_integration_stats(self) -> List[Dict[str, Any]]:
        """Get statistics from the universal integration system"""
        try:
            stats = {
                "integration": "universal_auto_recording",
                "enabled": self._enabled,
                "session_id": self._session_id,
                "namespace": self.namespace,
                "providers": {},
            }

            # LiteLLM stats
            if LITELLM_AVAILABLE:
                stats["providers"]["litellm"] = {
                    "available": True,
                    "method": "native_callbacks",
                    "callback_registered": self._enabled,
                    "callbacks_count": len(success_callback) if self._enabled else 0,
                }
            else:
                stats["providers"]["litellm"] = {
                    "available": False,
                    "method": "native_callbacks",
                    "callback_registered": False,
                }

            # OpenAI stats
            try:
                import openai

                stats["providers"]["openai"] = {
                    "available": True,
                    "method": "auto_wrapping",
                    "wrapped": (
                        hasattr(openai.OpenAI, "_memori_wrapped")
                        if hasattr(openai, "OpenAI")
                        else False
                    ),
                }
            except ImportError:
                stats["providers"]["openai"] = {
                    "available": False,
                    "method": "auto_wrapping",
                    "wrapped": False,
                }

            # Anthropic stats
            try:
                import anthropic

                stats["providers"]["anthropic"] = {
                    "available": True,
                    "method": "auto_wrapping",
                    "wrapped": (
                        hasattr(anthropic.Anthropic, "_memori_wrapped")
                        if hasattr(anthropic, "Anthropic")
                        else False
                    ),
                }
            except ImportError:
                stats["providers"]["anthropic"] = {
                    "available": False,
                    "method": "auto_wrapping",
                    "wrapped": False,
                }

            return [stats]
        except Exception as e:
            logger.error(f"Failed to get integration stats: {e}")
            return []

    def update_user_context(
        self,
        current_projects: Optional[List[str]] = None,
        relevant_skills: Optional[List[str]] = None,
        user_preferences: Optional[List[str]] = None,
    ):
        """Update user context for better memory processing"""
        if current_projects is not None:
            self._user_context["current_projects"] = current_projects
        if relevant_skills is not None:
            self._user_context["relevant_skills"] = relevant_skills
        if user_preferences is not None:
            self._user_context["user_preferences"] = user_preferences

        logger.debug(f"Updated user context: {self._user_context}")

    def search_memories_by_category(
        self, category: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by specific category"""
        try:
            return self.db_manager.search_memories(
                query="",
                namespace=self.namespace,
                category_filter=[category],
                limit=limit,
            )
        except Exception as e:
            logger.error(f"Category search failed: {e}")
            return []

    def get_entity_memories(
        self, entity_value: str, entity_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get memories that contain a specific entity"""
        try:
            # This would use the entity index in the database
            # For now, use keyword search as fallback
            return self.db_manager.search_memories(
                query=entity_value, namespace=self.namespace, limit=limit
            )
        except Exception as e:
            logger.error(f"Entity search failed: {e}")
            return []
