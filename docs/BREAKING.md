## Current
### v0.0.6 (not released yet but already on master)
#### Expandable messages
The optional arguments for
- `Plugin.send_messae()`
- `Plugin.respond_message()`

have changed.  
`expanded_mesage` has been added as a new optional argument, moving optional argument `delay` by one 
  position. It is recommended to always use optional arguments explicitly, e.g. `plugin.respond_message(command, 
  "short text", expanded_message="long text", delay=200)`

## Upcoming
### Simplify plugins-interface
Method naming, required parameters and return values are inconsistent between methods of the Plugin-class. Internal 
methods should not be visible to plugins.  
This change is currently targeted for [v0.1.0](https://github.com/alturiak/nio-smith/milestone/3).  
Ideas:  
- argument checking and parsing of commands by plugin-interface, not plugins itself
- methods could accept either client or command as argument

## Past
### v0.0.3
With release [v0.0.3](https://github.com/alturiak/nio-smith/releases/tag/v0.0.3), all included plugins are being 
moved to directories. Stored data will automatically be moved over if the bot has been run with
[v0.0.2](https://github.com/alturiak/nio-smith/releases/tag/v0.0.2) at least once.  
If you notice missing data after upgrading, make sure to check out
[v0.0.2](https://github.com/alturiak/nio-smith/releases/tag/v0.0.2) and run it once, before updating to
[v0.0.3](https://github.com/alturiak/nio-smith/releases/tag/v0.0.3) again.

### v0.0.2
With Release [v0.0.2](https://github.com/alturiak/nio-smith/releases/tag/v0.0.2), the backend to store plugin data has 
changed from pickle files to json. 
- Please make sure you have `jsonpickle` installed (update requirements, e.g. `pip install -r requirements.txt`).
- One limitation of the new storage format is that you will not be able to store `Dict`s that use `int` as key since 
they will be loaded as `str` from now on. The old `.pkl`-file will be preserved. Please make sure, your plugins work 
with the new storage-backend before deleting it. 
  
### v0.0.1
This release has been replaced by v0.0.2.