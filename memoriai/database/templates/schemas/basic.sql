-- Memori v1.0 Database Schema - Pydantic-based Memory Storage
-- This schema supports structured memory processing with entity extraction and indexing

-- Chat History Table
-- Stores all conversations between users and AI systems
CREATE TABLE IF NOT EXISTS chat_history (
    chat_id TEXT PRIMARY KEY,
    user_input TEXT NOT NULL,
    ai_output TEXT NOT NULL,
    model TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    session_id TEXT NOT NULL,
    namespace TEXT NOT NULL DEFAULT 'default',
    tokens_used INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}'
);

-- Short-term Memory Table (with full ProcessedMemory structure)
-- Stores temporary memories with expiration (auto-expires after ~7 days)
CREATE TABLE IF NOT EXISTS short_term_memory (
    memory_id TEXT PRIMARY KEY,
    chat_id TEXT,
    processed_data TEXT NOT NULL,  -- Full ProcessedMemory JSON
    importance_score REAL NOT NULL DEFAULT 0.5,
    category_primary TEXT NOT NULL,  -- Extracted for indexing
    retention_type TEXT NOT NULL DEFAULT 'short_term',
    namespace TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    searchable_content TEXT NOT NULL,  -- Optimized for search
    summary TEXT NOT NULL,  -- Concise summary
    FOREIGN KEY (chat_id) REFERENCES chat_history (chat_id)
);

-- Long-term Memory Table (with full ProcessedMemory structure)
-- Stores persistent memories without expiration
CREATE TABLE IF NOT EXISTS long_term_memory (
    memory_id TEXT PRIMARY KEY,
    original_chat_id TEXT,
    processed_data TEXT NOT NULL,  -- Full ProcessedMemory JSON
    importance_score REAL NOT NULL DEFAULT 0.5,
    category_primary TEXT NOT NULL,  -- Extracted for indexing
    retention_type TEXT NOT NULL DEFAULT 'long_term',
    namespace TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    searchable_content TEXT NOT NULL,  -- Optimized for search
    summary TEXT NOT NULL,  -- Concise summary
    novelty_score REAL DEFAULT 0.5,
    relevance_score REAL DEFAULT 0.5,
    actionability_score REAL DEFAULT 0.5
);

-- Rules Memory Table (specialized for user rules and preferences)
-- Stores behavioral rules, constraints, and preferences
CREATE TABLE IF NOT EXISTS rules_memory (
    rule_id TEXT PRIMARY KEY,
    rule_text TEXT NOT NULL,
    rule_type TEXT NOT NULL,  -- preference, instruction, constraint, goal
    priority INTEGER DEFAULT 5,  -- 1-10 scale
    active BOOLEAN DEFAULT 1,
    context_conditions TEXT,  -- When this rule applies
    namespace TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    processed_data TEXT,  -- Optional ProcessedMemory JSON for complex rules
    metadata TEXT DEFAULT '{}'
);

-- Entity Index for Advanced Search
-- Enables fast entity-based memory retrieval
CREATE TABLE IF NOT EXISTS memory_entities (
    entity_id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,  -- short_term, long_term, rules
    entity_type TEXT NOT NULL,  -- person, technology, topic, skill, project, keyword
    entity_value TEXT NOT NULL,
    relevance_score REAL NOT NULL DEFAULT 0.5,
    entity_context TEXT,  -- Additional context about this entity
    namespace TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES short_term_memory (memory_id) ON DELETE CASCADE,
    FOREIGN KEY (memory_id) REFERENCES long_term_memory (memory_id) ON DELETE CASCADE
);

-- Memory Relationships Table (for future graph features)
-- Tracks relationships between memories
CREATE TABLE IF NOT EXISTS memory_relationships (
    relationship_id TEXT PRIMARY KEY,
    source_memory_id TEXT NOT NULL,
    target_memory_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,  -- builds_on, contradicts, supports, related_to, prerequisite
    strength REAL NOT NULL DEFAULT 0.5,
    reasoning TEXT,
    namespace TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL
);

-- Indexes for High Performance

-- Chat History Indexes
CREATE INDEX IF NOT EXISTS idx_chat_namespace_session ON chat_history(namespace, session_id);
CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_chat_model ON chat_history(model);

