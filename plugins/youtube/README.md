Plugin: youtube
===
Watches for youtube links and posts video title, description, thumbnail and other various details.  
If dislikes are enabled, the sample size
(count of likes returnyoutubedislike.com has seen by plugin users compared to total count of likes is being displayed)

## Commands

### youtube

Usage: `youtube`  
Enable/disable automatic youtube link preview

## Configuration

This plugin requires configuration in `youtube.yaml`:

- `api_key`: mandatory API-Key for youtube - see https://developers.google.com/youtube/v3/getting-started
- `enable_dislikes`: optionally enable displaying dislikes (queries an additional API
  from https://returnyoutubedislike.com/)
- `allowed_rooms`: List of room-id the plugin is allowed to work in (if empty, all rooms are allowed)

## External Requirements

- [yarl](https://pypi.org/project/yarl/) for the `URL`-object
- [urlextract](https://pypi.org/project/urlextract/) for extracting valid URLs from messages
- [requests](https://pypi.org/project/requests/) to query youtube's API
- [humanize](https://pypi.org/project/humanize/) to display various details in human-readable form


