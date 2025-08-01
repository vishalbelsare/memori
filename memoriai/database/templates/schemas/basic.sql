-- Basic Memory Schema for Memori
-- This schema provides the foundational tables for memory storage and retrieval

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

-- Short-term Memory Table  
-- Stores temporary memories with expiration
CREATE TABLE IF NOT EXISTS short_term_memory (
    memory_id TEXT PRIMARY KEY,
    chat_id TEXT,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    importance_score REAL NOT NULL DEFAULT 0.5,
    namespace TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (chat_id) REFERENCES chat_history (chat_id)
);

-- Long-term Memory Table
-- Stores persistent memories without expiration
CREATE TABLE IF NOT EXISTS long_term_memory (
    memory_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT NOT NULL,
    importance_score REAL NOT NULL DEFAULT 0.5,
    namespace TEXT NOT NULL DEFAULT 'default', 
    created_at TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    metadata TEXT DEFAULT '{}'
);

-- Rules Memory Table
-- Stores behavioral rules and constraints
CREATE TABLE IF NOT EXISTS rules_memory (
    rule_id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL,
    condition_text TEXT NOT NULL,
    action_text TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    active BOOLEAN DEFAULT 1,
    namespace TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP NOT NULL,
    metadata TEXT DEFAULT '{}'
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_chat_namespace_session ON chat_history(namespace, session_id);
CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_short_term_namespace ON short_term_memory(namespace);
CREATE INDEX IF NOT EXISTS idx_short_term_category ON short_term_memory(category);
CREATE INDEX IF NOT EXISTS idx_short_term_importance ON short_term_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_short_term_expires ON short_term_memory(expires_at);

CREATE INDEX IF NOT EXISTS idx_long_term_namespace ON long_term_memory(namespace);
CREATE INDEX IF NOT EXISTS idx_long_term_category ON long_term_memory(category);  
CREATE INDEX IF NOT EXISTS idx_long_term_importance ON long_term_memory(importance_score);
CREATE INDEX IF NOT EXISTS idx_long_term_access ON long_term_memory(access_count);

CREATE INDEX IF NOT EXISTS idx_rules_namespace ON rules_memory(namespace);
CREATE INDEX IF NOT EXISTS idx_rules_active ON rules_memory(active);
CREATE INDEX IF NOT EXISTS idx_rules_priority ON rules_memory(priority);
