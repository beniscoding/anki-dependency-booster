"""
Module for rescheduling dependent vocabulary cards.
"""

from typing import List
from aqt import mw
from aqt.utils import tooltip


def reschedule_cards_for_tomorrow(card_ids: List[int]) -> int:
    """
    Reschedule cards to appear in tomorrow's review.
    
    Args:
        card_ids: List of card IDs to reschedule
        
    Returns:
        Number of cards successfully rescheduled
    """
    if not mw or not mw.col:
        return 0
    
    count = 0
    
    # Get the current deck
    deck_id = mw.col.decks.current()["id"]
    
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        if not card:
            continue
            
        # Skip cards that are already due tomorrow or sooner
        if card.queue in (2, 3) and card.due <= mw.col.sched.today + 1:
            # Card is already due today or tomorrow
            continue
            
        # Skip cards in filtered/custom decks
        if card.odid:
            continue
            
        # Reschedule to tomorrow
        try:
            # Save the original deck
            orig_did = card.did
            
            # Move to current deck temporarily if needed
            if orig_did != deck_id:
                mw.col.set_deck([card_id], deck_id)
                
            # Set due date to tomorrow (1 day from now)
            card.due = mw.col.sched.today + 1
            card.ivl = 1
            card.queue = 2  # review queue
            card.type = 2   # review type
            
            # Save changes
            card.flush()
            
            # Return to original deck if changed
            if orig_did != deck_id:
                mw.col.set_deck([card_id], orig_did)
                
            count += 1
            
        except Exception as e:
            # Log any errors but continue processing other cards
            print(f"Error rescheduling card {card_id}: {e}")
    
    # Update UI if any cards were rescheduled
    if count > 0:
        mw.col.reset()
        mw.reset()
    
    return count


def show_rescheduling_results(count: int) -> None:
    """
    Display a tooltip with the results of the rescheduling operation.
    
    Args:
        count: Number of cards rescheduled
    """
    if count == 0:
        tooltip("No vocabulary dependencies needed rescheduling")
    else:
        tooltip(f"Boosted {count} vocabulary cards for tomorrow's review") 