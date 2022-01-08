Plugin: xkcd_comic
===
Post an xkcd-comic as image or url. Use the most recent by default, or a specific one if an ID is given.  

## Commands

### xkcd
Usage: `xkcd [id]`  
Post the most recent xkcd-comic. If id is given, post the specified one.

## Configuration
`xkcd_comic.yaml`:
- `url_only`: if true, do not post an actual image but the url instead (make use of clients' url-preview features)

## External Requirements
- [xkcd](https://pypi.org/project/xkcd/)
