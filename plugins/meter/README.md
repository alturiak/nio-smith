Plugin: meter
===
Plugin to provide a simple, randomized meter

## Commands

### meter
Usage: `meter <target> <condition>`  
Make the bot respond with a meter from 0 to 10, gauging the target's condition-ness.

Example: measure alturiak's competence
`meter alturiak competent`

## Configuration

This plugin allows configuration in `meter.yaml`:

- `room_list`: Optional list of rooms to enable meter on. Active on all rooms by default.
- `special_targets`: Optional list of targets that trigger level 11.
- `special_conditions`: Optiona list of conditions that trigger level 11.

## External Requirements
- none