"""
Unit tests for memoriai.config.settings module.
"""

import os
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from memoriai.config.settings import (
    AgentSettings,
    DatabaseSettings,
    LoggingSettings,
    MemoriSettings,
    MemorySettings,
)


class TestDatabaseSettings:
    """Test the DatabaseSettings class."""

    def test_database_settings_defaults(self):
        """Test DatabaseSettings with default values."""
        settings = DatabaseSettings()

        assert settings.connection_string == "sqlite:///memoriai.db"
        assert settings.echo is False
        assert settings.pool_size == 5
        assert settings.max_overflow == 10
        assert settings.pool_timeout == 30
        assert settings.pool_recycle == 3600

    def test_database_settings_custom_values(self):
        """Test DatabaseSettings with custom values."""
        settings = DatabaseSettings(
            connection_string="postgresql://user:pass@localhost/db",
            echo=True,
            pool_size=10,
            max_overflow=20,
        )

        assert settings.connection_string == "postgresql://user:pass@localhost/db"
        assert settings.echo is True
        assert settings.pool_size == 10
        assert settings.max_overflow == 20

    def test_database_settings_validation(self):
        """Test DatabaseSettings validation."""
        # Test invalid pool size
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_size=-1)

        # Test invalid max overflow
        with pytest.raises(ValidationError):
            DatabaseSettings(max_overflow=-1)

        # Test invalid timeout
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_timeout=-1)

    def test_database_settings_from_env(self):
        """Test DatabaseSettings loading from environment variables."""
        with patch.dict(
            os.environ,
            {
                "MEMORI_DATABASE__CONNECTION_STRING": "postgresql://test:test@localhost/test",
                "MEMORI_DATABASE__ECHO": "true",
                "MEMORI_DATABASE__POOL_SIZE": "15",
            },
        ):
            settings = DatabaseSettings()

            assert settings.connection_string == "postgresql://test:test@localhost/test"
            assert settings.echo is True
            assert settings.pool_size == 15


class TestAgentSettings:
    """Test the AgentSettings class."""

    def test_agent_settings_defaults(self):
        """Test AgentSettings with default values."""
        settings = AgentSettings()

        assert settings.default_model == "gpt-3.5-turbo"
        assert settings.default_temperature == 0.7
        assert settings.max_tokens == 1000
        assert settings.timeout == 30
        assert settings.retry_attempts == 3

    def test_agent_settings_custom_values(self):
        """Test AgentSettings with custom values."""
        settings = AgentSettings(
            default_model="gpt-4",
            default_temperature=0.5,
            max_tokens=2000,
            timeout=60,
        )

        assert settings.default_model == "gpt-4"
        assert settings.default_temperature == 0.5
        assert settings.max_tokens == 2000
        assert settings.timeout == 60

    def test_agent_settings_validation(self):
        """Test AgentSettings validation."""
        # Test invalid temperature
        with pytest.raises(ValidationError):
            AgentSettings(default_temperature=2.0)  # > 1.0

        with pytest.raises(ValidationError):
            AgentSettings(default_temperature=-0.1)  # < 0.0

        # Test invalid max_tokens
        with pytest.raises(ValidationError):
            AgentSettings(max_tokens=0)

        # Test invalid timeout
        with pytest.raises(ValidationError):
            AgentSettings(timeout=-1)


class TestLoggingSettings:
    """Test the LoggingSettings class."""

    def test_logging_settings_defaults(self):
        """Test LoggingSettings with default values."""
        settings = LoggingSettings()

        assert settings.level == "INFO"
        assert settings.format_string == "{time} | {level} | {name} | {message}"
        assert settings.file_path is None
        assert settings.rotation == "1 day"
        assert settings.retention == "1 week"

    def test_logging_settings_custom_values(self):
        """Test LoggingSettings with custom values."""
        settings = LoggingSettings(
            level="DEBUG",
            file_path="/var/log/memoriai.log",
            rotation="12 hours",
            retention="1 month",
        )

        assert settings.level == "DEBUG"
        assert settings.file_path == "/var/log/memoriai.log"
        assert settings.rotation == "12 hours"
        assert settings.retention == "1 month"

    def test_logging_settings_validation(self):
        """Test LoggingSettings validation."""
        # Test invalid log level
        with pytest.raises(ValidationError):
            LoggingSettings(level="INVALID")


class TestMemorySettings:
    """Test the MemorySettings class."""

    def test_memory_settings_defaults(self):
        """Test MemorySettings with default values."""
        settings = MemorySettings()

        assert settings.default_namespace == "default"
        assert settings.max_memory_age_days == 365
        assert settings.cleanup_interval_hours == 24
        assert settings.importance_threshold == 0.5
        assert settings.max_memories_per_query == 100

    def test_memory_settings_custom_values(self):
        """Test MemorySettings with custom values."""
        settings = MemorySettings(
            default_namespace="custom",
            max_memory_age_days=180,
            cleanup_interval_hours=12,
            importance_threshold=0.7,
        )

        assert settings.default_namespace == "custom"
        assert settings.max_memory_age_days == 180
        assert settings.cleanup_interval_hours == 12
        assert settings.importance_threshold == 0.7

    def test_memory_settings_validation(self):
        """Test MemorySettings validation."""
        # Test invalid importance threshold
        with pytest.raises(ValidationError):
            MemorySettings(importance_threshold=1.5)  # > 1.0

        with pytest.raises(ValidationError):
            MemorySettings(importance_threshold=-0.1)  # < 0.0

        # Test invalid max_memory_age_days
        with pytest.raises(ValidationError):
            MemorySettings(max_memory_age_days=0)


