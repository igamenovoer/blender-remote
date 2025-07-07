"""Utility functions for BLD Remote MCP addon."""

import datetime


def log_message(level, message):
    """Standard logging format: [BLD Remote][LogLevel][Time] <message>"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[BLD Remote][{level}][{timestamp}] {message}")


def log_info(message):
    """Log an info message."""
    log_message("INFO", message)


def log_warning(message):
    """Log a warning message."""
    log_message("WARN", message)


def log_error(message):
    """Log an error message."""
    log_message("ERROR", message)


def log_debug(message):
    """Log a debug message."""
    log_message("DEBUG", message)