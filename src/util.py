import logging
import os
import sys

def setup_logging(log_file: str = None, level=logging.INFO):
    """
    Sets up logging to output to a file with timestamped entries.

    If no log_file is provided, defaults to `[calling_script_name].log` inside
    a 'logs' folder at the project root (where main.py or the calling script is).

    Args:
        log_file: Path to the log file. If None, defaults to 'logs/[script_name].log'
        level: Logging level (e.g., logging.INFO, logging.DEBUG)

    Returns:
        Logger instance
    """
    # Determine project root (directory containing the main script)
    project_root = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Default log file name
    if log_file is None:
        script_name = os.path.basename(sys.argv[0])
        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{script_name}.log")
    else:
        # Ensure the directory for a custom log_file exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    # Configure file logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename=log_file,
        filemode="a",  # append
    )

    # Add console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logging.getLogger().addHandler(console_handler)

    return logging.getLogger()