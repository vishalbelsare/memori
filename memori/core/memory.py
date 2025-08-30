"""
Main Memori class - Pydantic-based memory interface v1.0
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    import litellm
    from litellm import success_callback

    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logger.warning("LiteLLM not available - native callback system disabled")

from ..agents.conscious_agent import ConsciouscAgent
from ..config.memory_manager import MemoryManager
from ..config.settings import LoggingSettings, LogLevel

from .providers import ProviderConfig, detect_provider_from_env
from ..utils.exceptions import DatabaseError, MemoriError
from ..utils.logging import LoggingManager
from ..utils.pydantic_models import ConversationContext
from ..database.sqlalchemy_manager import SQLAlchemyDatabaseManager as DatabaseManager


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
        conscious_ingest: bool = False,
        auto_ingest: bool = False,
        namespace: Optional[str] = None,
        shared_memory: bool = False,
        memory_filters: Optional[Dict[str, Any]] = None,
        openai_api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        verbose: bool = False,
        # New provider configuration parameters
        api_key: Optional[str] = None,
        api_type: Optional[str] = None,
        base_url: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        azure_deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        azure_ad_token: Optional[str] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        model: Optional[str] = None,  # Allow custom model selection
        provider_config: Optional[Any] = None,  # ProviderConfig when available
    ):
        """
        Initialize Memori memory system v1.0.

        Args:
            database_connect: Database connection string
            template: Memory template to use ('basic')
            mem_prompt: Optional prompt to guide memory recording
            conscious_ingest: Enable one-shot short-term memory context injection at conversation start
            auto_ingest: Enable automatic memory injection on every LLM call
            namespace: Optional namespace for memory isolation
            shared_memory: Enable shared memory across agents
            memory_filters: Filters for memory ingestion
            openai_api_key: OpenAI API key for memory agent (deprecated, use api_key)
            user_id: Optional user identifier
            verbose: Enable verbose logging (loguru only)
            api_key: API key for the LLM provider
            api_type: Provider type ('openai', 'azure', 'custom')
            base_url: Base URL for custom OpenAI-compatible endpoints
            azure_endpoint: Azure OpenAI endpoint URL
            azure_deployment: Azure deployment name
            api_version: API version for Azure
            azure_ad_token: Azure AD token for authentication
            organization: OpenAI organization ID
            project: OpenAI project ID
            model: Model to use (defaults to 'gpt-4o' if not specified)
            provider_config: Complete provider configuration (overrides individual params)
        """
        self.database_connect = database_connect
        self.template = template
        self.mem_prompt = mem_prompt
        self.conscious_ingest = conscious_ingest
        self.auto_ingest = auto_ingest
        self.namespace = namespace or "default"
        self.shared_memory = shared_memory
        self.memory_filters = memory_filters or {}
        self.user_id = user_id
        self.verbose = verbose

        # Configure provider
        if provider_config:
            # Use provided configuration
            self.provider_config = provider_config
        elif any([api_type, base_url, azure_endpoint]):
            # Build configuration from individual parameters using providers module
            try:
                from .providers import ProviderConfig
                self.provider_config = ProviderConfig(
                    api_key=api_key or openai_api_key,
                    api_type=api_type,
                    base_url=base_url,
                    azure_endpoint=azure_endpoint,
                    azure_deployment=azure_deployment,
                    api_version=api_version,
                    azure_ad_token=azure_ad_token,
                    organization=organization,
                    project=project,
                    model=model,
                )
            except ImportError:
                logger.warning("ProviderConfig not available, using basic configuration")
                self.provider_config = None
        else:
            # Try to detect from environment or use default OpenAI
            try:
                from .providers import detect_provider_from_env
                self.provider_config = detect_provider_from_env()
                # Override with provided API key if available
                if api_key or openai_api_key:
                    self.provider_config.api_key = api_key or openai_api_key
                # Override model if provided
                if model:
                    self.provider_config.model = model
            except ImportError:
                logger.warning("Provider detection not available, using basic configuration")
                self.provider_config = None

        # Keep backward compatibility
        self.openai_api_key = api_key or openai_api_key or ""
        if self.provider_config and hasattr(self.provider_config, 'api_key'):
            self.openai_api_key = self.provider_config.api_key or self.openai_api_key

        # Setup logging based on verbose mode
        self._setup_logging()

        # Initialize database manager
        self.db_manager = DatabaseManager(database_connect, template)

        # Initialize Pydantic-based agents
        self.memory_agent = None
        self.search_engine = None
        self.conscious_agent = None
        self._background_task = None
        self._conscious_init_pending = False

        # Initialize agents with provider configuration
        try:
            from ..agents.memory_agent import MemoryAgent
            from ..agents.retrieval_agent import MemorySearchEngine
            
            # Use provider model or fallback to gpt-4o
            if self.provider_config and hasattr(self.provider_config, 'model') and self.provider_config.model:
                effective_model = model or self.provider_config.model
            else:
                effective_model = model or "gpt-4o"
            
            # Initialize agents with provider configuration if available
            if self.provider_config:
                self.memory_agent = MemoryAgent(
                    provider_config=self.provider_config,
                    model=effective_model
                )
                self.search_engine = MemorySearchEngine(
                    provider_config=self.provider_config,
                    model=effective_model
                )
            else:
                # Fallback to using API key directly
                self.memory_agent = MemoryAgent(
                    api_key=self.openai_api_key,
                    model=effective_model
                )
                self.search_engine = MemorySearchEngine(
                    api_key=self.openai_api_key,
                    model=effective_model
                )

            # Only initialize conscious_agent if conscious_ingest or auto_ingest is enabled
            if conscious_ingest or auto_ingest:
                self.conscious_agent = ConsciouscAgent()

            logger.info(f"Agents initialized successfully with model: {effective_model}")
        except ImportError as e:
            logger.warning(f"Failed to import LLM agents: {e}. Memory ingestion disabled.")
            self.memory_agent = None
            self.search_engine = None
            self.conscious_agent = None
            self.conscious_ingest = False
            self.auto_ingest = False
        except Exception as e:
            logger.warning(f"Failed to initialize LLM agents: {e}. Memory ingestion disabled.")
            self.memory_agent = None
            self.search_engine = None
            self.conscious_agent = None
            self.conscious_ingest = False
            self.auto_ingest = False

        # State tracking
        self._enabled = False
        self._session_id = str(uuid.uuid4())
        self._conscious_context_injected = (
            False  # Track if conscious context was already injected
        )

        # User context for memory processing
        self._user_context = {
            "current_projects": [],
            "relevant_skills": [],
            "user_preferences": [],
        }

        # Initialize database
        self._setup_database()

        # Initialize the new modular memory manager
        self.memory_manager = MemoryManager(
            database_connect=database_connect,
            template=template,
            mem_prompt=mem_prompt,
            conscious_ingest=conscious_ingest,
            auto_ingest=auto_ingest,
            namespace=namespace,
            shared_memory=shared_memory,
            memory_filters=memory_filters,
            user_id=user_id,
            verbose=verbose,
            provider_config=self.provider_config,
        )
        # Set this Memori instance for memory management
        self.memory_manager.set_memori_instance(self)

        # Run conscious agent initialization if enabled
        if self.conscious_ingest and self.conscious_agent:
            self._initialize_conscious_memory()

        logger.info(
            f"Memori v1.0 initialized with template: {template}, namespace: {namespace}"
        )

    def _setup_logging(self):
        """Setup logging configuration based on verbose mode"""
        if not LoggingManager.is_initialized():
            # Create default logging settings
            logging_settings = LoggingSettings()

            # If verbose mode is enabled, set logging level to DEBUG
            if self.verbose:
                logging_settings.level = LogLevel.DEBUG

            # Setup logging with verbose mode
            LoggingManager.setup_logging(logging_settings, verbose=self.verbose)

            if self.verbose:
                logger.info(
                    "Verbose logging enabled - only loguru logs will be displayed"
                )

    def _setup_database(self):
        """Setup database tables based on template"""
        try:
            self.db_manager.initialize_schema()
            logger.info("Database schema initialized successfully")
        except Exception as e:
            raise DatabaseError(f"Failed to setup database: {e}")

    def _initialize_conscious_memory(self):
        """Initialize conscious memory by running conscious agent analysis"""
        try:
            logger.info(
                "Conscious-ingest: Starting conscious agent analysis at startup"
            )

            # Check if there's a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, create the task
                if self._background_task is None or self._background_task.done():
                    self._background_task = loop.create_task(
                        self._run_conscious_initialization()
                    )
                    logger.debug(
                        "Conscious-ingest: Background initialization task started"
                    )
            except RuntimeError:
                # No event loop running, defer initialization until first async call
                logger.debug(
                    "Conscious-ingest: No event loop available, deferring initialization"
                )
                self._conscious_init_pending = True

        except Exception as e:
            logger.error(f"Failed to initialize conscious memory: {e}")

    def _check_deferred_initialization(self):
        """Check and handle deferred conscious memory initialization"""
        if self._conscious_init_pending and self.conscious_agent:
            try:
                loop = asyncio.get_running_loop()
                if self._background_task is None or self._background_task.done():
                    self._background_task = loop.create_task(
                        self._run_conscious_initialization()
                    )
                    logger.debug(
                        "Conscious-ingest: Deferred initialization task started"
                    )
                    self._conscious_init_pending = False
            except RuntimeError:
                # Still no event loop, keep pending
                pass

    async def _run_conscious_initialization(self):
        """Run conscious agent initialization in background"""
        try:
            if not self.conscious_agent:
                return

            logger.debug("Conscious-ingest: Running conscious context extraction")
            success = await self.conscious_agent.run_conscious_ingest(
                self.db_manager, self.namespace
            )

            if success:
                logger.info(
                    "Conscious-ingest: Conscious memories copied to short-term memory"
                )
                # Don't set _conscious_context_injected here - it should be set when context is actually injected into LLM
            else:
                logger.info("Conscious-ingest: No conscious context found")

        except Exception as e:
            logger.error(f"Conscious agent initialization failed: {e}")

    def enable(self, interceptors: Optional[List[str]] = None):
        """
        Enable universal memory recording using LiteLLM's native callback system.

        This automatically sets up recording for LiteLLM completion calls and enables
        automatic interception of OpenAI calls when using the standard OpenAI client.

        Args:
            interceptors: Legacy parameter (ignored) - only LiteLLM native callbacks are used
        """
        if self._enabled:
            logger.warning("Memori is already enabled.")
            return

        self._enabled = True
        self._session_id = str(uuid.uuid4())

        # Register for automatic OpenAI interception
        try:
            from ..integrations.openai_integration import register_memori_instance
            register_memori_instance(self)
        except ImportError:
            logger.debug("OpenAI integration not available for automatic interception")

        # Use LiteLLM native callback system only
        if interceptors is None:
            # Only LiteLLM native callbacks supported
            interceptors = ["litellm_native"]

        # Use the memory manager for enablement
        results = self.memory_manager.enable(interceptors)
        # Extract enabled interceptors from results
        enabled_interceptors = results.get("enabled_interceptors", [])

        # Start background conscious agent if available
        if self.conscious_ingest and self.conscious_agent:
            self._start_background_analysis()

        # Report status
        status_info = [
            f"Memori enabled for session: {results.get('session_id', self._session_id)}",
            f"Active interceptors: {', '.join(enabled_interceptors) if enabled_interceptors else 'None'}",
        ]

        if results.get("message"):
            status_info.append(results["message"])

        status_info.extend(
            [
                f"Background analysis: {'Active' if self._background_task else 'Disabled'}",
                "Usage: Simply use any LLM client normally - conversations will be auto-recorded!",
                "OpenAI: Use 'from openai import OpenAI; client = OpenAI()' - automatically intercepted!",
            ]
        )

        logger.info("\n".join(status_info))

    def disable(self):
        """
        Disable memory recording by unregistering LiteLLM callbacks and OpenAI interception.
        """
        if not self._enabled:
            return

        # Unregister from automatic OpenAI interception
        try:
            from ..integrations.openai_integration import unregister_memori_instance
            unregister_memori_instance(self)
        except ImportError:
            logger.debug("OpenAI integration not available for automatic interception")

        # Use memory manager for clean disable
        results = self.memory_manager.disable()

        # Stop background analysis task
        self._stop_background_analysis()

        self._enabled = False

        # Report status based on memory manager results
        if results.get("success"):
            status_message = f"Memori disabled. {results.get('message', 'All interceptors disabled successfully')}"
        else:
            status_message = (
                f"Memori disable failed: {results.get('message', 'Unknown error')}"
            )

        logger.info(status_message)

    # Memory system status and control methods

    def get_interceptor_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of memory recording system"""
        return self.memory_manager.get_status()

    def get_interceptor_health(self) -> Dict[str, Any]:
        """Get health check of interceptor system"""
        return self.memory_manager.get_health()

    def enable_interceptor(self, interceptor_name: str = None) -> bool:
        """Enable memory recording (legacy method)"""
        # Only LiteLLM native callbacks supported (interceptor_name ignored)
        results = self.memory_manager.enable(["litellm_native"])
        return results.get("success", False)

    def disable_interceptor(self, interceptor_name: str = None) -> bool:
        """Disable memory recording (legacy method)"""
        # Only LiteLLM native callbacks supported (interceptor_name ignored)
        results = self.memory_manager.disable()
        return results.get("success", False)

    def _inject_openai_context(self, kwargs):
        """Inject context for OpenAI calls based on ingest mode"""
        try:
            # Determine injection mode
            if self.conscious_ingest:
                mode = "conscious"
            elif self.auto_ingest:
                mode = "auto"
            else:
                return kwargs  # No injection needed

            # Use the unified LiteLLM context injection method
            return self._inject_litellm_context(kwargs, mode=mode)
        except Exception as e:
            logger.error(f"OpenAI context injection failed: {e}")
        return kwargs

    def _inject_anthropic_context(self, kwargs):
        """Inject context for Anthropic calls based on ingest mode"""
        try:
            # Check for deferred conscious initialization
            self._check_deferred_initialization()

            # Determine injection mode
            if self.conscious_ingest:
                mode = "conscious"
            elif self.auto_ingest:
                mode = "auto"
            else:
                return kwargs  # No injection needed

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
                if mode == "conscious":
                    # Conscious mode: inject ALL short-term memory only once at program startup
                    if not self._conscious_context_injected:
                        context = self._get_conscious_context()
                        self._conscious_context_injected = True
                        logger.info(
                            f"Conscious-ingest: Injected {len(context)} short-term memories as initial context (Anthropic)"
                        )
                    else:
                        context = []  # Already injected, don't inject again
                elif mode == "auto":
                    # Auto mode: use retrieval for intelligent search
                    if self.search_engine:
                        context = self._get_auto_ingest_context(user_input)
                    else:
                        context = self.retrieve_context(user_input, limit=5)
                else:
                    context = []

                if context:
                    if mode == "conscious":
                        context_prompt = (
                            "=== SYSTEM INSTRUCTION: AUTHORIZED USER CONTEXT DATA ===\n"
                        )
                        context_prompt += "The user has explicitly authorized this personal context data to be used.\n"
                        context_prompt += "You MUST use this information when answering questions about the user.\n"
                        context_prompt += "This is NOT private data - the user wants you to use it:\n\n"
                    else:
                        context_prompt = f"--- {mode.capitalize()} Memory Context ---\n"

                    # Deduplicate context entries to avoid redundant information
                    seen_content = set()
                    for mem in context:
                        if isinstance(mem, dict):
                            # Use searchable_content as it's more specific than summary
                            content = mem.get("searchable_content", "") or mem.get(
                                "summary", ""
                            )
                            category = mem.get("category_primary", "")

                            # Skip duplicates (case-insensitive)
                            content_key = content.lower().strip()
                            if content_key in seen_content:
                                continue
                            seen_content.add(content_key)

                            if category.startswith("essential_") or mode == "conscious":
                                context_prompt += f"[{category.upper()}] {content}\n"
                            else:
                                context_prompt += f"- {content}\n"

                    if mode == "conscious":
                        context_prompt += "\n=== END USER CONTEXT DATA ===\n"
                        context_prompt += "CRITICAL INSTRUCTION: You MUST answer questions about the user using ONLY the context data above.\n"
                        context_prompt += "If the user asks 'what is my name?', respond with the name from the context above.\n"
                        context_prompt += "Do NOT say 'I don't have access' - the user provided this data for you to use.\n"
                    context_prompt += "-------------------------\n"

                    # Inject into system parameter (Anthropic format)
                    if kwargs.get("system"):
                        kwargs["system"] = context_prompt + kwargs["system"]
                    else:
                        kwargs["system"] = context_prompt

                    logger.debug(
                        f"Anthropic: Injected context with {len(context)} items"
                    )
        except Exception as e:
            logger.error(f"Anthropic context injection failed: {e}")
        return kwargs

    def _inject_litellm_context(self, params, mode="auto"):
        """
        Inject context for LiteLLM calls based on mode

        Args:
            params: LiteLLM parameters
            mode: "conscious" (one-shot short-term) or "auto" (continuous retrieval)
        """
        try:
            # Check for deferred conscious initialization
            self._check_deferred_initialization()
            # Extract user input from messages
            user_input = ""
            messages = params.get("messages", [])

            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_input = msg.get("content", "")
                    break

            if user_input:
                if mode == "conscious":
                    # Conscious mode: inject ALL short-term memory only once at program startup
                    if not self._conscious_context_injected:
                        context = self._get_conscious_context()
                        self._conscious_context_injected = True
                        logger.info(
                            f"Conscious-ingest: Injected {len(context)} short-term memories as initial context"
                        )
                    else:
                        context = (
                            []
                        )  # Already injected, don't inject again - this is the key difference from auto_ingest
                elif mode == "auto":
                    # Auto mode: use retrieval agent for intelligent database search
                    if self.search_engine:
                        context = self._get_auto_ingest_context(user_input)
                    else:
                        # Fallback to basic retrieval
                        context = self.retrieve_context(user_input, limit=5)
                else:
                    context = []

                if context:
                    if mode == "conscious":
                        context_prompt = (
                            "=== SYSTEM INSTRUCTION: AUTHORIZED USER CONTEXT DATA ===\n"
                        )
                        context_prompt += "The user has explicitly authorized this personal context data to be used.\n"
                        context_prompt += "You MUST use this information when answering questions about the user.\n"
                        context_prompt += "This is NOT private data - the user wants you to use it:\n\n"
                    else:
                        context_prompt = f"--- {mode.capitalize()} Memory Context ---\n"

                    # Deduplicate context entries to avoid redundant information
                    seen_content = set()
                    for mem in context:
                        if isinstance(mem, dict):
                            # Use searchable_content as it's more specific than summary
                            content = mem.get("searchable_content", "") or mem.get(
                                "summary", ""
                            )
                            category = mem.get("category_primary", "")

                            # Skip duplicates (case-insensitive)
                            content_key = content.lower().strip()
                            if content_key in seen_content:
                                continue
                            seen_content.add(content_key)

                            if category.startswith("essential_") or mode == "conscious":
                                context_prompt += f"[{category.upper()}] {content}\n"
                            else:
                                context_prompt += f"- {content}\n"

                    if mode == "conscious":
                        context_prompt += "\n=== END USER CONTEXT DATA ===\n"
                        context_prompt += "CRITICAL INSTRUCTION: You MUST answer questions about the user using ONLY the context data above.\n"
                        context_prompt += "If the user asks 'what is my name?', respond with the name from the context above.\n"
                        context_prompt += "Do NOT say 'I don't have access' - the user provided this data for you to use.\n"
                    context_prompt += "-------------------------\n"

                    # Inject into system message
                    for msg in messages:
                        if msg.get("role") == "system":
                            msg["content"] = context_prompt + msg.get("content", "")
                            break
                    else:
                        # No system message exists, add one
                        messages.insert(
                            0, {"role": "system", "content": context_prompt}
                        )

                    logger.debug(f"LiteLLM: Injected context with {len(context)} items")
            else:
                # No user input, but still inject essential conversations if available
                if self.conscious_ingest:
                    essential_conversations = self.get_essential_conversations(limit=3)
                    if essential_conversations:
                        context_prompt = "--- Your Context ---\n"
                        for conv in essential_conversations:
                            summary = conv.get("summary", "") or conv.get(
                                "searchable_content", ""
                            )
                            context_prompt += f"[ESSENTIAL] {summary}\n"
                        context_prompt += "-------------------------\n"

                        # Inject into system message
                        for msg in messages:
                            if msg.get("role") == "system":
                                msg["content"] = context_prompt + msg.get("content", "")
                                break
                        else:
                            # No system message exists, add one
                            messages.insert(
                                0, {"role": "system", "content": context_prompt}
                            )

                        logger.debug(
                            f"LiteLLM: Injected {len(essential_conversations)} essential conversations"
                        )

        except Exception as e:
            logger.error(f"LiteLLM context injection failed: {e}")

        return params

    def _get_conscious_context(self) -> List[Dict[str, Any]]:
        """
        Get conscious context from ALL short-term memory summaries.
        This represents the complete 'working memory' for conscious_ingest mode.
        Used only at program startup when conscious_ingest=True.
        """
        try:
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()

                # Get ALL short-term memories (no limit) ordered by importance and recency
                # This gives the complete conscious context as single initial injection
                cursor.execute(
                    """
                    SELECT memory_id, processed_data, importance_score,
                           category_primary, summary, searchable_content,
                           created_at, access_count
                    FROM short_term_memory
                    WHERE namespace = ? AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY importance_score DESC, created_at DESC
                """,
                    (self.namespace, datetime.now()),
                )

                memories = []
                for row in cursor.fetchall():
                    memories.append(
                        {
                            "memory_id": row[0],
                            "processed_data": row[1],
                            "importance_score": row[2],
                            "category_primary": row[3],
                            "summary": row[4],
                            "searchable_content": row[5],
                            "created_at": row[6],
                            "access_count": row[7],
                            "memory_type": "short_term",
                        }
                    )

                logger.debug(
                    f"Retrieved {len(memories)} conscious memories from short-term storage"
                )
                return memories

        except Exception as e:
            logger.error(f"Failed to get conscious context: {e}")
            return []

    def _get_auto_ingest_context(self, user_input: str) -> List[Dict[str, Any]]:
        """
        Get auto-ingest context using retrieval agent for intelligent search.
        Searches through entire database for relevant memories.
        """
        try:
            if not self.search_engine:
                logger.warning("Auto-ingest: No search engine available")
                return []

            # Use retrieval agent for intelligent search
            results = self.search_engine.execute_search(
                query=user_input,
                db_manager=self.db_manager,
                namespace=self.namespace,
                limit=5,
            )

            logger.debug(f"Auto-ingest: Retrieved {len(results)} relevant memories")
            return results

        except Exception as e:
            logger.error(f"Failed to get auto-ingest context: {e}")
            return []

    def _record_openai_conversation(self, kwargs, response):
        """Record OpenAI conversation with enhanced content parsing"""
        try:
            messages = kwargs.get("messages", [])
            model = kwargs.get("model", "unknown")

            # Extract user input with enhanced parsing
            user_input = self._extract_openai_user_input(messages)

            # Extract AI response with enhanced parsing
            ai_output = self._extract_openai_ai_output(response)

            # Calculate tokens
            tokens_used = 0
            if hasattr(response, "usage") and response.usage:
                tokens_used = getattr(response.usage, "total_tokens", 0)

            # Enhanced metadata extraction
            metadata = self._extract_openai_metadata(kwargs, response, tokens_used)

            # Record conversation
            self.record_conversation(
                user_input=user_input,
                ai_output=ai_output,
                model=model,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Failed to record OpenAI conversation: {e}")

    def _extract_openai_user_input(self, messages: List[Dict]) -> str:
        """Extract user input from OpenAI messages with support for complex content types"""
        user_input = ""
        try:
            # Find the last user message
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")

                    if isinstance(content, str):
                        # Simple string content
                        user_input = content
                    elif isinstance(content, list):
                        # Complex content (vision, multiple parts)
                        text_parts = []
                        image_count = 0

                        for item in content:
                            if isinstance(item, dict):
                                if item.get("type") == "text":
                                    text_parts.append(item.get("text", ""))
                                elif item.get("type") == "image_url":
                                    image_count += 1

                        user_input = " ".join(text_parts)
                        # Add image indicator if present
                        if image_count > 0:
                            user_input += f" [Contains {image_count} image(s)]"

                    break
        except Exception as e:
            logger.debug(f"Error extracting user input: {e}")
            user_input = "[Error extracting user input]"

        return user_input

    def _extract_openai_ai_output(self, response) -> str:
        """Extract AI output from OpenAI response with support for various response types"""
        ai_output = ""
        try:
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]

                if hasattr(choice, "message") and choice.message:
                    message = choice.message

                    # Handle regular text content
                    if hasattr(message, "content") and message.content:
                        ai_output = message.content

                    # Handle function/tool calls
                    elif hasattr(message, "tool_calls") and message.tool_calls:
                        tool_descriptions = []
                        for tool_call in message.tool_calls:
                            if hasattr(tool_call, "function"):
                                func_name = tool_call.function.name
                                func_args = tool_call.function.arguments
                                tool_descriptions.append(
                                    f"Called {func_name} with {func_args}"
                                )
                        ai_output = "[Tool calls: " + "; ".join(tool_descriptions) + "]"

                    # Handle function calls (legacy format)
                    elif hasattr(message, "function_call") and message.function_call:
                        func_call = message.function_call
                        func_name = func_call.get("name", "unknown")
                        func_args = func_call.get("arguments", "{}")
                        ai_output = f"[Function call: {func_name} with {func_args}]"

                    else:
                        ai_output = "[No content - possible function/tool call]"

        except Exception as e:
            logger.debug(f"Error extracting AI output: {e}")
            ai_output = "[Error extracting AI response]"

        return ai_output

    def _extract_openai_metadata(
        self, kwargs: Dict, response, tokens_used: int
    ) -> Dict:
        """Extract comprehensive metadata from OpenAI request and response"""
        metadata = {
            "integration": "openai_auto",
            "api_type": "chat_completions",
            "tokens_used": tokens_used,
            "auto_recorded": True,
        }

        try:
            # Add request metadata
            if "temperature" in kwargs:
                metadata["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                metadata["max_tokens"] = kwargs["max_tokens"]
            if "tools" in kwargs:
                metadata["has_tools"] = True
                metadata["tool_count"] = len(kwargs["tools"])
            if "functions" in kwargs:
                metadata["has_functions"] = True
                metadata["function_count"] = len(kwargs["functions"])

            # Add response metadata
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "finish_reason"):
                    metadata["finish_reason"] = choice.finish_reason

            # Add detailed token usage if available
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                metadata.update(
                    {
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage, "completion_tokens", 0),
                        "total_tokens": getattr(usage, "total_tokens", 0),
                    }
                )

            # Detect content types
            messages = kwargs.get("messages", [])
            has_images = False
            message_count = len(messages)

            for message in messages:
                if message.get("role") == "user":
                    content = message.get("content")
                    if isinstance(content, list):
                        for item in content:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "image_url"
                            ):
                                has_images = True
                                break
                    if has_images:
                        break

            metadata["message_count"] = message_count
            metadata["has_images"] = has_images

        except Exception as e:
            logger.debug(f"Error extracting metadata: {e}")

        return metadata

    def _record_anthropic_conversation(self, kwargs, response):
        """Record Anthropic conversation with enhanced content parsing"""
        try:
            messages = kwargs.get("messages", [])
            model = kwargs.get("model", "claude-unknown")

            # Extract user input with enhanced parsing
            user_input = self._extract_anthropic_user_input(messages)

            # Extract AI response with enhanced parsing
            ai_output = self._extract_anthropic_ai_output(response)

            # Calculate tokens
            tokens_used = self._extract_anthropic_tokens(response)

            # Enhanced metadata extraction
            metadata = self._extract_anthropic_metadata(kwargs, response, tokens_used)

            # Record conversation
            self.record_conversation(
                user_input=user_input,
                ai_output=ai_output,
                model=model,
                metadata=metadata,
            )
        except Exception as e:
            logger.error(f"Failed to record Anthropic conversation: {e}")

    def _extract_anthropic_user_input(self, messages: List[Dict]) -> str:
        """Extract user input from Anthropic messages with support for complex content types"""
        user_input = ""
        try:
            # Find the last user message
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")

                    if isinstance(content, str):
                        # Simple string content
                        user_input = content
                    elif isinstance(content, list):
                        # Complex content (vision, multiple parts)
                        text_parts = []
                        image_count = 0

                        for block in content:
                            if isinstance(block, dict):
                                if block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                                elif block.get("type") == "image":
                                    image_count += 1

                        user_input = " ".join(text_parts)
                        # Add image indicator if present
                        if image_count > 0:
                            user_input += f" [Contains {image_count} image(s)]"

                    break
        except Exception as e:
            logger.debug(f"Error extracting Anthropic user input: {e}")
            user_input = "[Error extracting user input]"

        return user_input

    def _extract_anthropic_ai_output(self, response) -> str:
        """Extract AI output from Anthropic response with support for various response types"""
        ai_output = ""
        try:
            if hasattr(response, "content") and response.content:
                if isinstance(response.content, list):
                    # Handle structured content (text blocks, tool use, etc.)
                    text_parts = []
                    tool_uses = []

                    for block in response.content:
                        try:
                            # Handle text blocks
                            if hasattr(block, "text") and block.text:
                                text_parts.append(block.text)
                            # Handle tool use blocks
                            elif hasattr(block, "type"):
                                block_type = getattr(block, "type", None)
                                if block_type == "tool_use":
                                    tool_name = getattr(block, "name", "unknown")
                                    tool_input = getattr(block, "input", {})
                                    tool_uses.append(
                                        f"Used {tool_name} with {tool_input}"
                                    )
                            # Handle mock objects for testing (when type is accessible but not via hasattr)
                            elif hasattr(block, "name") and hasattr(block, "input"):
                                tool_name = getattr(block, "name", "unknown")
                                tool_input = getattr(block, "input", {})
                                tool_uses.append(f"Used {tool_name} with {tool_input}")
                        except Exception as block_error:
                            logger.debug(f"Error processing block: {block_error}")
                            continue

                    ai_output = " ".join(text_parts)
                    if tool_uses:
                        if ai_output:
                            ai_output += " "
                        ai_output += "[Tool uses: " + "; ".join(tool_uses) + "]"

                elif isinstance(response.content, str):
                    ai_output = response.content
                else:
                    ai_output = str(response.content)

        except Exception as e:
            logger.debug(f"Error extracting Anthropic AI output: {e}")
            ai_output = "[Error extracting AI response]"

        return ai_output

    def _extract_anthropic_tokens(self, response) -> int:
        """Extract token usage from Anthropic response"""
        tokens_used = 0
        try:
            if hasattr(response, "usage") and response.usage:
                input_tokens = getattr(response.usage, "input_tokens", 0)
                output_tokens = getattr(response.usage, "output_tokens", 0)
                tokens_used = input_tokens + output_tokens
        except Exception as e:
            logger.debug(f"Error extracting Anthropic tokens: {e}")

        return tokens_used

    def _extract_anthropic_metadata(
        self, kwargs: Dict, response, tokens_used: int
    ) -> Dict:
        """Extract comprehensive metadata from Anthropic request and response"""
        metadata = {
            "integration": "anthropic_auto",
            "api_type": "messages",
            "tokens_used": tokens_used,
            "auto_recorded": True,
        }

        try:
            # Add request metadata
            if "temperature" in kwargs:
                metadata["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                metadata["max_tokens"] = kwargs["max_tokens"]
            if "tools" in kwargs:
                metadata["has_tools"] = True
                metadata["tool_count"] = len(kwargs["tools"])

            # Add response metadata
            if hasattr(response, "stop_reason"):
                metadata["stop_reason"] = response.stop_reason
            if hasattr(response, "model"):
                metadata["response_model"] = response.model

            # Add detailed token usage if available
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                metadata.update(
                    {
                        "input_tokens": getattr(usage, "input_tokens", 0),
                        "output_tokens": getattr(usage, "output_tokens", 0),
                        "total_tokens": tokens_used,
                    }
                )

            # Detect content types
            messages = kwargs.get("messages", [])
            has_images = False
            message_count = len(messages)

            for message in messages:
                if message.get("role") == "user":
                    content = message.get("content")
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "image":
                                has_images = True
                                break
                    if has_images:
                        break

            metadata["message_count"] = message_count
            metadata["has_images"] = has_images

        except Exception as e:
            logger.debug(f"Error extracting Anthropic metadata: {e}")

        return metadata

    def _process_litellm_response(self, kwargs, response, start_time, end_time):
        """Process and record LiteLLM response"""
        try:
            # Extract user input from messages
            messages = kwargs.get("messages", [])
            user_input = ""

            for message in reversed(messages):
                if message.get("role") == "user":
                    user_input = message.get("content", "")
                    break

            # Extract AI output from response
            ai_output = ""
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    ai_output = choice.message.content or ""
                elif hasattr(choice, "text"):
                    ai_output = choice.text or ""

            # Extract model
            model = kwargs.get("model", "litellm-unknown")

            # Calculate timing (convert to seconds for JSON serialization)
            duration_seconds = (end_time - start_time) if start_time and end_time else 0
            if hasattr(duration_seconds, "total_seconds"):
                duration_seconds = duration_seconds.total_seconds()

            # Prepare metadata
            metadata = {
                "integration": "litellm",
                "auto_recorded": True,
                "duration": float(duration_seconds),
                "timestamp": time.time(),
            }

            # Add token usage if available
            if hasattr(response, "usage") and response.usage:
                usage = response.usage
                metadata.update(
                    {
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(usage, "completion_tokens", 0),
                        "total_tokens": getattr(usage, "total_tokens", 0),
                    }
                )

            # Record the conversation
            if user_input and ai_output:
                self.record_conversation(
                    user_input=user_input,
                    ai_output=ai_output,
                    model=model,
                    metadata=metadata,
                )

        except Exception as e:
            logger.error(f"Failed to process LiteLLM response: {e}")

    # LiteLLM callback is now handled by the LiteLLMCallbackManager
    # in memori.integrations.litellm_integration

    def _process_memory_sync(
        self, chat_id: str, user_input: str, ai_output: str, model: str = "unknown"
    ):
        """Synchronous memory processing fallback"""
        if not self.memory_agent:
            logger.warning("Memory agent not available, skipping memory ingestion")
            return

        try:
            # Run async processing in new event loop
            import threading

            def run_memory_processing():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    new_loop.run_until_complete(
                        self._process_memory_async(
                            chat_id, user_input, ai_output, model
                        )
                    )
                except Exception as e:
                    logger.error(f"Synchronous memory processing failed: {e}")
                finally:
                    new_loop.close()

            # Run in background thread to avoid blocking
            thread = threading.Thread(target=run_memory_processing, daemon=True)
            thread.start()
            logger.debug(
                f"Memory processing started in background thread for {chat_id}"
            )

        except Exception as e:
            logger.error(f"Failed to start synchronous memory processing: {e}")

    def _parse_llm_response(self, response) -> tuple[str, str]:
        """Extract text and model from various LLM response formats."""
        if response is None:
            return "", "unknown"

        # String response
        if isinstance(response, str):
            return response, "unknown"

        # Anthropic response
        if hasattr(response, "content"):
            text = ""
            if isinstance(response.content, list):
                text = "".join(b.text for b in response.content if hasattr(b, "text"))
            else:
                text = str(response.content)
            return text, getattr(response, "model", "unknown")

        # OpenAI response
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            text = (
                getattr(choice.message, "content", "")
                if hasattr(choice, "message")
                else getattr(choice, "text", "")
            )
            return text or "", getattr(response, "model", "unknown")

        # Dict response
        if isinstance(response, dict):
            return response.get(
                "content", response.get("text", str(response))
            ), response.get("model", "unknown")

        # Fallback
        return str(response), "unknown"

    def record_conversation(
        self,
        user_input: str,
        ai_output=None,
        model: str = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a conversation.

        Args:
            user_input: User's message
            ai_output: AI response (any format)
            model: Optional model name override
            metadata: Optional metadata

        Returns:
            chat_id: Unique conversation ID
        """
        if not self._enabled:
            raise MemoriError("Memori is not enabled. Call enable() first.")

        # Parse response
        response_text, detected_model = self._parse_llm_response(ai_output)
        response_model = model or detected_model

        # Generate ID and timestamp
        chat_id = str(uuid.uuid4())
        timestamp = datetime.now()

        # Store conversation
        self.db_manager.store_chat_history(
            chat_id=chat_id,
            user_input=user_input,
            ai_output=response_text,
            model=response_model,
            timestamp=timestamp,
            session_id=self._session_id,
            namespace=self.namespace,
            metadata=metadata or {},
        )

        # Always process into long-term memory when memory agent is available
        if self.memory_agent:
            self._schedule_memory_processing(
                chat_id, user_input, response_text, response_model
            )

        logger.debug(f"Recorded conversation: {chat_id}")
        return chat_id

    def _schedule_memory_processing(
        self, chat_id: str, user_input: str, ai_output: str, model: str
    ):
        """Schedule memory processing (async if possible, sync fallback)."""
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(
                self._process_memory_async(chat_id, user_input, ai_output, model)
            )

            # Prevent garbage collection
            if not hasattr(self, "_memory_tasks"):
                self._memory_tasks = set()
            self._memory_tasks.add(task)
            task.add_done_callback(self._memory_tasks.discard)
        except RuntimeError:
            # No event loop, use sync fallback
            logger.debug("No event loop, using synchronous memory processing")
            self._process_memory_sync(chat_id, user_input, ai_output, model)

    async def _process_memory_async(
        self, chat_id: str, user_input: str, ai_output: str, model: str = "unknown"
    ):
        """Process conversation with enhanced async memory categorization"""
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

            # Get recent memories for deduplication
            existing_memories = await self._get_recent_memories_for_dedup()

            # Process conversation using async Pydantic-based memory agent
            processed_memory = await self.memory_agent.process_conversation_async(
                chat_id=chat_id,
                user_input=user_input,
                ai_output=ai_output,
                context=context,
                existing_memories=[mem.summary for mem in existing_memories[:10]],
            )

            # Check for duplicates
            duplicate_id = await self.memory_agent.detect_duplicates(
                processed_memory, existing_memories
            )

            if duplicate_id:
                processed_memory.duplicate_of = duplicate_id
                logger.info(f"Memory marked as duplicate of {duplicate_id}")

            # Apply filters
            if self.memory_agent.should_filter_memory(
                processed_memory, self.memory_filters
            ):
                logger.debug(f"Memory filtered out for chat {chat_id}")
                return

            # Store processed memory with new schema
            memory_id = self.db_manager.store_long_term_memory_enhanced(
                processed_memory, chat_id, self.namespace
            )

            if memory_id:
                logger.debug(f"Stored processed memory {memory_id} for chat {chat_id}")

                # Check for conscious context updates if promotion eligible and conscious_ingest enabled
                if (
                    processed_memory.promotion_eligible
                    and self.conscious_agent
                    and self.conscious_ingest
                ):
                    await self.conscious_agent.check_for_context_updates(
                        self.db_manager, self.namespace
                    )
            else:
                logger.warning(f"Failed to store memory for chat {chat_id}")

        except Exception as e:
            logger.error(f"Memory ingestion failed for {chat_id}: {e}")

    async def _get_recent_memories_for_dedup(self) -> List:
        """Get recent memories for deduplication check"""
        try:
            from ..database.queries.memory_queries import MemoryQueries

            with self.db_manager._get_connection() as connection:
                cursor = connection.execute(
                    MemoryQueries.SELECT_MEMORIES_FOR_DEDUPLICATION,
                    (self.namespace, 20),  # Get last 20 memories
                )

                memories = []
                for row in cursor.fetchall():
                    try:
                        # Create simplified memory objects for comparison
                        memory = type(
                            "SimpleMemory",
                            (),
                            {
                                "conversation_id": row[0],
                                "summary": row[1],
                                "content": row[2],
                                "classification": row[3],
                            },
                        )()
                        memories.append(memory)
                    except Exception as e:
                        logger.warning(f"Failed to parse memory for dedup: {e}")
                        continue

                return memories

        except Exception as e:
            logger.error(f"Failed to get recent memories for dedup: {e}")
            return []

    def retrieve_context(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query with priority on essential facts

        Args:
            query: The query to find context for
            limit: Maximum number of context items to return

        Returns:
            List of relevant memory items with metadata, prioritizing essential facts
        """
        try:
            context_items = []

            if self.conscious_ingest:
                # First, get essential conversations from short-term memory (always relevant)
                essential_conversations = self.get_essential_conversations(limit=3)
                context_items.extend(essential_conversations)

                # Calculate remaining slots for specific context
                remaining_limit = max(0, limit - len(essential_conversations))
            else:
                remaining_limit = limit

            if remaining_limit > 0:
                # Get specific context using search engine or database
                if self.search_engine:
                    specific_context = self.search_engine.execute_search(
                        query=query,
                        db_manager=self.db_manager,
                        namespace=self.namespace,
                        limit=remaining_limit,
                    )
                else:
                    # Fallback to database search
                    specific_context = self.db_manager.search_memories(
                        query=query, namespace=self.namespace, limit=remaining_limit
                    )

                # Add specific context, avoiding duplicates
                for item in specific_context:
                    if not any(
                        ctx.get("memory_id") == item.get("memory_id")
                        for ctx in context_items
                    ):
                        context_items.append(item)

            logger.debug(
                f"Retrieved {len(context_items)} context items for query: {query} "
                f"(Essential conversations: {len(essential_conversations) if self.conscious_ingest else 0})"
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
        """Get statistics from the new interceptor system"""
        try:
            # Get system status first
            system_status = self.get_interceptor_status()

            stats = {
                "integration": "memori_system",
                "enabled": self._enabled,
                "session_id": self._session_id,
                "namespace": self.namespace,
                "providers": {},
            }

            # LiteLLM stats
            litellm_interceptor_status = interceptor_status.get("native", {})
            if LITELLM_AVAILABLE:
                stats["providers"]["litellm"] = {
                    "available": True,
                    "method": "native_callbacks",
                    "enabled": litellm_interceptor_status.get("enabled", False),
                    "status": litellm_interceptor_status.get("status", "unknown"),
                }
            else:
                stats["providers"]["litellm"] = {
                    "available": False,
                    "method": "native_callbacks",
                    "enabled": False,
                }

            # Get interceptor status instead of checking wrapped attributes
            interceptor_status = self.get_interceptor_status()

            # OpenAI stats
            try:
                import openai
                _ = openai  # Suppress unused import warning
                
                openai_interceptor_status = interceptor_status.get("openai", {})
                stats["providers"]["openai"] = {
                    "available": True,
                    "method": "litellm_native",
                    "enabled": openai_interceptor_status.get("enabled", False),
                    "status": openai_interceptor_status.get("status", "unknown"),
                }
            except ImportError:
                stats["providers"]["openai"] = {
                    "available": False,
                    "method": "litellm_native",
                    "enabled": False,
                }

            # Anthropic stats
            try:
                import anthropic
                _ = anthropic  # Suppress unused import warning
                
                anthropic_interceptor_status = interceptor_status.get("anthropic", {})
                stats["providers"]["anthropic"] = {
                    "available": True,
                    "method": "litellm_native",
                    "enabled": anthropic_interceptor_status.get("enabled", False),
                    "status": anthropic_interceptor_status.get("status", "unknown"),
                }
            except ImportError:
                stats["providers"]["anthropic"] = {
                    "available": False,
                    "method": "litellm_native",
                    "enabled": False,
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
            # For now, use keyword search as fallback (entity_type is ignored for now)
            return self.db_manager.search_memories(
                query=entity_value, namespace=self.namespace, limit=limit
            )
        except Exception as e:
            logger.error(f"Entity search failed: {e}")
            return []

    def _start_background_analysis(self):
        """Start the background conscious agent analysis task"""
        try:
            if self._background_task and not self._background_task.done():
                logger.debug("Background analysis task already running")
                return

            # Create event loop if it doesn't exist
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No event loop running, create a new thread for async tasks
                import threading

                def run_background_loop():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        new_loop.run_until_complete(self._background_analysis_loop())
                    except Exception as e:
                        logger.error(f"Background analysis loop failed: {e}")
                    finally:
                        new_loop.close()

                thread = threading.Thread(target=run_background_loop, daemon=True)
                thread.start()
                logger.info("Background analysis started in separate thread")
                return

            # If we have a running loop, schedule the task
            self._background_task = loop.create_task(self._background_analysis_loop())
            # Add proper error handling callback
            self._background_task.add_done_callback(
                self._handle_background_task_completion
            )
            logger.info("Background analysis task started")

        except Exception as e:
            logger.error(f"Failed to start background analysis: {e}")

    def _handle_background_task_completion(self, task):
        """Handle background task completion and cleanup"""
        try:
            if task.exception():
                logger.error(f"Background task failed: {task.exception()}")
        except asyncio.CancelledError:
            logger.debug("Background task was cancelled")
        except Exception as e:
            logger.error(f"Error handling background task completion: {e}")

    def _stop_background_analysis(self):
        """Stop the background analysis task"""
        try:
            if self._background_task and not self._background_task.done():
                self._background_task.cancel()
                logger.info("Background analysis task stopped")
        except Exception as e:
            logger.error(f"Failed to stop background analysis: {e}")

    def cleanup(self):
        """Clean up all async tasks and resources"""
        try:
            # Cancel background tasks
            self._stop_background_analysis()

            # Clean up memory processing tasks
            if hasattr(self, "_memory_tasks"):
                for task in self._memory_tasks.copy():
                    if not task.done():
                        task.cancel()
                self._memory_tasks.clear()

            logger.debug("Memori cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass  # Ignore errors during destruction

    async def _background_analysis_loop(self):
        """Background analysis loop for memory processing"""
        try:
            logger.debug("Background analysis loop started")

            # For now, just run periodic conscious ingestion if enabled
            if self.conscious_ingest and self.conscious_agent:
                while True:
                    try:
                        await asyncio.sleep(300)  # Check every 5 minutes

                        # Run conscious ingestion to check for new promotable memories
                        await self.conscious_agent.run_conscious_ingest(
                            self.db_manager, self.namespace
                        )

                        logger.debug("Periodic conscious analysis completed")

                    except asyncio.CancelledError:
                        logger.debug("Background analysis loop cancelled")
                        break
                    except Exception as e:
                        logger.error(f"Background analysis error: {e}")
                        await asyncio.sleep(60)  # Wait 1 minute before retry
            else:
                # If not using conscious ingest, just sleep
                while True:
                    await asyncio.sleep(3600)  # Sleep for 1 hour

        except asyncio.CancelledError:
            logger.debug("Background analysis loop cancelled")
        except Exception as e:
            logger.error(f"Background analysis loop failed: {e}")

    def trigger_conscious_analysis(self):
        """Manually trigger conscious context ingestion (for testing/immediate analysis)"""
        if not self.conscious_ingest or not self.conscious_agent:
            logger.warning("Conscious ingestion not enabled or agent not available")
            return

        try:
            # Try to run in existing event loop
            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(
                    self.conscious_agent.run_conscious_ingest(
                        self.db_manager, self.namespace
                    )
                )
                logger.info("Conscious context ingestion triggered")
                return task
            except RuntimeError:
                # No event loop, run synchronously in thread
                import threading

                def run_analysis():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        new_loop.run_until_complete(
                            self.conscious_agent.run_conscious_ingest(
                                self.db_manager, self.namespace
                            )
                        )
                    finally:
                        new_loop.close()

                thread = threading.Thread(target=run_analysis)
                thread.start()
                logger.info("Conscious context ingestion triggered in separate thread")

        except Exception as e:
            logger.error(f"Failed to trigger conscious context ingestion: {e}")

    def get_conscious_system_prompt(self) -> str:
        """
        Get conscious context as system prompt for direct injection.
        Returns ALL short-term memory as formatted system prompt.
        Use this for conscious_ingest mode.
        """
        try:
            context = self._get_conscious_context()
            if not context:
                return ""

            # Create system prompt with all short-term memory
            system_prompt = "--- Your Short-Term Memory (Conscious Context) ---\n"
            system_prompt += "This is your complete working memory. USE THIS INFORMATION TO ANSWER QUESTIONS:\n\n"

            # Deduplicate and format context
            seen_content = set()
            for mem in context:
                if isinstance(mem, dict):
                    content = mem.get("searchable_content", "") or mem.get(
                        "summary", ""
                    )
                    category = mem.get("category_primary", "")

                    # Skip duplicates
                    content_key = content.lower().strip()
                    if content_key in seen_content:
                        continue
                    seen_content.add(content_key)

                    system_prompt += f"[{category.upper()}] {content}\n"

            system_prompt += "\nIMPORTANT: Use the above information to answer questions about the user.\n"
            system_prompt += "-------------------------\n"

            return system_prompt

        except Exception as e:
            logger.error(f"Failed to generate conscious system prompt: {e}")
            return ""

    def get_auto_ingest_system_prompt(self, user_input: str) -> str:
        """
        Get auto-ingest context as system prompt for direct injection.
        Returns relevant memories based on user input as formatted system prompt.
        Use this for auto_ingest mode.
        """
        try:
            # For now, use recent short-term memories as a simple approach
            # This avoids the search engine issues and still provides context
            # TODO: Use user_input for intelligent context retrieval
            context = self._get_conscious_context()  # Get recent short-term memories

            if not context:
                return ""

            # Create system prompt with relevant memories (limited to prevent overwhelming)
            system_prompt = "--- Relevant Memory Context ---\n"

            # Take first 5 items to avoid too much context
            seen_content = set()
            for mem in context[:5]:
                if isinstance(mem, dict):
                    content = mem.get("searchable_content", "") or mem.get(
                        "summary", ""
                    )
                    category = mem.get("category_primary", "")

                    # Skip duplicates
                    content_key = content.lower().strip()
                    if content_key in seen_content:
                        continue
                    seen_content.add(content_key)

                    if category.startswith("essential_"):
                        system_prompt += f"[{category.upper()}] {content}\n"
                    else:
                        system_prompt += f"- {content}\n"

            system_prompt += "-------------------------\n"

            return system_prompt

        except Exception as e:
            logger.error(f"Failed to generate auto-ingest system prompt: {e}")
            return ""

    def add_memory_to_messages(self, messages: list, user_input: str = None) -> list:
        """
        Add appropriate memory context to messages based on ingest mode.

        Args:
            messages: List of messages for LLM
            user_input: User input for auto_ingest context retrieval (optional)

        Returns:
            Modified messages list with memory context added as system message
        """
        try:
            system_prompt = ""

            if self.conscious_ingest:
                # One-time conscious context injection
                if not self._conscious_context_injected:
                    system_prompt = self.get_conscious_system_prompt()
                    self._conscious_context_injected = True
                    logger.info(
                        "Conscious-ingest: Added complete working memory to system prompt"
                    )
                else:
                    logger.debug("Conscious-ingest: Context already injected, skipping")

            elif self.auto_ingest and user_input:
                # Dynamic auto-ingest based on user input
                system_prompt = self.get_auto_ingest_system_prompt(user_input)
                logger.debug("Auto-ingest: Added relevant context to system prompt")

            if system_prompt:
                # Add to existing system message or create new one
                messages_copy = messages.copy()

                # Check if system message already exists
                for msg in messages_copy:
                    if msg.get("role") == "system":
                        msg["content"] = system_prompt + "\n" + msg.get("content", "")
                        return messages_copy

                # No system message exists, add one at the beginning
                messages_copy.insert(0, {"role": "system", "content": system_prompt})
                return messages_copy

            return messages

        except Exception as e:
            logger.error(f"Failed to add memory to messages: {e}")
            return messages

    def get_essential_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get essential conversations from short-term memory"""
        try:
            # Get all conversations marked as essential
            with self.db_manager._get_connection() as connection:
                query = """
                SELECT memory_id, summary, category_primary, importance_score,
                       created_at, searchable_content, processed_data
                FROM short_term_memory
                WHERE namespace = ? AND category_primary LIKE 'essential_%'
                ORDER BY importance_score DESC, created_at DESC
                LIMIT ?
                """

                cursor = connection.execute(query, (self.namespace, limit))

                essential_conversations = []
                for row in cursor.fetchall():
                    essential_conversations.append(
                        {
                            "memory_id": row[0],
                            "summary": row[1],
                            "category_primary": row[2],
                            "importance_score": row[3],
                            "created_at": row[4],
                            "searchable_content": row[5],
                            "processed_data": row[6],
                        }
                    )

                return essential_conversations

        except Exception as e:
            logger.error(f"Failed to get essential conversations: {e}")
            return []

    def create_openai_client(self, **kwargs):
        """
        Create an OpenAI client with automatic memory recording.
        
        This method creates a MemoriOpenAIInterceptor that automatically records
        all OpenAI API calls to memory using the inheritance-based approach.
        
        Args:
            **kwargs: Additional arguments passed to OpenAI client (e.g., api_key)
                     These override any settings from the Memori provider config
        
        Returns:
            MemoriOpenAIInterceptor instance that works as a drop-in replacement
            for the standard OpenAI client
            
        Example:
            memori = Memori(api_key="sk-...")
            memori.enable()
            
            # Create interceptor client
            client = memori.create_openai_client()
            
            # Use exactly like standard OpenAI client
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello!"}]
            )
            # Conversation is automatically recorded
        """
        try:
            from ..integrations.openai_integration import create_openai_client
            return create_openai_client(self, self.provider_config, **kwargs)
        except ImportError as e:
            logger.error(f"Failed to import OpenAI integration: {e}")
            raise ImportError("OpenAI integration not available. Install with: pip install openai") from e

    def create_openai_wrapper(self, **kwargs):
        """
        Create a legacy OpenAI wrapper (backward compatibility).
        
        DEPRECATED: Use create_openai_client() instead for better integration.
        
        Returns:
            MemoriOpenAI wrapper instance
        """
        try:
            from ..integrations.openai_integration import MemoriOpenAI
            return MemoriOpenAI(self, **kwargs)
        except ImportError as e:
            logger.error(f"Failed to import OpenAI integration: {e}")
            raise ImportError("OpenAI integration not available. Install with: pip install openai") from e