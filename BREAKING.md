## Current: v0.0.2
With Release [v0.0.2](https://github.com/alturiak/nio-smith/releases/tag/v0.0.2), the backend to store plugin data has 
changed from pickle files to json. 
- Please make sure you have `jsonpickle` installed (update requirements, e.g. `pip install -r requirements.txt`).
- One limitation of the new storage format is that you will not be able to store `Dict`s that use `int` as key since 
they will be loaded as `str` from now on. The old `.pkl`-file will be preserved. Please make sure, your plugins work 
with the new storage-backend before deleting it. 

## Upcoming
### Move plugins to a separate repository
Plugins will be moved to a directory-based structure soon, e.g. `plugins/sample/sample.py` instead of 
`plugins/sample.py` and will live in their own repository afterwards.  
The bot must have run at least once with [v0.0.1](https://github.com/alturiak/nio-smith/commit/ffc6acb07125c8b3324b2cf237fa5905686fff5c) or newer before migrating plugins to their 
directories.

### Simplify plugins-interface
Method naming, required parameters and return values are inconsistent between methods of the Plugin-class. Internal 
methods should not be visible to plugins.  
This change is currently targeted for v0.1.0.  
Ideas:  
- argument checking and parsing of commands by plugin-interface, not plugins itself
- methods could accept either client or command as argument

## Past
### v0.0.1
This release has been replaced by v0.0.2.