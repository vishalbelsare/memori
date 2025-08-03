"""
Centralized logging configuration for Memoriai
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from ..config.settings import LoggingSettings, LogLevel
from .exceptions import ConfigurationError


class LoggingManager:
    """Centralized logging management"""
    
    _initialized = False
    _current_config: Optional[LoggingSettings] = None
    
    @classmethod
    def setup_logging(cls, settings: LoggingSettings) -> None:
        """Setup logging configuration"""
        try:
            # Remove default handler if it exists
            if not cls._initialized:
                logger.remove()
            
            # Configure console logging
            logger.add(
                sys.stderr,
                level=settings.level.value,
                format=settings.format,
                colorize=True,
                backtrace=True,
                diagnose=True,
            )
            
            # Configure file logging if enabled
            if settings.log_to_file:
                log_path = Path(settings.log_file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                if settings.structured_logging:
                    # JSON structured logging
                    logger.add(
                        log_path,
                        level=settings.level.value,
                        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
                        rotation=settings.log_rotation,
                        retention=settings.log_retention,
                        compression=settings.log_compression,
                        serialize=True,
                    )
                else:
                    # Regular text logging
                    logger.add(
                        log_path,
                        level=settings.level.value,
                        format=settings.format,
                        rotation=settings.log_rotation,
                        retention=settings.log_retention,
                        compression=settings.log_compression,
                    )
            
            cls._initialized = True
            cls._current_config = settings
            logger.info("Logging configuration initialized")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to setup logging: {e}")
    
    @classmethod
    def get_logger(cls, name: str) -> "logger":
        """Get a logger instance with the given name"""
        return logger.bind(name=name)
    
    @classmethod
    def update_log_level(cls, level: LogLevel) -> None:
        """Update the logging level"""
        if not cls._initialized:
            raise ConfigurationError("Logging not initialized")
        
        try:
            # Remove existing handlers and recreate with new level
            logger.remove()
            
            if cls._current_config:
                cls._current_config.level = level
                cls.setup_logging(cls._current_config)
            
        except Exception as e:
            logger.error(f"Failed to update log level: {e}")
    
    @classmethod
    def add_custom_handler(cls, handler_config: Dict[str, Any]) -> None:
        """Add a custom logging handler"""
        try:
            logger.add(**handler_config)
            logger.debug(f"Added custom logging handler: {handler_config}")
        except Exception as e:
            logger.error(f"Failed to add custom handler: {e}")
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if logging is initialized"""
        return cls._initialized
    
    @classmethod
    def get_current_config(cls) -> Optional[LoggingSettings]:
        """Get current logging configuration"""
        return cls._current_config


def get_logger(name: str = "memori") -> "logger":
    """Convenience function to get a logger"""
    return LoggingManager.get_logger(name)