# Dependency Booster Configuration

This add-on allows you to automatically boost (reschedule) vocabulary cards that are dependencies of failed sentence cards.

## Settings

- **maturity_threshold**: Number of days since a card was new before it's considered "mature". Default: 21 days.
- **detection_method**: Method used to identify dependencies between cards. Currently only "tags" is supported.
- **processed_revlogs**: Now stored in a separate file to keep the config clean.
- **last_boost_time**: Timestamp of the last time dependencies were boosted.
- **days_to_check**: Number of days to look back for failed sentence cards. Default: 7 days.
- **auto_boost_enabled**: When set to true, automatically runs the dependency booster at the end of a review session. Default: false.

## Tagging System

For the tag-based detection method, you need to:
1. Tag vocabulary cards with `type:vocab` and `group:sX` (where X is a number).
2. Tag sentence cards with `type:sentence` and `group:sX` (with matching group numbers).

When a sentence card fails, all mature vocabulary cards with matching group tags will be rescheduled for tomorrow. 