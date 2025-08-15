"""
Conscious Agent for User Context Management

This agent extracts user context information from memory_agent labels
and manages permanent user context in short-term memory.
"""

import json
from datetime import datetime
from typing import List, Optional

from loguru import logger

from ..utils.pydantic_models import (
    ProcessedLongTermMemory,
    UserContextProfile,
    MemoryClassification,
)


class ConsciouscAgent:
    """
    Agent that manages user context by extracting conscious-info labeled memories
    and maintaining permanent user context in short-term memory.
    
    Runs once at program startup when conscious_ingest=True.
    """

    def __init__(self):
        """Initialize the conscious agent"""
        self.context_initialized = False

    async def run_conscious_ingest(
        self, 
        db_manager, 
        namespace: str = "default"
    ) -> Optional[UserContextProfile]:
        """
        Run conscious context ingestion once at program startup
        
        Extracts user context from conscious-info labeled memories
        and stores it permanently in short-term memory
        
        Args:
            db_manager: Database manager instance  
            namespace: Memory namespace
            
        Returns:
            UserContextProfile if context was extracted, None otherwise
        """
        try:
            # Check if context already exists
            existing_context = await self._get_existing_user_context(db_manager, namespace)
            if existing_context:
                logger.info("ConsciouscAgent: User context already exists")
                return existing_context
            
            # Get all conscious-info labeled memories
            conscious_memories = await self._get_conscious_memories(db_manager, namespace)
            
            if not conscious_memories:
                logger.info("ConsciouscAgent: No conscious-info memories found")
                return None
            
            # Extract user context profile
            user_profile = await self._extract_user_context_profile(conscious_memories)
            
            # Store permanently in short-term memory
            await self._store_permanent_context(db_manager, namespace, user_profile)
            
            # Mark memories as processed
            await self._mark_memories_processed(db_manager, conscious_memories)
            
            self.context_initialized = True
            logger.info(f"ConsciouscAgent: User context initialized for {user_profile.name or 'user'}")
            
            return user_profile
            
        except Exception as e:
            logger.error(f"ConsciouscAgent: Conscious ingest failed: {e}")
            return None

    async def check_for_context_updates(
        self, 
        db_manager, 
        namespace: str = "default"
    ) -> bool:
        """
        Check for new conscious-info memories and update context if needed
        
        Args:
            db_manager: Database manager instance
            namespace: Memory namespace
            
        Returns:
            True if context was updated, False otherwise
        """
        try:
            # Get unprocessed conscious memories
            new_memories = await self._get_unprocessed_conscious_memories(db_manager, namespace)
            
            if not new_memories:
                return False
            
            # Get existing context
            existing_context = await self._get_existing_user_context(db_manager, namespace)
            if not existing_context:
                # No existing context, run full ingest
                return await self.run_conscious_ingest(db_manager, namespace) is not None
            
            # Extract additional context from new memories
            additional_context = await self._extract_user_context_profile(new_memories)
            
            # Merge with existing context  
            updated_context = self._merge_user_contexts(existing_context, additional_context)
            
            # Update stored context
            await self._store_permanent_context(db_manager, namespace, updated_context)
            
            # Mark new memories as processed
            await self._mark_memories_processed(db_manager, new_memories)
            
            logger.info(f"ConsciouscAgent: Updated context with {len(new_memories)} new memories")
            return True
            
        except Exception as e:
            logger.error(f"ConsciouscAgent: Context update failed: {e}")
            return False

    async def _get_existing_user_context(
        self, 
        db_manager, 
        namespace: str
    ) -> Optional[UserContextProfile]:
        """Get existing user context from short-term memory"""
        try:
            from ..database.queries.memory_queries import MemoryQueries
            
            with db_manager._get_connection() as connection:
                cursor = connection.execute(
                    MemoryQueries.SELECT_USER_CONTEXT_PROFILE,
                    (namespace,)
                )
                row = cursor.fetchone()
                
                if row:
                    context_data = json.loads(row[0])
                    return UserContextProfile(**context_data.get('profile', {}))
                    
                return None
                
        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to get existing context: {e}")
            return None

    async def _get_conscious_memories(
        self, 
        db_manager, 
        namespace: str
    ) -> List[ProcessedLongTermMemory]:
        """Get all conscious-info labeled memories"""
        try:
            from ..database.queries.memory_queries import MemoryQueries
            
            with db_manager._get_connection() as connection:
                cursor = connection.execute(
                    MemoryQueries.SELECT_CONSCIOUS_MEMORIES,
                    (namespace,)
                )
                
                memories = []
                for row in cursor.fetchall():
                    try:
                        processed_data = json.loads(row[1])  # processed_data column
                        memory = ProcessedLongTermMemory(**processed_data)
                        memories.append(memory)
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"Failed to parse memory {row[0]}: {e}")
                        continue
                        
                return memories
                
        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to get conscious memories: {e}")
            return []

    async def _get_unprocessed_conscious_memories(
        self, 
        db_manager, 
        namespace: str
    ) -> List[ProcessedLongTermMemory]:
        """Get unprocessed conscious-info labeled memories"""
        try:
            from ..database.queries.memory_queries import MemoryQueries
            
            with db_manager._get_connection() as connection:
                cursor = connection.execute(
                    MemoryQueries.SELECT_UNPROCESSED_CONSCIOUS,
                    (namespace,)
                )
                
                memories = []
                for row in cursor.fetchall():
                    try:
                        processed_data = json.loads(row[1])  # processed_data column  
                        memory = ProcessedLongTermMemory(**processed_data)
                        memories.append(memory)
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"Failed to parse memory {row[0]}: {e}")
                        continue
                        
                return memories
                
        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to get unprocessed memories: {e}")
            return []

    async def _extract_user_context_profile(
        self, 
        conscious_memories: List[ProcessedLongTermMemory]
    ) -> UserContextProfile:
        """Extract user context profile from conscious memories"""
        # Consolidate memories by context categories
        context_data = {
            'personal': [],
            'professional': [], 
            'technical': [],
            'behavioral': [],
            'current': []
        }
        
        for memory in conscious_memories:
            category = self._classify_context_category(memory)
            context_data[category].append(memory.content)
        
        # Extract structured profile
        profile = UserContextProfile(
            name=self._extract_name(context_data['personal']),
            location=self._extract_location(context_data['personal']),
            job_title=self._extract_job_title(context_data['professional']),
            company=self._extract_company(context_data['professional']),
            primary_languages=self._extract_languages(context_data['technical']),
            tools=self._extract_tools(context_data['technical']),
            communication_style=self._extract_comm_style(context_data['behavioral']),
            active_projects=self._extract_projects(context_data['current']),
            learning_goals=self._extract_goals(context_data['current']),
            last_updated=datetime.now(),
        )
        
        return profile

    def _classify_context_category(self, memory: ProcessedLongTermMemory) -> str:
        """Classify memory into context categories"""  
        content_lower = memory.content.lower()
        
        if any(keyword in content_lower for keyword in ['name', 'called', 'location', 'from', 'live']):
            return 'personal'
        elif any(keyword in content_lower for keyword in ['job', 'work', 'company', 'role', 'title']):
            return 'professional'
        elif any(keyword in content_lower for keyword in ['language', 'framework', 'tool', 'technology']):
            return 'technical'
        elif any(keyword in content_lower for keyword in ['prefer', 'like', 'style', 'approach']):
            return 'behavioral'
        elif any(keyword in content_lower for keyword in ['project', 'working on', 'building', 'learning']):
            return 'current'
        else:
            return 'personal'  # Default

    async def _store_permanent_context(
        self, 
        db_manager, 
        namespace: str, 
        user_profile: UserContextProfile
    ):
        """Store user context permanently in short-term memory"""
        try:
            from ..database.queries.memory_queries import MemoryQueries
            
            # Create memory content
            memory_content = {
                'type': 'user_context_profile',
                'profile': user_profile.model_dump(mode='json'),  # JSON-serializable format
                'permanent': True,
                'category': 'user_context',
                'importance': 'critical'
            }
            
            memory_id = f"user_context_{namespace}_{int(datetime.now().timestamp())}"
            
            with db_manager._get_connection() as connection:
                connection.execute(
                    MemoryQueries.INSERT_USER_CONTEXT_PROFILE,
                    (
                        memory_id,
                        json.dumps(memory_content),
                        1.0,  # importance_score
                        'user_context',  # category_primary
                        'permanent',  # retention_type
                        namespace,
                        datetime.now().isoformat(),
                        None,  # expires_at (permanent)
                        f"User context: {user_profile.name or 'user'}",  # searchable_content
                        f"Permanent user context profile",  # summary
                        1  # is_permanent_context
                    )
                )
                connection.commit()
                
        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to store permanent context: {e}")

    async def _mark_memories_processed(
        self, 
        db_manager, 
        memories: List[ProcessedLongTermMemory]
    ):
        """Mark memories as processed for conscious context"""
        try:
            from ..database.queries.memory_queries import MemoryQueries
            
            with db_manager._get_connection() as connection:
                for memory in memories:
                    connection.execute(
                        MemoryQueries.MARK_CONSCIOUS_PROCESSED,
                        (memory.conversation_id, 'default')  # Using conversation_id as memory_id
                    )
                connection.commit()
                
        except Exception as e:
            logger.error(f"ConsciouscAgent: Failed to mark memories processed: {e}")

    def _merge_user_contexts(
        self, 
        existing: UserContextProfile, 
        additional: UserContextProfile
    ) -> UserContextProfile:
        """Merge additional context into existing context"""
        # Simple merge - could be enhanced with conflict resolution
        merged = existing.model_copy()
        
        # Update non-None fields from additional context
        if additional.name and not existing.name:
            merged.name = additional.name
        if additional.location and not existing.location:  
            merged.location = additional.location
        if additional.job_title and not existing.job_title:
            merged.job_title = additional.job_title
            
        # Merge lists
        merged.primary_languages = list(set(existing.primary_languages + additional.primary_languages))
        merged.tools = list(set(existing.tools + additional.tools))
        merged.active_projects = list(set(existing.active_projects + additional.active_projects))
        merged.learning_goals = list(set(existing.learning_goals + additional.learning_goals))
        
        merged.last_updated = datetime.now()
        merged.version += 1
        
        return merged

    # Simple extraction methods (can be enhanced with NLP)
    def _extract_name(self, personal_memories: List[str]) -> Optional[str]:
        """Extract user name from personal memories"""
        for memory in personal_memories:
            if 'name is' in memory.lower() or 'called' in memory.lower():
                words = memory.split()
                for i, word in enumerate(words):
                    if word.lower() in ['name', 'called'] and i + 1 < len(words):
                        return words[i + 1].strip('.,!?')
        return None

    def _extract_location(self, personal_memories: List[str]) -> Optional[str]:
        """Extract user location from personal memories"""
        for memory in personal_memories:
            if any(keyword in memory.lower() for keyword in ['from', 'live', 'location', 'based']):
                return memory.split()[-1] if memory.split() else None
        return None

    def _extract_job_title(self, professional_memories: List[str]) -> Optional[str]:
        """Extract job title from professional memories"""
        for memory in professional_memories:
            if any(keyword in memory.lower() for keyword in ['job', 'role', 'title', 'work as']):
                return memory
        return None

    def _extract_company(self, professional_memories: List[str]) -> Optional[str]:
        """Extract company from professional memories"""
        for memory in professional_memories:
            if any(keyword in memory.lower() for keyword in ['company', 'work at', 'employed']):
                return memory
        return None

    def _extract_languages(self, technical_memories: List[str]) -> List[str]:
        """Extract programming languages from technical memories"""
        languages = []
        common_languages = ['python', 'javascript', 'java', 'c++', 'go', 'rust', 'typescript', 'php']
        
        for memory in technical_memories:
            memory_lower = memory.lower()
            for lang in common_languages:
                if lang in memory_lower and lang not in languages:
                    languages.append(lang.title())
        
        return languages

    def _extract_tools(self, technical_memories: List[str]) -> List[str]:
        """Extract tools from technical memories"""
        tools = []
        common_tools = ['docker', 'kubernetes', 'git', 'vscode', 'pycharm', 'react', 'fastapi', 'flask']
        
        for memory in technical_memories:
            memory_lower = memory.lower()
            for tool in common_tools:
                if tool in memory_lower and tool not in tools:
                    tools.append(tool.title())
        
        return tools

    def _extract_comm_style(self, behavioral_memories: List[str]) -> Optional[str]:
        """Extract communication style from behavioral memories"""
        for memory in behavioral_memories:
            if 'style' in memory.lower() or 'prefer' in memory.lower():
                return memory
        return None

    def _extract_projects(self, current_memories: List[str]) -> List[str]:
        """Extract active projects from current memories"""
        projects = []
        for memory in current_memories:
            if any(keyword in memory.lower() for keyword in ['project', 'working on', 'building']):
                projects.append(memory)
        return projects

    def _extract_goals(self, current_memories: List[str]) -> List[str]:
        """Extract learning goals from current memories"""
        goals = []
        for memory in current_memories:
            if any(keyword in memory.lower() for keyword in ['learning', 'goal', 'want to']):
                goals.append(memory)
        return goals