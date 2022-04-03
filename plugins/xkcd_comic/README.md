Plugin: xkcd_comic
===
Post an xkcd-comic as image or url. Use the most recent by default, or a specific one if an ID is given.  
If `room_list` is configured, the plugin will check for new comics every hour and post a notification to each room, 
if a new comic is available.  

## Commands

### xkcd
Usage: `xkcd [id]`  
Post the most recent xkcd-comic. If id is given, post the specified one.

## Configuration
`xkcd_comic.yaml`:
- `url_only`: if true, do not post an actual image but the url instead (make use of clients' url-preview features) 
  (default: False)
- `notification_only`: if true, posts a notification about a newly released comic, instead of directly posting it 
  (default: True)
- `room_list`: List of rooms to post a notification about a new xkcd-comic to

## External Requirements
- [xkcd](https://pypi.org/project/xkcd/)
