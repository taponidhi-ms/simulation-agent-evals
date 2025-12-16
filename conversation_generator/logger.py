"""
Centralized logging configuration for the simulation agent evals project.

This module sets up Python's logging framework with best practices:
- Logs are persisted in the logs/ directory at repository root
- Console and file handlers for comprehensive logging
- Rotating file handler to prevent large log files
- Timestamps on all log entries
- Configurable log levels
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


# Log directory at repository root
REPO_ROOT = Path(__file__).parent.parent
LOGS_DIR = REPO_ROOT / "logs"

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)

# Log file naming
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILENAME = f"simulation_agent_evals_{TIMESTAMP}.log"

# Log format with timestamp
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO


def setup_logger(
    name: str,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger with file and console handlers.
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # File handler with rotation (max 10MB per file, keep 5 backup files)
    if log_to_file:
        log_file_path = LOGS_DIR / LOG_FILENAME
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler for real-time output
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance. If not already set up, creates one with default config.
    
    Args:
        name: Name of the logger (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


def log_llm_interaction(
    logger: logging.Logger,
    agent_type: str,
    prompt: str,
    response: str,
    model: str,
    temperature: float,
    turn_number: int = None
):
    """
    Log LLM interaction with structured formatting for easy transcript reading.
    
    Args:
        logger: Logger instance to use
        agent_type: Type of agent (e.g., "Customer", "CSR", "PersonaGenerator")
        prompt: The prompt sent to the LLM
        response: The response from the LLM
        model: Model name used
        temperature: Temperature parameter used
        turn_number: Optional turn number in conversation
    """
    separator = "=" * 80
    turn_info = f" (Turn {turn_number})" if turn_number else ""
    
    logger.info(f"\n{separator}")
    logger.info(f"LLM INTERACTION - {agent_type}{turn_info}")
    logger.info(f"Model: {model}, Temperature: {temperature}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    logger.info(f"{separator}")
    logger.info(f"PROMPT:\n{prompt}")
    logger.info(f"{separator}")
    logger.info(f"RESPONSE:\n{response}")
    logger.info(f"{separator}\n")
