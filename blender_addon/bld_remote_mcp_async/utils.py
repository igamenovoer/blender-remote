"""Utility functions for BLD Remote MCP addon."""

import datetime
import os

# Logging level constants (matching Python's logging module)
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'WARN': 30,  # Alias for WARNING
    'ERROR': 40,
    'CRITICAL': 50,
}

def _get_log_level():
    """Get the current log level from environment variable BLD_REMOTE_LOG_LEVEL.
    
    Returns:
        int: The numeric log level (default: 20 for INFO)
    """
    env_level = os.environ.get('BLD_REMOTE_LOG_LEVEL', 'INFO').upper().strip()
    return LOG_LEVELS.get(env_level, 20)  # Default to INFO level


def _should_log(level):
    """Check if a message at the given level should be logged.
    
    Args:
        level (str): The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        bool: True if the message should be logged, False otherwise
    """
    current_level = _get_log_level()
    message_level = LOG_LEVELS.get(level.upper(), 0)
    return message_level >= current_level


def log_message(level, message):
    """Standard logging format: [BLD Remote][LogLevel][Time] <message>"""
    if _should_log(level):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[BLD Remote][{level}][{timestamp}] {message}")


def log_info(message):
    """Log an info message."""
    log_message("INFO", message)


def log_warning(message):
    """Log a warning message."""
    log_message("WARNING", message)


def log_error(message):
    """Log an error message."""
    log_message("ERROR", message)


def log_debug(message):
    """Log a debug message."""
    log_message("DEBUG", message)


def log_critical(message):
    """Log a critical message."""
    log_message("CRITICAL", message)