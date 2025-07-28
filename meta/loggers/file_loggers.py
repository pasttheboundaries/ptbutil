
import logging
from logging.handlers import RotatingFileHandler


def get_file_logger(name: str, log_file: str,
               max_bytes: int = 1024 * 1024,
               backup_count: int = 5,
               level: int = logging.INFO) -> logging.Logger:
    """
    Factory function to create or get a logger with rotating file handler.

    Args:
        name: Logger name
        log_file: Path to log file
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        level: Logging level

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only add handler if the logger doesn't already have handlers
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Create rotating file handler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        handler.setFormatter(formatter)

        # Add handler and set level
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger
