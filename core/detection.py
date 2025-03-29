"""
Module for detecting dependencies between sentence and vocabulary cards.
"""

from typing import List, Set
from aqt import mw


def extract_group_tags(tags: List[str]) -> Set[str]:
    """
    Extract group tags (group:sX) from a list of tags.
    
    Args:
        tags: List of tags
        
    Returns:
        Set of group tag values (e.g., {'s1', 's2'})
    """
    group_tags = set()
    
    for tag in tags:
        if tag.startswith("group:s"):
            # Extract the part after "group:s"
            group_id = tag[7:]
            group_tags.add(group_id)
            
    return group_tags


def find_vocabulary_dependencies(
        card_id: int, 
        maturity_threshold: int = 21
) -> List[int]:
    """
    Find mature vocabulary cards that are dependencies of the given card.
    
    Args:
        card_id: ID of the sentence card to find dependencies for
        maturity_threshold: Minimum days since creation to be considered mature
        
    Returns:
        List of card IDs for vocabulary dependencies
    """
    if not mw or not mw.col:
        return []
    
    # Get the sentence card
    sentence_card = mw.col.get_card(card_id)
    if not sentence_card:
        return []
    
    # Get the note
    sentence_note = sentence_card.note()
    
    # Extract group tags
    group_tags = extract_group_tags(sentence_note.tags)
    if not group_tags:
        return []
    
    # Build a query to find vocabulary cards with matching group tags
    group_conditions = []
    for group in group_tags:
        tag_name = f"group:s{group}"
        group_conditions.append(f"n.tags LIKE '%{tag_name}%'")
    
    group_clause = " OR ".join(group_conditions)
    
    # Query for vocabulary cards with matching group tags
    query = f"""
    SELECT c.id
    FROM cards c
    JOIN notes n ON c.nid = n.id
    WHERE 
        n.tags LIKE '%type:vocab%'
        AND ({group_clause})
    """
    
    result = mw.col.db.list(query)
    
    # Filter for mature cards
    mature_vocab_cards = []
    for card_id in result:
        card = mw.col.get_card(card_id)
        if card and is_card_mature(card, maturity_threshold):
            mature_vocab_cards.append(card_id)
    
    return mature_vocab_cards


def is_card_mature(card, threshold: int) -> bool:
    """
    Check if a card is considered mature based on its interval.
    
    Args:
        card: Anki card object
        threshold: Minimum days to be considered mature
        
    Returns:
        True if the card is mature, False otherwise
    """
    # Card is mature if its interval is at least the threshold
    return card.ivl >= threshold 