-- Short-term Memory Indexes
CREATE INDEX IF NOT EXISTS idx_short_term_namespace ON short_term_memory(namespace);
CREATE INDEX IF NOT EXISTS idx_short_term_category ON short_term_memory(category_primary);
CREATE INDEX IF NOT EXISTS idx_short_term_importance ON short_term_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_short_term_expires ON short_term_memory(expires_at);
CREATE INDEX IF NOT EXISTS idx_short_term_created ON short_term_memory(created_at);
CREATE INDEX IF NOT EXISTS idx_short_term_searchable ON short_term_memory(searchable_content);
CREATE INDEX IF NOT EXISTS idx_short_term_access ON short_term_memory(access_count, last_accessed);

-- Long-term Memory Indexes  
CREATE INDEX IF NOT EXISTS idx_long_term_namespace ON long_term_memory(namespace);
CREATE INDEX IF NOT EXISTS idx_long_term_category ON long_term_memory(category_primary);
CREATE INDEX IF NOT EXISTS idx_long_term_importance ON long_term_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_long_term_created ON long_term_memory(created_at);
CREATE INDEX IF NOT EXISTS idx_long_term_searchable ON long_term_memory(searchable_content);
CREATE INDEX IF NOT EXISTS idx_long_term_access ON long_term_memory(access_count, last_accessed);
CREATE INDEX IF NOT EXISTS idx_long_term_scores ON long_term_memory(novelty_score, relevance_score, actionability_score);

-- Rules Memory Indexes
CREATE INDEX IF NOT EXISTS idx_rules_namespace ON rules_memory(namespace);
CREATE INDEX IF NOT EXISTS idx_rules_active ON rules_memory(active);
CREATE INDEX IF NOT EXISTS idx_rules_priority ON rules_memory(priority);
CREATE INDEX IF NOT EXISTS idx_rules_type ON rules_memory(rule_type);
CREATE INDEX IF NOT EXISTS idx_rules_updated ON rules_memory(updated_at);

-- Entity Indexes for Fast Search
CREATE INDEX IF NOT EXISTS idx_entities_namespace ON memory_entities(namespace);
CREATE INDEX IF NOT EXISTS idx_entities_type ON memory_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_value ON memory_entities(entity_value);
CREATE INDEX IF NOT EXISTS idx_entities_memory ON memory_entities(memory_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_entities_relevance ON memory_entities(relevance_score);
CREATE INDEX IF NOT EXISTS idx_entities_value_type ON memory_entities(entity_value, entity_type);

-- Relationship Indexes
CREATE INDEX IF NOT EXISTS idx_relationships_source ON memory_relationships(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON memory_relationships(target_memory_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON memory_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_relationships_strength ON memory_relationships(strength);

-- Full-Text Search Support (SQLite FTS5)
-- Enables advanced text search capabilities
CREATE VIRTUAL TABLE IF NOT EXISTS memory_search_fts USING fts5(
    memory_id,
    memory_type,
    namespace,
    searchable_content,
    summary,
    category_primary,
    content='',
    contentless_delete=1
);

-- Triggers to maintain FTS index
CREATE TRIGGER IF NOT EXISTS short_term_memory_fts_insert AFTER INSERT ON short_term_memory
BEGIN
    INSERT INTO memory_search_fts(memory_id, memory_type, namespace, searchable_content, summary, category_primary)
    VALUES (NEW.memory_id, 'short_term', NEW.namespace, NEW.searchable_content, NEW.summary, NEW.category_primary);
END;

CREATE TRIGGER IF NOT EXISTS long_term_memory_fts_insert AFTER INSERT ON long_term_memory
BEGIN
    INSERT INTO memory_search_fts(memory_id, memory_type, namespace, searchable_content, summary, category_primary)
    VALUES (NEW.memory_id, 'long_term', NEW.namespace, NEW.searchable_content, NEW.summary, NEW.category_primary);
END;

CREATE TRIGGER IF NOT EXISTS short_term_memory_fts_delete AFTER DELETE ON short_term_memory
BEGIN
    DELETE FROM memory_search_fts WHERE memory_id = OLD.memory_id AND memory_type = 'short_term';
END;

CREATE TRIGGER IF NOT EXISTS long_term_memory_fts_delete AFTER DELETE ON long_term_memory
BEGIN
    DELETE FROM memory_search_fts WHERE memory_id = OLD.memory_id AND memory_type = 'long_term';
END;