class TestMemoriSettings:
    """Test the MemoriSettings class."""

    def test_memori_settings_defaults(self):
        """Test MemoriSettings with default values."""
        settings = MemoriSettings()

        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.agents, AgentSettings)
        assert isinstance(settings.logging, LoggingSettings)
        assert isinstance(settings.memory, MemorySettings)

    def test_memori_settings_custom_values(self):
        """Test MemoriSettings with custom nested settings."""
        settings = MemoriSettings(
            database=DatabaseSettings(connection_string="postgresql://localhost/test"),
            agents=AgentSettings(
                default_model="gpt-4",
                default_temperature=0.5,
            ),
            memory=MemorySettings(
                default_namespace="test_namespace",
                importance_threshold=0.8,
            ),
        )

        assert settings.database.connection_string == "postgresql://localhost/test"
        assert settings.agents.default_model == "gpt-4"
        assert settings.agents.default_temperature == 0.5
        assert settings.memory.default_namespace == "test_namespace"
        assert settings.memory.importance_threshold == 0.8

    def test_memori_settings_from_dict(self):
        """Test MemoriSettings creation from dictionary."""
        config_dict = {
            "database": {
                "connection_string": "sqlite:///test.db",
                "echo": True,
            },
            "agents": {
                "default_model": "gpt-4",
                "max_tokens": 2000,
            },
            "memory": {
                "default_namespace": "test",
                "importance_threshold": 0.6,
            },
        }

        settings = MemoriSettings(**config_dict)

        assert settings.database.connection_string == "sqlite:///test.db"
        assert settings.database.echo is True
        assert settings.agents.default_model == "gpt-4"
        assert settings.agents.max_tokens == 2000
        assert settings.memory.default_namespace == "test"
        assert settings.memory.importance_threshold == 0.6

    def test_memori_settings_from_env_variables(self):
        """Test MemoriSettings loading from environment variables."""
        env_vars = {
            "MEMORI_DATABASE__CONNECTION_STRING": "postgresql://env:test@localhost/env",
            "MEMORI_DATABASE__ECHO": "true",
            "MEMORI_AGENTS__DEFAULT_MODEL": "gpt-4",
            "MEMORI_AGENTS__DEFAULT_TEMPERATURE": "0.3",
            "MEMORI_MEMORY__DEFAULT_NAMESPACE": "env_namespace",
            "MEMORI_MEMORY__IMPORTANCE_THRESHOLD": "0.9",
            "MEMORI_LOGGING__LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, env_vars):
            settings = MemoriSettings()

            assert (
                settings.database.connection_string
                == "postgresql://env:test@localhost/env"
            )
            assert settings.database.echo is True
            assert settings.agents.default_model == "gpt-4"
            assert settings.agents.default_temperature == 0.3
            assert settings.memory.default_namespace == "env_namespace"
            assert settings.memory.importance_threshold == 0.9
            assert settings.logging.level == "DEBUG"

    def test_memori_settings_to_dict(self):
        """Test converting MemoriSettings to dictionary."""
        settings = MemoriSettings(
            database=DatabaseSettings(connection_string="test://connection"),
            agents=AgentSettings(default_model="test-model"),
        )

        settings_dict = settings.model_dump()

        assert isinstance(settings_dict, dict)
        assert "database" in settings_dict
        assert "agents" in settings_dict
        assert "logging" in settings_dict
        assert "memory" in settings_dict
        assert settings_dict["database"]["connection_string"] == "test://connection"
        assert settings_dict["agents"]["default_model"] == "test-model"

    def test_memori_settings_json_serialization(self):
        """Test JSON serialization of MemoriSettings."""
        settings = MemoriSettings()

        json_str = settings.model_dump_json()
        assert isinstance(json_str, str)
        assert "database" in json_str
        assert "agents" in json_str

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"database": {"connection_string": "file://test"}}',
    )
    def test_memori_settings_from_file(self, mock_file):
        """Test loading MemoriSettings from JSON file."""
        import json

        # Mock the JSON loading
        with patch("json.load") as mock_json_load:
            mock_json_load.return_value = {
                "database": {"connection_string": "file://test"},
                "agents": {"default_model": "file-model"},
            }

            # This would be implemented in the config manager
            with open("test_config.json") as f:
                config_data = json.load(f)
                settings = MemoriSettings(**config_data)

            assert settings.database.connection_string == "file://test"
            assert settings.agents.default_model == "file-model"

    def test_memori_settings_validation_errors(self):
        """Test validation errors in nested settings."""
        with pytest.raises(ValidationError):
            MemoriSettings(database=DatabaseSettings(pool_size=-1))  # Invalid pool size

        with pytest.raises(ValidationError):
            MemoriSettings(
                agents=AgentSettings(default_temperature=2.0)  # Invalid temperature
            )

        with pytest.raises(ValidationError):
            MemoriSettings(
                memory=MemorySettings(importance_threshold=1.5)  # Invalid threshold
            )

    def test_memori_settings_partial_updates(self):
        """Test partial updates to MemoriSettings."""
        settings = MemoriSettings()
        original_db_string = settings.database.connection_string

        # Update only database settings
        updated_settings = MemoriSettings(
            database=DatabaseSettings(
                connection_string="postgresql://updated/db",
                echo=True,
            ),
            # Keep other settings as defaults
            agents=settings.agents,
            logging=settings.logging,
            memory=settings.memory,
        )

        assert updated_settings.database.connection_string == "postgresql://updated/db"
        assert updated_settings.database.echo is True
        # Other settings should remain as original defaults
        assert updated_settings.agents.default_model == settings.agents.default_model
        assert (
            updated_settings.memory.default_namespace
            == settings.memory.default_namespace
        )
