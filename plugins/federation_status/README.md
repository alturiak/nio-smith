Plugin: federation_status
===
Checks federation-status of all connected homeservers and posts alerts if they become unreachable or get back online.  
It will also post warnings to rooms if a homeserver's certificate is about to expire.

## Commands

### federation_status
Usage: `federation [global]`  
Display the current federation status and certificate expiry date of all homeservers in the room. When called with 
the otional `global` parameter, displays information about all homeservers known to the bot.

## Configuration
This plugin allows configuration in `federation_status.yaml`:
- `room_list`: Optional list of rooms to enable federation_status on. Active on all rooms by default.
- `warn_cert_expiry`: (future use) Optional warn time in days before a federating server's cert expires (default: 7)
- `server_max_age`: Optional maximum age of a server's data in minutes before checking it again (default: 60)
- `federation_tester_url`: Optional url of [federation-tester](https://github.com/matrix-org/matrix-federation-tester)

## External Requirements
- pytz