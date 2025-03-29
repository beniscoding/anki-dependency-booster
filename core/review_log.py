"""
Module for processing Anki review logs to find failed sentence cards.
"""

import time
from typing import List, Dict, Any, Set
from aqt import mw


def get_recent_review_logs(days: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch recent review logs from the Anki database, filtered by date.
    
    Args:
        days: Number of days to look back
        
    Returns:
        List of review log dictionaries
    """
    if not mw or not mw.col:
        return []
    
    # Calculate timestamp from days ago
    cutoff_time = int((time.time() - (days * 86400)) * 1000)  # Convert to Anki's millisecond timestamp
    
    # Query the Anki database for review logs since the cutoff date
    query = """
    SELECT id, cid, ease, type 
    FROM revlog 
    WHERE id >= ?
    ORDER BY id DESC
    """
    result = mw.col.db.all(query, cutoff_time)
    
    logs = []
    for log_id, card_id, ease, review_type in result:
        logs.append({
            "id": log_id,
            "card_id": card_id,
            "ease": ease,  # 1 = fail, 2-4 = pass with varying ease
            "type": review_type
        })
    
    return logs


def find_failed_sentence_cards(
        logs: List[Dict[str, Any]],
        processed_ids: Set[int]
) -> List[int]:
    """
    Filter review logs for failed sentence cards.
    
    Args:
        logs: List of review log entries
        processed_ids: Set of review IDs that have already been processed
        
    Returns:
        List of card IDs for failed sentence cards
    """
    failed_cards = []
    
    for log in logs:
        # Skip already processed review logs
        if log["id"] in processed_ids:
            continue
        
        # Check if the review was a failure (ease = 1)
        if log["ease"] != 1:
            continue
        
        try:
            # Get the card from the database
            card = mw.col.get_card(log["card_id"])
            if not card:
                continue
            
            # Get the note for this card
            note = card.note()
            
            # Check if it's a sentence card
            tags = note.tags
            if "type:sentence" in tags:
                failed_cards.append(log["card_id"])
        except Exception:
            # Card might have been deleted or database inconsistency
            continue
            
    return failed_cards 