# Logging Framework

## Overview

This project uses a centralized logging framework built on Python's standard `logging` module. All logs are persisted to the `logs/` directory at the repository root with timestamps.

## Features

- **Centralized Configuration**: All logging is configured through `conversation_generator/logger.py`
- **Dual Output**: Logs are written to both console (for real-time monitoring) and files (for persistence)
- **Timestamps**: All log entries include timestamps in the format `YYYY-MM-DD HH:MM:SS`
- **Rotating Files**: Log files automatically rotate when they reach 10MB, with up to 5 backup files kept
- **LLM Interaction Logging**: Special formatting for LLM prompts and responses to create readable transcripts

## Usage

### Basic Logging

```python
from conversation_generator.logger import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Use different log levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
```

### Logging LLM Interactions

For logging LLM requests and responses (especially useful during conversation generation):

```python
from conversation_generator.logger import get_logger, log_llm_interaction

logger = get_logger(__name__)

# Log an LLM interaction
log_llm_interaction(
    logger=logger,
    agent_type="Customer",  # or "CSR", "PersonaGenerator", etc.
    prompt="The full prompt sent to the LLM",
    response="The LLM's response",
    model="gpt-4",
    temperature=0.7,
    turn_number=1  # Optional: for conversations
)
```

This creates a nicely formatted log entry that includes:
- Agent type and turn number
- Model and temperature settings
- Precise timestamp (with milliseconds)
- Full prompt and response text
- Visual separators for easy reading

## Log Files

### Location

All logs are written to: `<repository_root>/logs/`

The logs directory is excluded from git via `.gitignore`.

### File Naming

Log files are named with timestamps: `simulation_agent_evals_YYYYMMDD_HHMMSS.log`

Example: `simulation_agent_evals_20251216_143022.log`

### File Rotation

- Maximum file size: 10MB
- Backup count: 5 files
- Old files are automatically renamed with `.1`, `.2`, etc. suffixes
- When the limit is reached, the oldest backup is deleted

## Log Levels

The default log level is `INFO`. To see debug messages, modify the `DEFAULT_LOG_LEVEL` in `conversation_generator/logger.py` or pass a different level when calling `setup_logger()`.

Available levels (in order of verbosity):
- `logging.DEBUG` - Detailed diagnostic information
- `logging.INFO` - General informational messages (default)
- `logging.WARNING` - Warning messages
- `logging.ERROR` - Error messages
- `logging.CRITICAL` - Critical errors

## Benefits

1. **Live Transcripts**: During conversation simulation, you can watch the LLM interactions in real-time through the console output
2. **Debugging**: All LLM prompts and responses are logged with timestamps, making it easy to trace issues
3. **Audit Trail**: Complete history of operations is preserved in log files
4. **Verbose Output**: More detailed information than simple print statements, making the system less of a "black box"

## Migration from print()

If you're updating old code that uses `print()`, replace it with appropriate logger calls:

```python
# Old
print("Starting process...")
print(f"Error: {error_message}")

# New
logger.info("Starting process...")
logger.error(f"Error: {error_message}")
```

For LLM interactions specifically, use the `log_llm_interaction()` helper function instead of manually logging the prompt and response.
