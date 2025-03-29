# Dependency Booster for Anki

An Anki add-on that automatically reschedules vocabulary cards that are dependencies of failed sentence cards.

## Purpose

When learning a language, you often study both vocabulary cards and sentence cards. Sometimes, you may fail to remember a sentence because you've forgotten a specific vocabulary word. This add-on helps by automatically identifying those vocabulary dependencies and rescheduling them for review when you fail a sentence card.

## How It Works

1. When you fail a sentence card during review, the add-on checks for vocabulary cards that are dependencies of that sentence.
2. If any dependent vocabulary cards are found and considered "mature" (default: 21+ days old), they will be rescheduled to appear in tomorrow's review.
3. This ensures that you review the foundation vocabulary before seeing the sentence again.

## Installation

### Method 1: Manual Installation

1. Download the latest release zip file from [GitHub Releases](https://github.com/beniscoding/anki-dependency-booster/releases)
2. In Anki, go to Tools → Add-ons → Install from file...
3. Select the downloaded zip file

### Method 2: AnkiWeb (Coming Soon)

Will be available on AnkiWeb after initial testing.

## Usage

### Card Tagging

For the tag-based detection (current implementation):

1. Tag vocabulary cards with `type:vocab` and `group:sX` (where X is a number)
2. Tag sentence cards with `type:sentence` and `group:sX` (with matching group numbers)

For example, if a vocabulary card for "apple" is tagged with `group:s1`, and a sentence using that word is also tagged with `group:s1`, failing the sentence card will cause the "apple" card to be boosted if it's mature.

### Manual Boosting

Go to Tools → Dependency Booster → Boost Dependencies to manually trigger the dependency boosting process.

### Automatic Boosting

The add-on can automatically boost dependencies when you complete a review session:

1. Enable the feature via Tools → Dependency Booster → Enable Auto-Boost After Review 
   (or through the Settings dialog)
2. After you exit a review session, any failed sentence cards will have their vocabulary dependencies rescheduled
3. You'll see a notification when this process completes

### AnkiDroid Compatibility

While this add-on only runs on desktop Anki, we've included a special feature for AnkiDroid users:

1. Review your cards on AnkiDroid as usual
2. When you're back at your desktop, open Anki
3. Go to Tools → Dependency Booster → Sync & Boost AnkiDroid Reviews
4. This will:
   - Sync with AnkiWeb to get your latest AnkiDroid reviews
   - Process any failed sentence cards
   - Reschedule the vocabulary dependencies
   - Sync back to AnkiWeb so your changes appear on AnkiDroid

## Configuration

### Settings Dialog

Access the settings by going to Tools → Dependency Booster → Settings. The dialog allows you to:

- Adjust the minimum card age (how many days old a card must be before it's considered for boosting)
- Set how many days back to look for failed sentence cards (default: 7 days)
- Enable/disable automatic boosting
- Clear processed review history

### Advanced Configuration

The add-on's configuration can also be modified directly through Anki's add-on configuration screen:

1. Go to Tools → Add-ons
2. Select "Dependency Booster"
3. Click "Config"

Available settings include:

- `maturity_threshold`: Days before a card is considered "mature" (default: 21)
- `detection_method`: How dependencies are identified (currently only tag-based)
- `days_to_check`: Number of days to look back for failed cards (default: 7)
- `auto_boost_enabled`: Whether to automatically boost after exiting review

## License

MIT License