Plugin: sonarr
===
Provides commands to query sonarr's V3 API. Posts expected episodes for the coming week and keeps posting updated with
the current status.  
Optionally posts changes to tracked series, e.g. information about a new season or state of the series 
(Continuing/Ended).  

## Commands

### series
Usage: `series`  
Display a list of all tracked series.

### episodes
Usage: `episodes`  
Recreate the weekly posting with the current status of tracked episodes.

## Configuration
This plugin requires configuration in `sonarr.yaml`:  
- `room_id`: mandatory room the plugin is active (allowing commands and posting series information), only one room 
  supported 
- `api_base`: mandatory url of sonarr's API, e.g. `http://localhost:8989/api/v3`
- `api_key`: mandatory api key to use for connecting to sonarr's api, as configured via Settings -> API Key 
- `series_tracking`: optional setting to enable/disable tracking changes to series tracked by sonarr  

## External Requirements
  - [requests](https://pypi.org/project/requests/) to query sonarr's API
  - [humanize](https://pypi.org/project/humanize/)


