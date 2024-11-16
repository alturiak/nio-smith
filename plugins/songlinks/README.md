Plugin: songlinks
===
Once enabled in a room, automatically posts a songlink whenever a link to a supported music platform is detected.  
allowed_domains and patterns "borrowed" from https://github.com/maubot/songwhip.
This plugin currently uses https://song.link (https://odesli.co/) which is currently not handing out new API-keys.
However, the service is usable without an API-key, but limited to 10 requests per minute. This should probably be fine
for most use cases.

## Commands

### songlinks

Usage: `songlinks`  
Enable/disable automatic songlinks

## Configuration

This plugin requires configuration in `songlinks.yaml` (copy `songlinks.sample.yaml` for a working example):

- `allowed_domains`: Mandatory list of allowed domains referencing their respective url-pattern
- `patterns`: Mandatory list of patterns referenced by allowed_domains
- `allowed_rooms`: List of room-id the plugin is allowed to work in (if empty, all rooms are allowed)

## External Requirements

- [yarl](https://pypi.org/project/yarl/) for the `URL`-object
- [urlextract](https://pypi.org/project/urlextract/) for extracting valid URLs from messages
- [requests](https://pypi.org/project/requests/) to query song.link's API
