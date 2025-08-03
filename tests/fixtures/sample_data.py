"""
Sample data fixtures for testing.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from memoriai.utils.pydantic_models import (
    ConversationRecord,
    ExtractedEntities,
    MemoryCategory,
    MemoryCategoryType,
    MemoryImportance,
    ProcessedMemory,
    RetentionType,
)


class SampleData:
    """Container for sample test data."""

    @staticmethod
    def get_sample_conversations() -> List[Dict[str, Any]]:
        """Get sample conversation data."""
        return [
            {
                "user_input": "How do I create a Django model?",
                "ai_output": "To create a Django model, you need to define a class that inherits from models.Model. Here's an example:\n\nclass User(models.Model):\n    name = models.CharField(max_length=100)\n    email = models.EmailField()\n    created_at = models.DateTimeField(auto_now_add=True)",
                "model": "gpt-4",
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "tokens_used": 120,
                    "response_time": 1.5,
                    "temperature": 0.7,
                },
            },
            {
                "user_input": "What's the difference between Python lists and tuples?",
                "ai_output": "The main differences between Python lists and tuples are:\n1. Mutability: Lists are mutable (can be changed), tuples are immutable\n2. Syntax: Lists use [], tuples use ()\n3. Performance: Tuples are slightly faster for iteration\n4. Use cases: Lists for changing data, tuples for fixed data",
                "model": "gpt-3.5-turbo",
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "metadata": {
                    "tokens_used": 95,
                    "response_time": 0.8,
                    "temperature": 0.5,
                },
            },
            {
                "user_input": "I prefer using dark mode in my IDE",
                "ai_output": "That's a great preference! Dark mode can reduce eye strain and is popular among developers. Most modern IDEs like VS Code, PyCharm, and IntelliJ offer excellent dark themes.",
                "model": "claude-3-sonnet",
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "metadata": {
                    "tokens_used": 45,
                    "response_time": 0.6,
                    "temperature": 0.8,
                },
            },
            {
                "user_input": "How do I optimize database queries in Django?",
                "ai_output": "Here are key strategies for optimizing Django database queries:\n1. Use select_related() for foreign keys\n2. Use prefetch_related() for many-to-many and reverse foreign keys\n3. Avoid N+1 query problems\n4. Use only() and defer() to limit fields\n5. Use database indexes\n6. Profile queries with Django Debug Toolbar",
                "model": "gpt-4",
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "metadata": {
                    "tokens_used": 180,
                    "response_time": 2.1,
                    "temperature": 0.3,
                },
            },
            {
                "user_input": "Remember that I'm working on a machine learning project using TensorFlow",
                "ai_output": "Got it! I'll remember that you're working on a machine learning project with TensorFlow. This context will help me provide more relevant suggestions and examples related to ML workflows, model training, and TensorFlow-specific best practices.",
                "model": "claude-3-sonnet",
                "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "metadata": {
                    "tokens_used": 65,
                    "response_time": 0.9,
                    "temperature": 0.7,
                },
            },
        ]

    @staticmethod
    def get_sample_processed_memories() -> List[ProcessedMemory]:
        """Get sample processed memory objects."""
        return [
            ProcessedMemory(
                category=MemoryCategory(
                    primary_category=MemoryCategoryType.fact,
                    confidence_score=0.95,
                    reasoning="Contains specific technical information about Django models",
                ),
                entities=ExtractedEntities(
                    technologies=["Django", "Python"],
                    topics=["web development", "database modeling", "ORM"],
                    keywords=[
                        "Django",
                        "model",
                        "models.Model",
                        "CharField",
                        "EmailField",
                    ],
                    organizations=["Django Software Foundation"],
                ),
                importance=MemoryImportance(
                    importance_score=0.85,
                    retention_type=RetentionType.long_term,
                    reasoning="Fundamental Django concept frequently referenced",
                ),
                summary="Django model creation with field types and inheritance",
                searchable_content="Django model creation class inheritance models.Model CharField EmailField DateTimeField auto_now_add",
                should_store=True,
                storage_reasoning="Essential Django knowledge for web development",
            ),
            ProcessedMemory(
                category=MemoryCategory(
                    primary_category=MemoryCategoryType.preference,
                    confidence_score=0.9,
                    reasoning="User explicitly stated a preference about IDE appearance",
                ),
                entities=ExtractedEntities(
                    topics=["user interface", "development tools", "preferences"],
                    keywords=["dark mode", "IDE", "preference", "eye strain"],
                    technologies=["VS Code", "PyCharm", "IntelliJ"],
                ),
                importance=MemoryImportance(
                    importance_score=0.6,
                    retention_type=RetentionType.long_term,
                    reasoning="Personal preference that affects recommendations",
                ),
                summary="User prefers dark mode in IDE for reduced eye strain",
                searchable_content="dark mode IDE preference eye strain VS Code PyCharm IntelliJ",
                should_store=True,
                storage_reasoning="User preference affects future IDE recommendations",
            ),
            ProcessedMemory(
                category=MemoryCategory(
                    primary_category=MemoryCategoryType.context,
                    confidence_score=0.85,
                    reasoning="User provided context about current project work",
                ),
                entities=ExtractedEntities(
                    technologies=["TensorFlow", "Python"],
                    topics=["machine learning", "AI", "deep learning"],
                    keywords=["machine learning", "TensorFlow", "project", "ML"],
                ),
                importance=MemoryImportance(
                    importance_score=0.8,
                    retention_type=RetentionType.long_term,
                    reasoning="Current project context affects all future interactions",
                ),
                summary="User working on machine learning project using TensorFlow",
                searchable_content="machine learning TensorFlow project ML workflows model training",
                should_store=True,
                storage_reasoning="Active project context influences recommendations",
            ),
            ProcessedMemory(
                category=MemoryCategory(
                    primary_category=MemoryCategoryType.skill,
                    confidence_score=0.8,
                    reasoning="Discussion about advanced Django optimization techniques",
                ),
                entities=ExtractedEntities(
                    technologies=["Django", "Python", "PostgreSQL"],
                    topics=["database optimization", "performance", "web development"],
                    keywords=[
                        "select_related",
                        "prefetch_related",
                        "N+1",
                        "queries",
                        "optimization",
                    ],
                ),
                importance=MemoryImportance(
                    importance_score=0.9,
                    retention_type=RetentionType.long_term,
                    reasoning="Advanced skill knowledge valuable for complex projects",
                ),
                summary="Django database query optimization techniques and best practices",
                searchable_content="Django database optimization select_related prefetch_related N+1 queries performance",
                should_store=True,
                storage_reasoning="Advanced Django skills for performance optimization",
            ),
            ProcessedMemory(
                category=MemoryCategory(
                    primary_category=MemoryCategoryType.fact,
                    confidence_score=0.92,
                    reasoning="Factual comparison of Python data structures",
                ),
                entities=ExtractedEntities(
                    technologies=["Python"],
                    topics=["data structures", "programming fundamentals"],
                    keywords=["lists", "tuples", "mutable", "immutable", "performance"],
                ),
                importance=MemoryImportance(
                    importance_score=0.7,
                    retention_type=RetentionType.long_term,
                    reasoning="Fundamental Python knowledge with broad applicability",
                ),
                summary="Python lists vs tuples: mutability, syntax, and performance differences",
                searchable_content="Python lists tuples mutable immutable syntax performance iteration",
                should_store=True,
                storage_reasoning="Core Python knowledge applicable to many scenarios",
            ),
        ]

    @staticmethod
    def get_sample_conversation_records() -> List[ConversationRecord]:
        """Get sample conversation record objects."""
        conversations = SampleData.get_sample_conversations()
        records = []

        for i, conv in enumerate(conversations):
            record = ConversationRecord(
                chat_id=f"chat_{i+1:03d}",
                user_input=conv["user_input"],
                ai_output=conv["ai_output"],
                model=conv["model"],
                session_id=f"session_{(i//2)+1:03d}",  # Group conversations by session
                namespace="test_namespace",
                metadata=conv["metadata"],
            )
            records.append(record)

        return records

    @staticmethod
    def get_sample_entities() -> List[ExtractedEntities]:
        """Get sample extracted entities."""
        return [
            ExtractedEntities(
                people=["John Doe", "Jane Smith", "Alice Johnson"],
                technologies=["Python", "Django", "PostgreSQL", "Redis", "Docker"],
                topics=[
                    "web development",
                    "machine learning",
                    "data science",
                    "DevOps",
                ],
                keywords=[
                    "optimization",
                    "performance",
                    "scalability",
                    "best practices",
                ],
                locations=["San Francisco", "New York", "London", "Remote"],
                organizations=["Google", "Microsoft", "OpenAI", "Anthropic"],
            ),
            ExtractedEntities(
                technologies=["React", "TypeScript", "Node.js", "MongoDB"],
                topics=["frontend development", "full-stack development", "API design"],
                keywords=["components", "hooks", "state management", "REST API"],
            ),
            ExtractedEntities(
                people=["Guido van Rossum", "Dennis Ritchie"],
                technologies=["Python", "C", "Linux", "Git"],
                topics=["programming languages", "software history", "open source"],
                keywords=["creator", "inventor", "programming", "development"],
            ),
        ]

    @staticmethod
    def get_sample_metadata() -> Dict[str, Any]:
        """Get sample metadata for testing."""
        return {
            "conversation_metadata": {
                "tokens_used": 150,
                "response_time": 1.2,
                "temperature": 0.7,
                "max_tokens": 1000,
                "model_version": "gpt-4-0613",
                "api_version": "2023-07-01-preview",
            },
            "memory_metadata": {
                "processing_time": 0.5,
                "confidence_threshold": 0.8,
                "extraction_method": "llm_based",
                "validation_passed": True,
                "storage_tier": "long_term",
            },
            "session_metadata": {
                "user_id": "user_12345",
                "session_start": datetime.utcnow().isoformat(),
                "user_agent": "MemoriAI Client v1.0",
                "ip_address": "192.168.1.100",
                "location": "San Francisco, CA",
            },
        }

    @staticmethod
    def get_sample_search_queries() -> List[Dict[str, Any]]:
        """Get sample search queries for testing."""
        return [
            {
                "query": "Django model optimization",
                "namespace": "development",
                "limit": 10,
                "category_filter": [MemoryCategoryType.fact, MemoryCategoryType.skill],
                "importance_threshold": 0.7,
            },
            {
                "query": "Python best practices",
                "namespace": "learning",
                "limit": 20,
                "category_filter": None,
                "importance_threshold": 0.5,
            },
            {
                "query": "machine learning TensorFlow",
                "namespace": "ml_project",
                "limit": 15,
                "category_filter": [
                    MemoryCategoryType.fact,
                    MemoryCategoryType.context,
                ],
                "importance_threshold": 0.6,
            },
            {
                "query": "user preferences dark mode",
                "namespace": "user_profile",
                "limit": 5,
                "category_filter": [MemoryCategoryType.preference],
                "importance_threshold": 0.4,
            },
        ]

    @staticmethod
    def get_large_dataset(size: int = 100) -> List[ProcessedMemory]:
        """Generate a large dataset of processed memories for testing."""
        base_memories = SampleData.get_sample_processed_memories()
        large_dataset = []

        categories = list(MemoryCategoryType)
        retention_types = list(RetentionType)
        technologies = [
            "Python",
            "JavaScript",
            "Java",
            "C++",
            "Go",
            "Rust",
            "TypeScript",
        ]
        topics = [
            "web development",
            "machine learning",
            "data science",
            "DevOps",
            "mobile development",
        ]

        for i in range(size):
            # Use base memories as templates and modify them
            base_memory = base_memories[i % len(base_memories)]

            # Create variations
            memory = ProcessedMemory(
                category=MemoryCategory(
                    primary_category=categories[i % len(categories)],
                    confidence_score=0.5 + (i % 5) * 0.1,
                    reasoning=f"Generated test memory {i} reasoning",
                ),
                entities=ExtractedEntities(
                    technologies=[technologies[i % len(technologies)]],
                    topics=[topics[i % len(topics)]],
                    keywords=[f"keyword_{i}", f"test_{i % 10}"],
                ),
                importance=MemoryImportance(
                    importance_score=0.3 + (i % 7) * 0.1,
                    retention_type=retention_types[i % len(retention_types)],
                    reasoning=f"Generated importance reasoning {i}",
                ),
                summary=f"Generated test memory {i}: {base_memory.summary}",
                searchable_content=f"generated test memory {i} {base_memory.searchable_content}",
                should_store=i % 4 != 0,  # 75% should be stored
                storage_reasoning=f"Generated storage reasoning {i}",
            )

            large_dataset.append(memory)

        return large_dataset
