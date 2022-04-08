# Plugins
## Included Plugins
Note: automatic loading of plugins can be configured by allow- and denylist in the bot's configuration.  
- `cashup`: settle expenses among a group ([README.md](cashup/README.md)) (Contributed by [JimmyPesto](https://github.com/JimmyPesto/nio-smith))
- `coingecko`: fetch market data for crypto currencies ([README.md](coingecko/README.md)) (Contributed by [Eulentier161](https://github.com/Eulentier161))
- `dates`: stores dates and birthdays, posts reminders ([README.md](dates/README.md))
- `echo`: echoes back text following the command. ([README.md](echo/README.md))
- `federation_status`: Checks federation-status of all connected homeservers ([README.md](federation_status/README.md))
- `help`: lists all available plugins. If called with a plugin as parameter, lists all available commands ([README.md](help/README.md))
- `manage_bot`: Various commands to manage the bot interactively. ([README.md](manage_bot/README.md))
- `meter`: Plugin to provide a simple, randomized meter ([README.md](meter/README.md))
- `oracle`: predicts the inevitable future (german, sorry) ([README.md](oracle/README.md))
- `pick`: Pick a random item from a given list of items. ([README.md](pick/README.md))
- `quote`: Store conversations as quotes to be displayed later. ([README.md](quote/README.md))
- `roll`: Roll one or more dice. The trigger is 'roll'. ([README.mde](roll/README.md))
- `sample`: Collection of several sample commands to illustrate usage and maybe serve as a plugin template. ([README.md](sample/README.md))
- `sonarr`: Provides commands to query sonarr's API. ([README.md](sonarr/README.md))
- `spruch`: Posts a random quote by more or less famous persons. (german, sorry) ([README.md](spruch/README.md))
- `translate`: Provide translations of all room-messages via Google Translate ([README.md](translate/README.md))
- `wiki`: Lookup keywords in various online encyclopedias. ([README.md](wiki/README.md))
- `wissen`: Post a random or specific entry of the database of useless knowledge. (german, sorry) ([README.md](wissen/README.md))
- `xkcd_comic`: Post an xkcd-comic as image or url. ([README.md](xkcd_comic/README.md))

## Included plugins' 3rd party requirements
- `coingecko`:
  - [pycoingecko](https://pypi.org/project/pycoingecko/)
- `dates`:
  - [dateparser](https://pypi.org/project/dateparser/) to allow for almost arbitrary input format of dates
- `sonarr`:
  - [requests](https://pypi.org/project/requests/) to query sonarr's API
  - [humanize](https://pypi.org/project/humanize/)
- `translate`:
  - Python 3.9 
  - [freetranslate](https://pypi.org/project/freetranslate/) to provide language detection and translation
- `wiki`:
  - [wikipedia](https://pypi.org/project/wikipedia/) to interact with wikipedia
- `xkcd_comic`:
  - [xkcd](https://pypi.org/project/xkcd/) to retrieve xkcd-comics

## Plugins can
- ✔ use (almost) arbitrary python-code
- ✔ be supplied
  - inside their own directory (e.g. `plugins/sample/sample.py`) (encouraged since [v0.0.2](https://github.com/alturiak/nio-smith/releases/tag/v0.0.2))
  - as a single file (e.g. `plugins/sample.py`) (deprecated with [v0.1.0](https://github.com/alturiak/nio-smith/releases/tag/v0.1.0))
- ✔ send room-messages
- ✔ replace (edit) their sent messages
- ✔ hook into to received room-messages
- ✔ send reactions to specific messages
- ✔ hook into to received reactions
- ✔ add multiple commands (with required power levels) 
- ✔ limit commands to certain rooms
- ✔ use built-in persistent storage
- ✔ request creation of a backup of the currently stored plugin data
- ✔ automatically be supplied with config-values from plugin-specific config-files at startup
- ✔ register timers for method execution at custom intervals or at the start of each:
    - week,
    - day or
    - hour
- ❌ not hook into other room-events (yet)

## Plugins must
- ✔ use async
- ✔ instantiate `core.plugin.Plugin` as `plugin`
- ✔ be uniquely named and use this name as
  - directory-name (`plugins/sample/`)
  - file-name (`plugins/sample/sample.py`)
  - plugin-name when instantiating `Plugin`: `plugin = Plugin("sample", "General", "Just a simple sample.")`
- ❌ not use `time.sleep()` - please use `asyncio.sleep()` instead

## Plugins should
- ✔ handle exceptions themselves (they will eventually be caught by the bot, but will produce error logs)
- ✔ use [type hints](https://docs.python.org/3/library/typing.html)
- ✔ adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) (except for
[maximum-line-length](https://www.python.org/dev/peps/pep-0008/#maximum-line-length) - anything up to 160 is fine by
 me)
- ✔ be formatted with `black -l 160` (See [black](https://pypi.org/project/black/) for details)
- ✔ contain a README.md in their directory for a detailed description about
    - their intended use,
    - usage of commands and
    - additional requirements.

## Plugin file structure
- 📂 `plugins/<pluginname>/`: folder holding anything related to the plugin  
  - `<pluginname>.py`: the actual python code of the plugin
  - `<pluginname>.yaml`: optional configuration file of the plugin
  - `<pluginname>.sample.yaml`: optional sample configuration file of the plugin
  - `<pluginname>.json`: (autogenerated) file to store any data stored by `store_data`
  - `<pluginname>.json.bak.<timestamp>`: backup-file created by calling `backup_data` - NO automatic backups as of now
  - `<pluginname>_state.json`: (autogenerated) current state of the plugin, used to store e.g. dynamic timers
  - `README.md`: optional documentation of the plugin  
  - `requirements.txt`: external modules required by the plugin

Additional files may be placed in the plugin's directory (e.g. an external database queried by the plugin's code).

## Plugin Interface
The class `Plugin` is used by all plugins, providing the following methods. See 
[sample.py](sample/sample.py) for examples.  
Please be advised that the plugin interface is about to
[change](https://github.com/alturiak/nio-smith/blob/master/BREAKING.md#simplify-plugins-interface) in future releases.

### Commands
- `add_command`: define
    - a command word,
    - the method called when the command is encountered,
    - a short helptext and
    - an optional list of rooms the command is valid for
- `del_command`: remove a previously added command (only if command_type=="dynamic")

### Interactions
#### Messages
- `replace_message`: replace (edit) a previously sent message
- `replace_notice`: replace (edit) a previously sent notice
- `respond_message`: respond to a command with a message
- `respond_notice`: respond to a command with a notice (also called "bot message")
- `send_message`: send a message to a room
- `send_notice`: send a notice (also called "bot message") to a room

#### Reactions
- `send_reaction`: react to a specific event

#### Deletion
- `redact_event`: Redact (delete) an event (e.g. a message, notice or reaction)

#### Other
- `get_mx_user_id`: given a displayname and a command, returns a mx user id
- `is_user_in_room`: checks if a given displayname is a member of the current room
- `is_user_id_in_room`: checks if a given userid is a member of the current room
- `link_user`: given a displayname, returns a link to the user (rendered as userpill in [Element](https://element.io))
- `link_user_by_id`: given a userid, returns a link to the user (rendered as userpill in [Element](https://element.io))
- `get_connected_servers`: Get a list of connected servers for a list of rooms. Returns all connected servers if room_id_list is empty.
- `get_rooms_for_server`: Get a list of rooms the bot shares with users of the given server.
- `get_users_on_servers`: Get a list of users on a specific homeserver in a list of rooms. Returns all known users if room_id_list is empty.

### Data persistence
- `store_data`: persistently store data for later use
- `read_data`: read data from store
- `clear_data`: clear stored data
- `backup_data`: create a backup copy of the currently stored plugin data in `<pluginnname>.json.bak.<timestamp>` 

### Configuration
- `add_config`: define
    - a config_item to look for in `<plugin_name>.yaml`
    - an optional default_value
    - if the value is required (must be in configuration or have a default value)
- `read_config`: read a config_item, either returning the value found in the configuration file or the default_value,
  if supplied

### Hooks
- `add_hook`: define
    - an event type to be hooked into
        - "m.room.message": normal text messages sent to rooms
        - "m.reaction": reactions to room messages
    - the method called when the event is encountered,
    - an optional list of rooms the hook is valid for
- `del_hook`: remove a previously added hook (only if hook_type=="dynamic")

### Timers
- `add_timer`: define
    - the method to be called (currently once every ~30s whenever a sync event is received)
    - the frequency, in which the method is to be called, either as
        - datetime.timedelta or
        - str: "weekly", "daily", "hourly"
- `del_timer`: remove a previously added timer (only if `timer_type=="dynamic"`)
- `has_timer_for_method`: check if a timer for the given method exists

## Configuration
Plugins can read additional configuration options from the file `plugins/<pluginname>/<pluginname>.yaml`.  
Any configuration item that is to be used within the plugin has to be defined by `add_config()` first. It's value can 
then be read at anytime by calling `read_config()`. See [sample.py](sample/sample.py) for examples.  

## Documentation URL for each individual plugin
If present in `<pluginname>.yaml`, the configuration item `doc_url` will automatically be read and used by the 
output of `help`. This happens internally, so there is no need to define `add_config("doc_url")` in the actual 
plugin code.
