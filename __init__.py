"""
Dependency Booster Add-on for Anki
===================================

This add-on automatically reschedules vocabulary cards when their
related sentence cards are failed during review.

GitHub: https://github.com/ankisrs/dependency_booster
"""

import os
import json
from aqt import mw
from aqt.qt import QAction, QMenu, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from aqt.qt import QSpinBox, QCheckBox, QMessageBox, QTimer
from aqt.utils import tooltip, showInfo
from anki.hooks import addHook
from typing import Dict, Any, Set

from .core.review_log import get_recent_review_logs, find_failed_sentence_cards
from .core.detection import find_vocabulary_dependencies
from .core.reschedule import (
    reschedule_cards_for_tomorrow,
    show_rescheduling_results
)


def get_addon_dir() -> str:
    """Get the add-on directory path"""
    return os.path.dirname(os.path.abspath(__file__))


def get_config() -> Dict[str, Any]:
    """Load the add-on configuration from config.json"""
    return mw.addonManager.getConfig(__name__) or {}


def save_config(config: Dict[str, Any]) -> None:
    """Save the configuration to disk"""
    # Ensure processed_revlogs is not stored in the main config
    if "processed_revlogs" in config:
        del config["processed_revlogs"]
    mw.addonManager.writeConfig(__name__, config)


def get_processed_revlogs() -> Set[int]:
    """
    Get the set of processed review log IDs from a separate file.
    This prevents the main config from becoming too large.
    """
    logs_path = os.path.join(get_addon_dir(), "processed_revlogs.json")
    if os.path.exists(logs_path):
        try:
            with open(logs_path, "r") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_processed_revlogs(logs: Set[int]) -> None:
    """Save the processed review log IDs to a separate file"""
    logs_path = os.path.join(get_addon_dir(), "processed_revlogs.json")
    try:
        with open(logs_path, "w") as f:
            json.dump(list(logs), f)
    except IOError as e:
        showInfo(f"Error saving processed review logs: {str(e)}")


def clear_processed_revlogs() -> None:
    """Clear all processed review logs"""
    logs_path = os.path.join(get_addon_dir(), "processed_revlogs.json")
    if os.path.exists(logs_path):
        try:
            os.remove(logs_path)
        except IOError as e:
            showInfo(f"Error clearing processed review logs: {str(e)}")


# Core Functionality
####################

def process_failed_reviews() -> None:
    """Check for failed sentence cards and boost dependencies"""
    config = get_config()
    
    # Get configuration values
    maturity_threshold = config.get("maturity_threshold", 21)
    days = config.get("days_to_check", 7)
    processed_revlogs = get_processed_revlogs()
    
    # Always use days-based filtering (simpler and more intuitive)
    logs = get_recent_review_logs(days=days)
    
    # Find failed sentence cards
    failed_cards = find_failed_sentence_cards(logs, processed_revlogs)
    
    # Track which review logs we've processed
    newly_processed = set()
    for log in logs:
        newly_processed.add(log["id"])
    
    # Update processed reviews
    all_processed = processed_revlogs.union(newly_processed)
    save_processed_revlogs(all_processed)
    
    # Update last boost time in config
    config["last_boost_time"] = int(__import__("time").time())
    save_config(config)
    
    # Find vocabulary dependencies for each failed card
    all_deps = []
    for card_id in failed_cards:
        deps = find_vocabulary_dependencies(card_id, maturity_threshold)
        all_deps.extend(deps)
    
    # Deduplicate to avoid rescheduling cards multiple times
    unique_deps = list(set(all_deps))
    
    # Reschedule dependencies
    count = reschedule_cards_for_tomorrow(unique_deps)
    
    # Show results
    show_rescheduling_results(count)


def sync_and_boost() -> None:
    """
    Sync with AnkiWeb, process dependencies, and sync back.
    
    This function is designed to help users who review cards on AnkiDroid
    and want to process dependencies on desktop Anki.
    """
    # Check if collection is available
    if not mw or not mw.col:
        showInfo("Collection not available. Please try again later.")
        return
        
    # First sync to get AnkiDroid reviews
    tooltip("Starting sync with AnkiWeb...", period=5000)
    
    try:
        # Modern Anki versions use mw.onSync() to trigger sync
        mw.onSync()
        
        # Process failed reviews after sync completes
        tooltip("Sync completed. Processing dependencies...", period=3000)
        process_failed_reviews()
        
        # Sync back to AnkiWeb
        tooltip("Boosting complete. Syncing changes back to AnkiWeb...", period=5000)
        mw.onSync()
        
        showInfo("Sync and boost process complete! Your changes have been synced back to AnkiWeb.")
    except Exception as e:
        showInfo(f"Error during sync and boost: {str(e)}")


