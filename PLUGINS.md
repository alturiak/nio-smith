# Plugins
## Included Plugins
- `dates`: Stores dates and birthdays, posts reminders ([README.md](plugins/dates/README.md))
- `echo`: echoes back text following the command.
- `help`: lists all available plugins. If called with a plugin as parameter, lists all available commands
- `meter`: accurately measures someones somethingness
- `oracle`: predicts the inevitable future (german, sorry)
- `pick`: aids you in those really important life decisions
- `quote`: store quotes and provide several means to display them
- `roll`: the dice giveth and the dice taketh away
- `sampleplugin`: Just a simple sample, demonstrating the current capabilities of the `Plugin` interface
- `sonarr`: provides commands to query sonarr's API
- `spruch`: famous quotes from even more famous people (german, sorry)
- `translate`: provides near-realtime translations of all room-messages via Google Translate

## Included plugins' 3rd party requirements
- `dates`: [dateparser](https://pypi.org/project/dateparser/) to allow for almost arbitrary input format of dates
- `sonarr`: [requests](https://pypi.org/project/requests/) to query sonarr's API
- `translate`: [googletrans](https://pypi.org/project/googletrans/) to provide language detection and translation

## Plugins can
- ✔ use (almost) arbitrary python-code
- ✔ be supplied as single `.py`-file or inside their own directory (either `plugins/sample.py` OR 
  `plugins/sample/sample.py`). From [v0.0.2](https://github.com/alturiak/nio-smith/releases/tag/v0.0.2) on, use of directory-based plugins is encouraged.
- ✔ send room-messages
- ✔ send reactions to specific messages
- ✔ add multiple commands (with required power levels)
- ✔ track their sent messages
- ✔ replace (edit) their sent messages 
- ✔ hook into to received room-messages
- ✔ hook into to received reactions
- ✔ limit commands to certain rooms
- ✔ use built-in persistent storage
- ✔ automatically be supplied with config-values from plugin-specific config-files at startup
- ✔ register timers for method execution at custom intervals or at the start of each:
    - week,
    - day or
    - hour
- ❌ not hook into other room-events
- ❌ not be moved from single-file to directory while retaining existing data

## Plugins must
- ✔ use async
- ✔ instantiate `Plugin` as `plugin`
- ✔ be uniquely named and use the plugin-name as file-name (`plugins/sample.py` OR `plugins/sample/sample.py`)
- ❌ not use `time.sleep()` - please use `asyncio.sleep()` instead

## Plugins should
- ✔ raise `ImportError`s with meaningful messages for missing 3rd-party modules
- ✔ handle any other exceptions themselves
- ✔ use [type hints](https://docs.python.org/3/library/typing.html)
- ✔ adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) (except for
[maximum-line-length](https://www.python.org/dev/peps/pep-0008/#maximum-line-length) - anything up to 160 is fine by
 me)
- ✔ contain a README.md in their directory for a detailed description about
    - their intended use,
    - usage of commands and
    - additional requirements.
  

## Plugin Interface
The class `Plugin` is used by all plugins, providing the following methods. See `sampleplugin.py` for examples.
Please be advised that the plugin interface is about to
[change](https://github.com/alturiak/nio-smith/blob/master/BREAKING.md#simplify-plugins-interface) in future releases.

- `add_command`: define
    - a command word,
    - the method called when the command is encountered,
    - a short helptext and
    - an optional list of rooms the command is valid for
- `add_hook`: define
    - an event type to be hooked into
        - "m.room.message": normal text messages sent to rooms
        - "m.reaction": reactions to room messages
    - the method called when the event is encountered,
    - an optional list of rooms the hook is valid for
- `add_timer`: define
    - the method to be called (currently once every ~30s whenever a sync event is received)
    - the frequency, in which the method is to be called, either as
        - datetime.timedelta or
        - str: "weekly", "daily", "hourly"
- `store_data`: persistently store data for later use
- `read_data`: read data from store
- `clear_data`: clear stored data
- `reply`: reply to a command with a message
- `reply_notice`: reply to a command with a notice
- `react`: react to a specific event
- `replace`: replace (edit) a previous message 
- `message`: send a message to a room
- `notice`: send a notice to a room
- `is_user_in_room`: checks if a given displayname is a member of the current room
- `link_user`: given a displayname, returns a link to the user (rendered as userpill in [Element](https://element.io))
- `get_mx_user_id`: given a displayname and a command, returns a mx user id
- `add_config`: define
    - a config_item to look for in `<plugin_name>.yaml`
    - an optional default_value
    - if the value is required (must be in configuration or have a default value)
- `read_config`: read a config_item, either returning the value found in the configuration file or the default_value,
  if supplied
