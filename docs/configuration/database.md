# Database Setup

Configure Memori with different database backends.

## Supported Databases

- **SQLite** (default) - File-based, no setup required
- **PostgreSQL** - Production-ready relational database  
- **MySQL** - Popular relational database

## SQLite (Default)

### Basic Setup
```python
from memori import Memori

memori = Memori(database_connect="sqlite:///memori.db")
```

### Configuration
```json
{
  "database": {
    "connection_string": "sqlite:///path/to/memori.db",
    "echo_sql": false
  }
}
```

### Features
- No installation required
- File-based storage
- Full-text search (FTS5)
- Perfect for development and small deployments
- No concurrent writes
- Limited scalability

## PostgreSQL

### Installation
```bash
pip install psycopg2-binary
```

### Setup
```python
from memori import Memori

memori = Memori(
    database_connect="postgresql://user:password@localhost:5432/memori"
)
```

### Configuration
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@host:5432/memori",
    "pool_size": 20,
    "echo_sql": false
  }
}
```

### Connection Parameters
```python
# Full connection string
"postgresql://user:pass@host:5432/database?sslmode=require"

# Environment variables
"postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:5432/${DB_NAME}"
```

### Features
- Production-ready
- Concurrent access
- Advanced indexing
- Full-text search
- JSON support
- Excellent performance

### Production Setup
```sql
-- Create database
CREATE DATABASE memori;

-- Create user
CREATE USER memori_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE memori TO memori_user;
```

## MySQL

### Installation
```bash
# Option 1: mysqlclient (recommended)
pip install mysqlclient

# Option 2: PyMySQL (pure Python)
pip install PyMySQL
```

### Setup
```python
from memori import Memori

# With mysqlclient
memori = Memori(
    database_connect="mysql://user:password@localhost:3306/memori"
)

# With PyMySQL
memori = Memori(
    database_connect="mysql+pymysql://user:password@localhost:3306/memori"
)
```

### Configuration
```json
{
  "database": {
    "connection_string": "mysql://user:pass@host:3306/memori",
    "pool_size": 15,
    "echo_sql": false
  }
}
```

### Features
- Popular and well-supported
- Good performance
- Concurrent access
- Replication support
- Limited full-text search compared to PostgreSQL

## Connection Pooling

### Configuration
```json
{
  "database": {
    "connection_string": "postgresql://...",
    "pool_size": 20,        // Max connections in pool
    "max_overflow": 10,     // Additional connections beyond pool_size
    "pool_timeout": 30,     // Timeout for getting connection
    "pool_recycle": 3600    // Recycle connections after 1 hour
  }
}
```

### Monitoring
```python
from memori import Memori

memori = Memori()
stats = memori.db_manager.get_connection_stats()
print(f"Active connections: {stats['active']}")
print(f"Pool size: {stats['pool_size']}")
```

## Database Migration

### Automatic Migration (Default)
```python
from memori import Memori

# Automatically creates/updates schema
memori = Memori(database_connect="postgresql://...")
```

### Manual Migration
```python
from memori import DatabaseManager

db = DatabaseManager("postgresql://...")
db.create_tables()      # Create initial schema
db.migrate_schema()     # Apply migrations
```

### Schema Versions
```python
# Check current schema version
version = db.get_schema_version()
print(f"Schema version: {version}")

# Get available migrations
migrations = db.get_available_migrations()
```

## Performance Optimization

### Indexing
Memori automatically creates optimized indexes:

```sql
-- Automatically created indexes
CREATE INDEX idx_chat_timestamp ON chat_history(timestamp);
CREATE INDEX idx_memory_importance ON short_term_memory(importance_score);
CREATE INDEX idx_entities_value ON memory_entities(entity_value);
```

### Query Optimization
```json
{
  "database": {
    "connection_string": "postgresql://...",
    "echo_sql": true,    // Log SQL queries for optimization
    "query_timeout": 30  // Timeout slow queries
  }
}
```

### Maintenance
```python
# Database maintenance
db.optimize_tables()    // Vacuum/optimize tables
db.rebuild_indexes()   // Rebuild indexes
db.analyze_tables()    // Update table statistics
```

## Backup and Recovery

### SQLite Backup
```bash
# Simple file copy
cp memori.db memori_backup.db

# SQLite backup command
sqlite3 memori.db ".backup memori_backup.db"
```

### PostgreSQL Backup
```bash
# Dump database
pg_dump memori > memori_backup.sql

# Restore database
psql memori < memori_backup.sql
```

### Automated Backup
```json
{
  "database": {
    "backup_enabled": true,
    "backup_interval_hours": 24,
    "backup_path": "/backups/memori",
    "backup_retention_days": 30
  }
}
```

## Monitoring

### Health Checks
```python
from memori import Memori

memori = Memori()

# Test connection
try:
    stats = memori.get_memory_stats()
    print("Database connection: OK")
except Exception as e:
    print(f"Database error: {e}")
```

### Performance Metrics
```python
# Get database performance stats
perf_stats = memori.db_manager.get_performance_stats()
print(f"Query time avg: {perf_stats['avg_query_time']}ms")
print(f"Connection pool usage: {perf_stats['pool_usage']}%")
```

### Logging
```json
{
  "database": {
    "echo_sql": true,           // Log all SQL queries
    "log_slow_queries": true,   // Log queries > threshold
    "slow_query_threshold": 1000 // Threshold in milliseconds
  }
}
```

## Security

### Connection Security
```python
# SSL connection (PostgreSQL)
"postgresql://user:pass@host:5432/db?sslmode=require"

# SSL with certificate verification
"postgresql://user:pass@host:5432/db?sslmode=verify-full&sslcert=client.crt&sslkey=client.key"
```

### Access Control
```sql
-- PostgreSQL: Create limited user
CREATE USER memori_app WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO memori_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO memori_app;
```

### Environment Variables
```bash
# Secure connection string storage
export MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:${DB_PASSWORD}@host:5432/memori"
export DB_PASSWORD="secure_password"
```

## Troubleshooting

### Common Issues

#### Connection Refused
```bash
# Check database is running
sudo systemctl status postgresql

# Check connection
psql -h localhost -U user -d memori
```

#### Permission Denied
```sql
-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE memori TO user;
GRANT ALL ON SCHEMA public TO user;
```

#### Pool Exhaustion
```json
{
  "database": {
    "pool_size": 30,      // Increase pool size
    "max_overflow": 20,   // Allow overflow connections
    "pool_timeout": 60    // Increase timeout
  }
}
```

#### Slow Queries
```python
# Enable query logging
memori = Memori(database_connect="postgresql://...?echo=true")

# Check slow queries
stats = memori.db_manager.get_slow_queries()
```

### Debug Mode
```python
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

memori = Memori(
    database_connect="postgresql://...",
    debug=True  # Enables detailed logging
)
```

## Next Steps

- [Settings](settings.md) - Full configuration options
- [Examples](https://github.com/GibsonAI/memori/tree/main/examples) - Explore more examples
- [Framework Integrations](https://github.com/GibsonAI/memori/tree/main/examples/integrations) - See how Memori works seamlessly with popular AI Agent frameworks
- [Demos](https://github.com/GibsonAI/memori/tree/main/demos) - Explore Memori's capabilities through these demos