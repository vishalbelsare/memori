# Configuration

Comprehensive guide to configuring Memoriai for your needs.

## Configuration Methods

### 1. Direct Configuration
```python
from memoriai import Memori

memori = Memori(
    database_connect="sqlite:///memori.db",
    conscious_ingest=True,
    openai_api_key="sk-..."
)
```

### 2. Configuration File
Create `memori.json`:
```json
{
  "database": {
    "connection_string": "sqlite:///memori.db",
    "pool_size": 10,
    "echo_sql": false
  },
  "agents": {
    "openai_api_key": "sk-...",
    "default_model": "gpt-4o",
    "conscious_ingest": true,
    "max_tokens": 2000,
    "temperature": 0.1
  },
  "memory": {
    "namespace": "my_project",
    "retention_policy": "30_days",
    "importance_threshold": 0.3,
    "context_limit": 3
  },
  "logging": {
    "level": "INFO",
    "log_to_file": false
  }
}
```

```python
from memoriai import ConfigManager

config = ConfigManager()
config.auto_load()  # Loads memori.json automatically

memori = Memori()  # Uses loaded configuration
```

### 3. Environment Variables
```bash
export MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
export MEMORI_DATABASE__CONNECTION_STRING="postgresql://..."
export MEMORI_MEMORY__NAMESPACE="production"
export MEMORI_LOGGING__LEVEL="INFO"
```

```python
from memoriai import ConfigManager

config = ConfigManager()
config.load_from_env()

memori = Memori()
```

## Configuration Sections

### Database Settings

```python
database = {
    "connection_string": "sqlite:///memori.db",
    "database_type": "sqlite",  # sqlite, postgresql, mysql
    "pool_size": 10,
    "echo_sql": False,
    "migration_auto": True,
    "backup_enabled": False,
    "backup_interval_hours": 24
}
```

#### Connection Strings
```python
# SQLite
"sqlite:///path/to/database.db"

# PostgreSQL  
"postgresql://user:password@localhost:5432/memori"

# MySQL
"mysql://user:password@localhost:3306/memori"
```

### Agent Settings

```python
agents = {
    "openai_api_key": "sk-...",
    "default_model": "gpt-4o",
    "fallback_model": "gpt-3.5-turbo", 
    "max_tokens": 2000,
    "temperature": 0.1,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "conscious_ingest": True
}
```

### Memory Settings

```python
memory = {
    "namespace": "default",
    "shared_memory": False,
    "retention_policy": "30_days",  # 7_days, 30_days, 90_days, permanent
    "auto_cleanup": True,
    "cleanup_interval_hours": 24,
    "importance_threshold": 0.3,
    "max_short_term_memories": 1000,
    "max_long_term_memories": 10000,
    "context_injection": True,
    "context_limit": 3
}
```

### Logging Settings

```python
logging = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "<green>{time}</green> | <level>{level}</level> | {message}",
    "log_to_file": False,
    "log_file_path": "logs/memori.log",
    "log_rotation": "10 MB",
    "log_retention": "30 days",
    "structured_logging": False
}
```

### Integration Settings

```python
integrations = {
    "litellm_enabled": True,
    "openai_wrapper_enabled": False,
    "anthropic_wrapper_enabled": False,
    "auto_enable_on_import": False,
    "callback_timeout": 5
}
```

## Configuration Manager

### Auto-Loading
```python
from memoriai import ConfigManager

config = ConfigManager()
config.auto_load()  # Loads from multiple sources in priority order
```

Priority (highest to lowest):
1. Environment variables (`MEMORI_*`)
2. `memori.json` in current directory
3. `memori.yaml` in current directory
4. `config/memori.json`
5. `~/.memori/config.json`
6. Default settings

### Manual Configuration
```python
# Load from specific file
config.load_from_file("custom_config.json")

# Load from environment
config.load_from_env()

# Update specific setting
config.update_setting("database.pool_size", 20)

# Get setting value
db_url = config.get_setting("database.connection_string")

# Save configuration
config.save_to_file("memori_backup.json")
```

### Configuration Info
```python
info = config.get_config_info()
print(f"Sources: {info['sources']}")
print(f"Debug mode: {info['debug_mode']}")
print(f"Production: {info['is_production']}")
```

### Validation
```python
is_valid = config.validate_configuration()
if not is_valid:
    print("Configuration has errors")
```

## Production Configuration

### Development
```json
{
  "database": {
    "connection_string": "sqlite:///dev_memori.db",
    "echo_sql": true
  },
  "agents": {
    "default_model": "gpt-4o-mini"
  },
  "logging": {
    "level": "DEBUG",
    "log_to_file": false
  },
  "debug": true
}
```

### Production
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@prod-db:5432/memori",
    "pool_size": 20,
    "backup_enabled": true
  },
  "agents": {
    "default_model": "gpt-4o",
    "retry_attempts": 5
  },
  "memory": {
    "auto_cleanup": true,
    "importance_threshold": 0.4
  },
  "logging": {
    "level": "INFO",
    "log_to_file": true,
    "log_file_path": "/var/log/memori/memori.log",
    "structured_logging": true
  },
  "debug": false
}
```

### Docker Environment
```dockerfile
ENV MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:pass@db:5432/memori"
ENV MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
ENV MEMORI_MEMORY__NAMESPACE="production"
ENV MEMORI_LOGGING__LEVEL="INFO"
ENV MEMORI_LOGGING__LOG_TO_FILE="true"
```

## Configuration Examples

### Multi-Project Setup
```python
# Project A
config_a = ConfigManager()
config_a.update_setting("memory.namespace", "project_a")
memori_a = Memori()

# Project B  
config_b = ConfigManager()
config_b.update_setting("memory.namespace", "project_b")
memori_b = Memori()
```

### High-Performance Setup
```json
{
  "database": {
    "connection_string": "postgresql://...",
    "pool_size": 50
  },
  "memory": {
    "importance_threshold": 0.5,
    "max_short_term_memories": 5000,
    "context_limit": 5
  },
  "agents": {
    "max_tokens": 4000,
    "retry_attempts": 2
  }
}
```

### Security-Focused Setup
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@secure-db:5432/memori?sslmode=require"
  },
  "logging": {
    "level": "WARNING",
    "structured_logging": true
  },
  "agents": {
    "timeout_seconds": 10
  }
}
```

## Environment Variables Reference

All configuration can be set via environment variables with the prefix `MEMORI_`:

```bash
# Database
export MEMORI_DATABASE__CONNECTION_STRING="sqlite:///memori.db"
export MEMORI_DATABASE__POOL_SIZE="10"

# Agents
export MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
export MEMORI_AGENTS__DEFAULT_MODEL="gpt-4o"
export MEMORI_AGENTS__CONSCIOUS_INGEST="true"

# Memory
export MEMORI_MEMORY__NAMESPACE="production"
export MEMORI_MEMORY__RETENTION_POLICY="30_days"
export MEMORI_MEMORY__IMPORTANCE_THRESHOLD="0.3"

# Logging
export MEMORI_LOGGING__LEVEL="INFO"
export MEMORI_LOGGING__LOG_TO_FILE="true"
```

## Next Steps

- [Database Setup](database.md) - Database-specific configuration
- [Environment Variables](environment.md) - Complete environment reference
- [Examples](../examples/advanced-config.md) - Configuration examples