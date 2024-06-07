Plugin: songwhip
===
Once enabled in a room, automatically posts a songwhip link whenever a link to a supported music platform is detected.  
allowed_domains and patterns "borrowed" from https://github.com/maubot/songwhip

## Commands

### songwhip

Usage: `songwhip`  
Enable/disable automatic songwhip links

## Configuration

This plugin requires configuration in `songwhip.yaml` (copy `songwhip.sample.yaml` for a working example):

- `allowed_domains`: Mandatory list of allowed domains referencing their respective url-pattern
- `patterns`: Mandatory list of patterns referenced by allowed_domains
- `allowed_rooms`: List of room-id the plugin is allowed to work in (if empty, all rooms are allowed)

## External Requirements

- [yarl](https://pypi.org/project/yarl/) for the `URL`-object
- [urlextract](https://pypi.org/project/urlextract/) for extracting valid URLs from messages
- [requests](https://pypi.org/project/requests/) to query songwhip's API

allowed_domains and patterns "borrowed" from: https://github.com/maubot/songwhip