# UI Integration
################

def on_boost_dependencies() -> None:
    """Menu action handler to manually trigger dependency boosting"""
    process_failed_reviews()


# Track the previous state to detect when exiting review
prev_state = None


def on_state_change(new_state, old_state, *args):
    """
    Monitor state changes to detect when user completely exits the review session.
    This is safer than trying to detect end-of-cards while still in the review interface.
    """
    global prev_state
    
    # If we're leaving the review state
    if old_state == "review" and new_state != "review":
        config = get_config()
        if config.get("auto_boost_enabled", False):
            # Add a small delay to ensure all data is properly saved
            tooltip("Review complete. Processing dependencies...", period=3000)
            QTimer.singleShot(1000, process_failed_reviews)
    
    prev_state = new_state


def toggle_auto_boost():
    """Toggle automatic boosting after review sessions"""
    config = get_config()
    config["auto_boost_enabled"] = auto_boost_action.isChecked()
    save_config(config)
    tooltip(f"Auto-boost {'enabled' if auto_boost_action.isChecked() else 'disabled'}")


# Settings Dialog
################

class SettingsDialog(QDialog):
    """Dialog for adjusting add-on configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dependency Booster Settings")
        self.setMinimumWidth(450)  # Wider to accommodate help text
        self.config = get_config()
        
        # Check if this is the first time opening settings
        self.is_first_use = not self.config.get("settings_viewed", False)
        self.config["settings_viewed"] = True
        save_config(self.config)
        
        self.initUI()
        
        # Show welcome guide on first use
        if self.is_first_use:
            self.show_welcome_guide()
    
    def create_help_label(self, text):
        """Create a small help label with explanatory text"""
        label = QLabel(text)
        label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        label.setWordWrap(True)
        return label
    
    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # === SECTION: CARD ELIGIBILITY ===
        section_label = QLabel("<b>Card Eligibility</b>")
        layout.addWidget(section_label)
        
        # Maturity threshold setting
        maturity_layout = QHBoxLayout()
        maturity_label = QLabel("Minimum card age (days):")
        self.maturity_spinner = QSpinBox()
        self.maturity_spinner.setMinimum(1)
        self.maturity_spinner.setMaximum(365)
        self.maturity_spinner.setValue(self.config.get("maturity_threshold", 21))
        maturity_layout.addWidget(maturity_label)
        maturity_layout.addWidget(self.maturity_spinner)
        layout.addLayout(maturity_layout)
        
        # Help text for maturity
        maturity_help = self.create_help_label(
            "Only reschedule vocabulary cards that are at least this many days old. "
            "New cards are excluded to avoid disrupting your learning schedule."
        )
        layout.addWidget(maturity_help)
        
        layout.addSpacing(10)
        
        # === SECTION: REVIEW HISTORY ===
        section_label = QLabel("<b>Review History</b>")
        layout.addWidget(section_label)
        
        history_help = self.create_help_label(
            "Control how far back to look for failed sentence cards."
        )
        layout.addWidget(history_help)
        
        # Days to check setting
        days_layout = QHBoxLayout()
        days_label = QLabel("Days to check:")
        self.days_spinner = QSpinBox()
        self.days_spinner.setMinimum(1)
        self.days_spinner.setMaximum(365)
        self.days_spinner.setValue(self.config.get("days_to_check", 7))
        days_layout.addWidget(days_label)
        days_layout.addWidget(self.days_spinner)
        layout.addLayout(days_layout)
        
        # Help text for days
        days_help = self.create_help_label(
            "Example: 7 days = all reviews from the past week"
        )
        layout.addWidget(days_help)
        
        layout.addSpacing(10)
        
        # === SECTION: AUTOMATION ===
        section_label = QLabel("<b>Automation</b>")
        layout.addWidget(section_label)
        
        # Auto-boost setting
        self.auto_boost_checkbox = QCheckBox("Automatically boost after review sessions")
        self.auto_boost_checkbox.setChecked(self.config.get("auto_boost_enabled", False))
        layout.addWidget(self.auto_boost_checkbox)
        
        # Help text for auto-boost
        auto_help = self.create_help_label(
            "When enabled, vocabulary dependencies will be rescheduled automatically "
            "after you finish a review session containing failed sentence cards."
        )
        layout.addWidget(auto_help)
        
        layout.addSpacing(10)
        
        # === SECTION: MAINTENANCE ===
        section_label = QLabel("<b>Maintenance</b>")
        layout.addWidget(section_label)
        
        # Clear history button
        clear_button = QPushButton("Clear Processed Review History")
        clear_button.clicked.connect(self.clearHistory)
        layout.addWidget(clear_button)
        
        # Help text for clear button
        clear_help = self.create_help_label(
            "Clears the record of which reviews have already been processed. "
            "Use this if you want to reprocess old reviews."
        )
        layout.addWidget(clear_help)
        
        # Review history stats
        logs_count = len(get_processed_revlogs())
        history_label = QLabel(f"Processed reviews: {logs_count}")
        layout.addWidget(history_label)
        
        layout.addSpacing(10)
        
        # Dialog buttons
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
    
    def show_welcome_guide(self):
        """Show a welcome guide for first-time users"""
        welcome_text = (
            "<h3>Welcome to Dependency Booster!</h3>"
            "<p>This add-on helps you review vocabulary words that you're struggling with in sentences.</p>"
            "<p><b>Quick setup:</b></p>"
            "<ol>"
            "<li>Tag your vocabulary cards with <code>type:vocab</code> and <code>group:s1</code> (where 1 is any number)</li>"
            "<li>Tag your sentence cards with <code>type:sentence</code> and matching <code>group:s1</code> tags</li>"
            "<li>When you fail a sentence, the add-on will automatically reschedule its vocabulary words</li>"
            "</ol>"
            "<p>The default settings work well for most users. Just enable auto-boost if you want the process to happen automatically.</p>"
        )
        
        QMessageBox.information(self, "Welcome to Dependency Booster", welcome_text)
    
    def clearHistory(self):
        """Clear the processed review history"""
        reply = QMessageBox.question(
            self, 
            "Clear History",
            "Are you sure you want to clear the processed review history? "
            "This will allow vocabulary cards to be boosted again when you next run the dependency booster.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            clear_processed_revlogs()
            tooltip("Review history cleared")
    
    def accept(self):
        """Save changes and close dialog"""
        self.config["maturity_threshold"] = self.maturity_spinner.value()
        self.config["days_to_check"] = self.days_spinner.value() 
        self.config["auto_boost_enabled"] = self.auto_boost_checkbox.isChecked()
        save_config(self.config)
        
        # Update menu item checked state
        auto_boost_action.setChecked(self.auto_boost_checkbox.isChecked())
        
        super().accept()


def show_settings():
    """Display the settings dialog"""
    dialog = SettingsDialog(mw)
    dialog.exec()


# Setup
#######

# Create a submenu for the add-on
dependency_menu = QMenu("Dependency Booster", mw)
mw.form.menuTools.addMenu(dependency_menu)

# Add items to the submenu
boost_action = QAction("Boost Dependencies", mw)
boost_action.triggered.connect(on_boost_dependencies)
dependency_menu.addAction(boost_action)

sync_action = QAction("Sync & Boost AnkiDroid Reviews", mw)
sync_action.triggered.connect(sync_and_boost)
dependency_menu.addAction(sync_action)

# Add auto-boost toggle to menu
auto_boost_action = QAction("Enable Auto-Boost After Review", mw)
auto_boost_action.setCheckable(True)
auto_boost_action.setChecked(get_config().get("auto_boost_enabled", False))
auto_boost_action.triggered.connect(toggle_auto_boost)
dependency_menu.addSeparator()
dependency_menu.addAction(auto_boost_action)

# Add settings dialog
settings_action = QAction("Settings", mw)
settings_action.triggered.connect(show_settings)
dependency_menu.addAction(settings_action)

# Register state change hook instead of card answer hook
addHook("afterStateChange", on_state_change) 