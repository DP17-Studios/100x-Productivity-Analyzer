#!/usr/bin/env python3
"""
Logging configuration for the Productivity Agent
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import Optional

def setup_logger(
    name: str, 
    log_level: str = "INFO",
    log_dir: Optional[str] = None
) -> logging.Logger:
    """Setup and configure logger with file and console handlers"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log directory is provided)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        
        # Main log file
        log_file = os.path.join(log_dir, f'productivity_agent_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
        
        # Error log file
        error_log_file = os.path.join(log_dir, f'productivity_agent_errors_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get existing logger or create new one"""
    return logging.getLogger(name)

def set_log_level(level: str):
    """Set log level for all loggers"""
    level = level.upper()
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level))
    
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(getattr(logging, level))

def log_function_call(func):
    """Decorator to log function calls"""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    
    return wrapper