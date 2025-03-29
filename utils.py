"""
Utility functions for the Dependency Booster add-on.
"""

import time
from typing import List


def limit_processed_logs(
        log_ids: List[int],
        max_count: int = 1000
) -> List[int]:
    """
    Limit the number of processed log IDs to prevent excessive memory usage.
    Keeps the most recent logs.
    
    Args:
        log_ids: List of log IDs
        max_count: Maximum number of logs to keep
        
    Returns:
        Trimmed list of log IDs
    """
    if len(log_ids) <= max_count:
        return log_ids
    
    # Sort by recency (assuming higher IDs are more recent)
    sorted_ids = sorted(log_ids, reverse=True)
    
    # Keep the most recent logs
    return sorted_ids[:max_count]


def get_current_timestamp() -> int:
    """
    Get the current Unix timestamp.
    
    Returns:
        Current time as Unix timestamp (seconds since epoch)
    """
    return int(time.time()) 