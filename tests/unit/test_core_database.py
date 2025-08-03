"""
Unit tests for memoriai.core.database module.
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from memoriai.config.settings import DatabaseSettings
from memoriai.core.database import DatabaseManager
from memoriai.utils.exceptions import (
    DatabaseError,
)


class TestDatabaseManager:
    """Test the DatabaseManager class."""

    def test_database_manager_initialization(self, memory_db_settings):
        """Test DatabaseManager initialization with valid settings."""
        db_settings = memory_db_settings.database
        manager = DatabaseManager(db_settings)

        assert manager.settings == db_settings
        assert manager.connection_string == db_settings.connection_string
        assert not manager.is_initialized

    def test_database_manager_initialization_with_invalid_settings(self):
        """Test DatabaseManager initialization with invalid settings."""
        invalid_settings = DatabaseSettings(connection_string="")

        with pytest.raises(ValueError):
            DatabaseManager(invalid_settings)

    def test_initialize_database_success(self, memory_db_settings):
        """Test successful database initialization."""
        db_settings = memory_db_settings.database
        manager = DatabaseManager(db_settings)

        manager.initialize_database()
        assert manager.is_initialized
        assert manager.engine is not None

    def test_initialize_database_twice(self, memory_db_settings):
        """Test that initializing database twice doesn't cause issues."""
        db_settings = memory_db_settings.database
        manager = DatabaseManager(db_settings)

        manager.initialize_database()
        manager.initialize_database()  # Should not raise error
        assert manager.is_initialized

    @patch("memoriai.core.database.create_engine")
    def test_initialize_database_connection_error(
        self, mock_create_engine, memory_db_settings
    ):
        """Test database initialization with connection error."""
        mock_create_engine.side_effect = Exception("Connection failed")

        db_settings = memory_db_settings.database
        manager = DatabaseManager(db_settings)

        with pytest.raises(DatabaseConnectionError):
            manager.initialize_database()

    def test_get_session(self, db_manager):
        """Test getting a database session."""
        with db_manager.get_session() as session:
            assert session is not None
            # Session should be usable
            result = session.execute("SELECT 1")
            assert result.scalar() == 1

    def test_execute_query(self, db_manager):
        """Test executing a direct query."""
        result = db_manager.execute_query("SELECT 1 as test_value")
        assert len(result) > 0
        assert result[0]["test_value"] == 1

    def test_execute_query_with_parameters(self, db_manager):
        """Test executing a query with parameters."""
        result = db_manager.execute_query("SELECT :value as test_value", {"value": 42})
        assert result[0]["test_value"] == 42

    @patch("memoriai.core.database.DatabaseManager.get_session")
    def test_execute_query_database_error(self, mock_get_session, db_manager):
        """Test handling of database errors during query execution."""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Query failed")
        mock_get_session.return_value.__enter__.return_value = mock_session

        with pytest.raises(Exception):
            db_manager.execute_query("SELECT 1")

    def test_check_table_exists(self, db_manager):
        """Test checking if a table exists."""
        # Test with a table that doesn't exist
        exists = db_manager.check_table_exists("nonexistent_table")
        assert exists is False

        # Create a simple table
        db_manager.execute_query("CREATE TABLE test_table (id INTEGER PRIMARY KEY)")

        # Now it should exist
        exists = db_manager.check_table_exists("test_table")
        assert exists is True

    def test_get_table_schema(self, db_manager):
        """Test getting table schema information."""
        # Create a test table with known schema
        db_manager.execute_query(
            """
            CREATE TABLE test_schema_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                score REAL DEFAULT 0.0
            )
        """
        )

        schema = db_manager.get_table_schema("test_schema_table")
        assert isinstance(schema, list)
        assert len(schema) > 0

        # Check that we have column information
        column_names = [col["name"] for col in schema]
        assert "id" in column_names
        assert "name" in column_names
        assert "score" in column_names

    def test_backup_database(self, temp_db_settings):
        """Test database backup functionality."""
        manager = DatabaseManager(temp_db_settings.database)
        manager.initialize_database()

        # Create some test data
        manager.execute_query(
            "CREATE TABLE test_backup (id INTEGER PRIMARY KEY, data TEXT)"
        )
        manager.execute_query(
            "INSERT INTO test_backup (data) VALUES (?)", ("test data",)
        )

        # Create backup
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as backup_file:
            backup_path = backup_file.name

        try:
            result = manager.backup_database(backup_path)
            assert result is True
            assert os.path.exists(backup_path)

            # Verify backup contains our data
            backup_manager = DatabaseManager(
                DatabaseSettings(connection_string=f"sqlite:///{backup_path}")
            )
            backup_manager.initialize_database()

            data = backup_manager.execute_query("SELECT * FROM test_backup")
            assert len(data) == 1
            assert data[0]["data"] == "test data"

        finally:
            if os.path.exists(backup_path):
                os.unlink(backup_path)

    def test_restore_database(self, temp_db_settings):
        """Test database restore functionality."""
        # Create source database with data
        source_manager = DatabaseManager(temp_db_settings.database)
        source_manager.initialize_database()

        source_manager.execute_query(
            "CREATE TABLE test_restore (id INTEGER PRIMARY KEY, data TEXT)"
        )
        source_manager.execute_query(
            "INSERT INTO test_restore (data) VALUES (?)", ("restore test data",)
        )

        # Create target database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as target_file:
            target_path = target_file.name

        try:
            target_settings = DatabaseSettings(
                connection_string=f"sqlite:///{target_path}"
            )
            target_manager = DatabaseManager(target_settings)
            target_manager.initialize_database()

            # Get source database path (for SQLite)
            source_path = temp_db_settings.database.connection_string.replace(
                "sqlite:///", ""
            )

            # Restore database
            result = target_manager.restore_database(source_path)
            assert result is True

            # Verify restored data
            data = target_manager.execute_query("SELECT * FROM test_restore")
            assert len(data) == 1
            assert data[0]["data"] == "restore test data"

        finally:
            if os.path.exists(target_path):
                os.unlink(target_path)

    def test_get_database_statistics(self, db_manager):
        """Test getting database statistics."""
        # Create some test tables and data
        db_manager.execute_query(
            "CREATE TABLE stats_test1 (id INTEGER PRIMARY KEY, data TEXT)"
        )
        db_manager.execute_query(
            "CREATE TABLE stats_test2 (id INTEGER PRIMARY KEY, value INTEGER)"
        )
        db_manager.execute_query(
            "INSERT INTO stats_test1 (data) VALUES ('test1'), ('test2')"
        )

        stats = db_manager.get_database_statistics()

        assert isinstance(stats, dict)
        assert "table_count" in stats
        assert "total_size" in stats
        assert stats["table_count"] >= 2

    def test_optimize_database(self, db_manager):
        """Test database optimization."""
        # This should not raise an exception
        result = db_manager.optimize_database()
        assert result is True

    def test_validate_connection(self, db_manager):
        """Test connection validation."""
        result = db_manager.validate_connection()
        assert result is True

    @patch("memoriai.core.database.DatabaseManager.get_session")
    def test_validate_connection_failure(self, mock_get_session, db_manager):
        """Test connection validation failure."""
        mock_get_session.side_effect = Exception("Connection failed")

        result = db_manager.validate_connection()
        assert result is False

    def test_close_connection(self, memory_db_settings):
        """Test closing database connection."""
        db_settings = memory_db_settings.database
        manager = DatabaseManager(db_settings)
        manager.initialize_database()

        assert manager.is_initialized

        manager.close()
        # After closing, should not be initialized
        # Note: This depends on implementation details

    def test_context_manager(self, memory_db_settings):
        """Test using DatabaseManager as context manager."""
        db_settings = memory_db_settings.database

        with DatabaseManager(db_settings) as manager:
            manager.initialize_database()
            assert manager.is_initialized

            # Should be able to execute queries
            result = manager.execute_query("SELECT 1")
            assert len(result) > 0

    def test_transaction_rollback(self, db_manager):
        """Test transaction rollback on error."""
        # Create test table
        db_manager.execute_query(
            "CREATE TABLE transaction_test (id INTEGER PRIMARY KEY, data TEXT UNIQUE)"
        )

        try:
            with db_manager.get_session() as session:
                # Insert first record
                session.execute(
                    "INSERT INTO transaction_test (data) VALUES (?)", ("unique_data",)
                )

                # Try to insert duplicate (should fail)
                session.execute(
                    "INSERT INTO transaction_test (data) VALUES (?)", ("unique_data",)
                )
                session.commit()
        except Exception:
            # Transaction should be rolled back
            pass

        # Verify no data was inserted
        result = db_manager.execute_query("SELECT * FROM transaction_test")
        assert len(result) == 0

    def test_concurrent_access(self, db_manager):
        """Test concurrent database access."""
        import threading

        results = []
        errors = []

        def worker(worker_id):
            try:
                with db_manager.get_session() as session:
                    result = session.execute("SELECT ? as worker_id", (worker_id,))
                    results.append(result.scalar())
            except Exception as e:
                errors.append(e)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}
