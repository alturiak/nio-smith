Plugin: federation_status
===
Checks federation-status of all connected homeservers and posts alerts if they become unreachable or get back online.

## Commands

### federation_status
Usage: `federation_status [homeserver or username]`  
Display the current federation status of a given homeserver or the homeserver of a given username.

## Configuration
This plugin allows configuration in `federation_status.yaml`:
- `room_list`: Optional list of rooms to enable federation_status on. Active on all rooms by default.
- `warn_cert_expiry`: (future use) Optional warn time in days before a federating server's cert expires (default: 7)
- `server_max_age`: Optional maximum age of a server's data in minutes before checking again (default: 60)
- `federation_tester_url`: Optional url of [federation-tester](https://github.com/matrix-org/matrix-federation-tester)

## External Requirements
- none