"""Base service class for Asus TUF utilities."""

import cython
import logging
from functools import wraps
from time import sleep
from typing import TextIO, Dict
from contextlib import contextmanager

from config import MAX_RETRIES, INITIAL_RETRY_DELAY

logger = logging.getLogger('TUFUtils.BaseService')

def retry_with_backoff(max_retries: int = MAX_RETRIES, initial_delay: float = INITIAL_RETRY_DELAY):
    """Decorator for retrying operations with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for retry in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if retry == max_retries - 1:
                        raise
                    logger.warning(f"Retrying {func.__name__} after error: {str(e)}")
                    sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

@cython.cclass
class BaseService:
    """Base service class with common functionality."""
    
    _file_descriptors: Dict[str, TextIO]
    
    def __init__(self):
        """Initialize the base service."""
        self._file_descriptors = {}
    
    def cleanup(self):
        """Clean up resources."""
        self._close_cached_files()
    
    @contextmanager
    def _get_cached_file(self, filepath: str, mode: str = 'r') -> TextIO:
        """Get a cached file descriptor or open a new one."""
        if filepath in self._file_descriptors:
            fd = self._file_descriptors[filepath]
            fd.seek(0)
            yield fd
        else:
            with open(filepath, mode) as f:
                yield f
    
    def _close_cached_files(self):
        """Close all cached file descriptors."""
        for fd in self._file_descriptors.values():
            try:
                fd.close()
            except Exception as e:
                logger.error(f"Error closing file descriptor: {str(e)}")
        self._file_descriptors.clear()
    
    @cython.cfunc
    @retry_with_backoff()
    def _write_to_file(self, filepath: str, content: str) -> None:
        """Write content to a file with error handling and retry."""
        try:
            with self._get_cached_file(filepath, 'w') as f:
                f.write(content)
                f.flush()
        except IOError as e:
            logger.error(f"Failed to write to {filepath}: {str(e)}")
            raise
    
    @cython.cfunc
    @retry_with_backoff()
    def _read_from_file(self, filepath: str) -> str:
        """Read content from a file with error handling and retry."""
        try:
            with self._get_cached_file(filepath) as f:
                return f.read()
        except IOError as e:
            logger.error(f"Failed to read from {filepath}: {str(e)}")
            raise
