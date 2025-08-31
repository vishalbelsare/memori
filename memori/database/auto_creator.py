"""
Database Auto-Creation System

This module automatically creates databases if they don't exist, supporting
PostgreSQL and MySQL with proper error handling and security validation.
"""

from typing import Optional, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, ProgrammingError
from loguru import logger

from .connection_utils import DatabaseConnectionUtils


class DatabaseAutoCreator:
    """Handles automatic database creation for PostgreSQL and MySQL"""
    
    def __init__(self, enable_auto_creation: bool = True):
        """
        Initialize database auto-creator.
        
        Args:
            enable_auto_creation: Whether to enable automatic database creation
        """
        self.enable_auto_creation = enable_auto_creation
        self.utils = DatabaseConnectionUtils()
    
    def ensure_database_exists(self, connection_string: str) -> str:
        """
        Ensure target database exists, creating it if necessary.
        
        Args:
            connection_string: Original database connection string
            
        Returns:
            Connection string to use (may be unchanged if creation not needed)
            
        Raises:
            DatabaseCreationError: If database creation fails
        """
        if not self.enable_auto_creation:
            logger.debug("Auto-creation disabled, using original connection string")
            return connection_string
        
        try:
            # Parse connection string
            components = self.utils.parse_connection_string(connection_string)
            
            # SQLite doesn't need database creation
            if not components['needs_creation']:
                logger.debug(f"Database engine {components['engine']} auto-creates, no action needed")
                return connection_string
            
            # Validate database name
            if not self.utils.validate_database_name(components['database']):
                raise ValueError(f"Invalid database name: {components['database']}")
            
            # Check if database exists
            if self._database_exists(components):
                logger.debug(f"Database '{components['database']}' already exists")
                return connection_string
            
            # Create database
            self._create_database(components)
            logger.info(f"Successfully created database '{components['database']}'")
            return connection_string
            
        except Exception as e:
            logger.error(f"Database auto-creation failed: {e}")
            # Don't raise exception - let the original connection attempt proceed
            # This allows graceful degradation if user has manual setup
            return connection_string
    
    def _database_exists(self, components: Dict[str, str]) -> bool:
        """Check if target database exists."""
        try:
            engine = components['engine']
            
            if engine == 'postgresql':
                return self._postgresql_database_exists(components)
            elif engine == 'mysql':
                return self._mysql_database_exists(components)
            else:
                logger.warning(f"Database existence check not supported for {engine}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to check database existence: {e}")
            return False
    
    def _postgresql_database_exists(self, components: Dict[str, str]) -> bool:
        """Check if PostgreSQL database exists."""
        try:
            # Connect to postgres system database
            engine = create_engine(components['default_url'])
            
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": components['database']}
                )
                exists = result.fetchone() is not None
                
            engine.dispose()
            return exists
            
        except Exception as e:
            logger.error(f"PostgreSQL database existence check failed: {e}")
            return False
    
    def _mysql_database_exists(self, components: Dict[str, str]) -> bool:
        """Check if MySQL database exists."""
        try:
            # Connect to mysql system database
            engine = create_engine(components['default_url'])
            
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :dbname"),
                    {"dbname": components['database']}
                )
                exists = result.fetchone() is not None
                
            engine.dispose()
            return exists
            
        except Exception as e:
            logger.error(f"MySQL database existence check failed: {e}")
            return False
    
    def _create_database(self, components: Dict[str, str]) -> None:
        """Create the target database."""
        engine = components['engine']
        
        if engine == 'postgresql':
            self._create_postgresql_database(components)
        elif engine == 'mysql':
            self._create_mysql_database(components)
        else:
            raise ValueError(f"Database creation not supported for {engine}")
    
    def _create_postgresql_database(self, components: Dict[str, str]) -> None:
        """Create PostgreSQL database."""
        try:
            logger.info(f"Creating PostgreSQL database '{components['database']}'...")
            
            # Connect to postgres system database
            engine = create_engine(components['default_url'])
            
            # PostgreSQL requires autocommit for CREATE DATABASE
            with engine.connect() as conn:
                # Set autocommit mode
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                
                # Create database (can't use parameters for database name)
                # Database name is already validated, so this is safe
                conn.execute(text(f'CREATE DATABASE "{components["database"]}"'))
                
            engine.dispose()
            logger.info(f"PostgreSQL database '{components['database']}' created successfully")
            
        except (OperationalError, ProgrammingError) as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                logger.info(f"PostgreSQL database '{components['database']}' already exists")
                return
            elif "permission denied" in error_msg.lower():
                raise PermissionError(f"Insufficient permissions to create database '{components['database']}'")
            else:
                raise RuntimeError(f"Failed to create PostgreSQL database: {e}")
        
        except Exception as e:
            raise RuntimeError(f"Unexpected error creating PostgreSQL database: {e}")
    
    def _create_mysql_database(self, components: Dict[str, str]) -> None:
        """Create MySQL database."""
        try:
            logger.info(f"Creating MySQL database '{components['database']}'...")
            
            # Connect to mysql system database
            engine = create_engine(components['default_url'])
            
            with engine.connect() as conn:
                # Create database (can't use parameters for database name)
                # Database name is already validated, so this is safe
                conn.execute(text(f'CREATE DATABASE `{components["database"]}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'))
                conn.commit()
                
            engine.dispose()
            logger.info(f"MySQL database '{components['database']}' created successfully")
            
        except (OperationalError, ProgrammingError) as e:
            error_msg = str(e)
            if "database exists" in error_msg.lower():
                logger.info(f"MySQL database '{components['database']}' already exists")
                return
            elif "access denied" in error_msg.lower():
                raise PermissionError(f"Insufficient permissions to create database '{components['database']}'")
            else:
                raise RuntimeError(f"Failed to create MySQL database: {e}")
        
        except Exception as e:
            raise RuntimeError(f"Unexpected error creating MySQL database: {e}")
    
    def get_database_info(self, connection_string: str) -> Dict[str, str]:
        """
        Get detailed information about database from connection string.
        
        Args:
            connection_string: Database connection URL
            
        Returns:
            Dictionary with database information
        """
        try:
            components = self.utils.parse_connection_string(connection_string)
            
            info = {
                'engine': components['engine'],
                'database': components['database'],
                'host': components['host'],
                'port': components['port'],
                'needs_creation': components['needs_creation'],
                'auto_creation_enabled': self.enable_auto_creation,
            }
            
            # Add existence check if auto-creation is enabled
            if self.enable_auto_creation and components['needs_creation']:
                info['exists'] = self._database_exists(components)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {'error': str(e)}


class DatabaseCreationError(Exception):
    """Raised when database creation fails"""
    pass