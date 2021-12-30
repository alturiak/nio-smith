Plugin: quote
===
Store conversations as quotes to be displayed later.  
**Attention**: Quotes are currently bot-global, e.g. accessible from *any* room the bot is in. This allows for 
circumventing power level restrictions of privileged commands. It is recommended to configure `manage_quote_rooms` to 
prevent this.

## Commands
### quote
Post quotes, either randomly, by id, or by search string  
Usage: `quote [id|search string [match]]`  

Example: post a random quote:  
`quote`

Example: post quote 1:  
`quote 1`

Example: post one of the quotes containing the word "test", displaying the number of matching quotes:  
`quote test`

Example: post the second quote containing the word "test":  
`quote test 2`


### quote_add
Add a quote, using either matrix- or irc-style formatting.  
Usage: `quote_add <text of the quote>`

Example: add a quote using irc-style (all in one line, use ` | ` for line breaks):
`quote_add <Sheldon> Do you know what's interesting about caves, Leonard? | 
<Leonard> What? | <Sheldon> Nothing!`

Example: add a quote using matrix-style (separate lines, but all in one message, allows for c&p'ing from matrix 
clients):  
`quote_add Sheldon`  
`Do you know what's interesting about caves, Leonard?`  
`Leonard`  
`What?`  
`Sheldon`  
`Nothing!`  

Example: add a quote using matrix-style with annotations:  
`quote_add [Leonard and Sheldong walking down the stairs of their building]`  
`Sheldon`    
`Do you know what's interesting about caves, Leonard?`    
`Leonard`  
`What?`  
`Sheldon`  
`Nothing!`  

### quote_del (Power Level: 50)
Delete (hide) a quote by id. The quote can be restored by `quote_restore`.  
Usage: `quote_del 1`

### quote_restore (Power Level: 50)
Restore (unhide) a quote by id deleted by `quote_del`.  
Usage: `quote_restore 1`

### quote_links (Power Level: 100)
Toggle automatic nickname linking. Only usable on configured rooms, if `manage_quote_rooms` is set.  
Usage: `quote_links`

### quote_replace (Power Level: 50)
Replace a specific quote with the supplied text - destructive, can not be reverted.  
See `quote_add` for accepted quote formats.  
Only usable on configured rooms, if `manage_quote_rooms` is set.  
Usage: `quote_replace <quote-id> <text of the quote>`

Example:
`quote_replace 1 [Leonard and Sheldong walking down the stairs of their building]`  
`Sheldon`    
`Do you know what's interesting about caves, Leonard?`    
`Leonard`  
`What?`  
`Sheldon`  
`Nothing!`  


### quote_replace_nick (Power Level: 50)
Replace a nickname in *ALL QUOTES* with another nickname - destructive, can not be reverted. USE WITH CAUTION!  
Only usable on configured rooms, if `manage_quote_rooms` is set.  
This creates a backup of the plugin's data before replacing the nicknames.  
By default, the bot will add an `<new_nick> as <old_nick>`-annotation to the quote to make sure the old nick is not 
lost (in case it is relevant to the content of the quote). This can be skipped with the `-s`-Switch.  
The added annotation can also be removed from the affected quotes by editing them afterwards.

Usage: `quote_replace_nick [-s] <old_nick> <new_nick>`  
(`-s` switch skips adding an annotation)

Example:
```
<user> !quote_replace_nick VooDoo-NA VooDoo
<bot> 67 occurrences of VooDoo-NA replaced by VooDoo in 46 quotes.
```


### quote_upgrade (Power Level: 100)
Upgrade all Quotes to the most recent version, only needed if there is a change in storing quotes. There will be a 
warning on startup, should this be required in the future. Only usable on configured rooms, if `manage_quote_rooms` is set.  
Usage: `quote_upgrade`

### quote_stats
Display various stats about the currently stored quotes  
Usage: `quote_stats [full]`

Example: Display short quote stats:  
`quote_stats`  

Example: Display full quote stats:  
`quote_stats full`

## Configuration
This plugin allows configuration in `quote.yaml`:
- `manage_quote_rooms`: Optional list of room-ids the plugin will allow quote-modifications on (Default: none)

## External Requirements
- none
