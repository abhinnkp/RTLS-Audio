import logging
import os
import sys

def setup_logger(log_dir: str = None, console_only: bool = False, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger("rtls-audio")
    logger.setLevel(level)

    # Remove existing handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if not console_only and log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "rtls-audio.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except PermissionError:
            logger.warning(f"Permission denied to create log directory {log_dir}. Falling back to console only.")
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}. Falling back to console only.")

    return logger

def get_logger() -> logging.Logger:
    return logging.getLogger("rtls-audio")
