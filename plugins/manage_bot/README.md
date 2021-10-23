Plugin: manage_bot
===
Various commands to manage the bot interactively.

## Commands

### bot_rooms_list
Usage: `bot_room_list`  
Display a list of all rooms the bot is in, including their name, room_id and member count.

### bot_rooms_cleanup
Usage: `bot_rooms_cleanup`
Make the bot leave all rooms in which it is the only member.  
**Warning**: This might permanently render invite-only rooms inaccessible, as nobody is left within the room to invite 
anyone.

## Configuration
This plugin requires configuration in `manage_bot.yaml`:  
- `manage_bot_rooms`: Mandatory list of room-ids the plugin will accept commands on (Default: none)
- `manage_bot_power_level`: Optional minimum power level required to issue commands (Default: 100)

## External Requirements
- none