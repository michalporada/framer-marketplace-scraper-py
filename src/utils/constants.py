"""Constants used throughout the scraper application."""

# Progress logging milestones (as percentages)
PROGRESS_MILESTONES = [0.1, 0.25, 0.5, 0.75, 0.9]

# Progress logging interval (log every N items)
PROGRESS_LOG_INTERVAL = 50

# Retry configuration
RETRY_EXPONENTIAL_BASE = 2.0
DEFAULT_RETRY_INITIAL_WAIT = 1.0
DEFAULT_RETRY_MAX_WAIT = 60.0

# HTTP configuration
DEFAULT_TIMEOUT = 30

# Checkpoint configuration
DEFAULT_CHECKPOINT_FILE = "data/checkpoint.json"
