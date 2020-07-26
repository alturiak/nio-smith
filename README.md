Nio Smith
===
[![#nio-smith](https://img.shields.io/matrix/nio-smith:matrix.org?color=blue&label=%23nio-smith)](https://matrix.to/#/!rdBDrHapAsYdvmgGMP:pack.rocks?via=pack.rocks)

A modular bot for [@matrix-org](https://github.com/matrix-org), written in python using
[matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html), supporting end-to-end-encryption out of the box.
It's based on the lovely [nio-template](https://github.com/anoadragon453/nio-template) and tries to incorporate most
 of [@anoadragon453](https://github.com/anoadragon453) 's improvements.

Be advised: the bot (and it's name ;-) is a work in progress, but basic functionality exists. Huge or small rewrites of
 any part of the project may or may not happen soon(ish).
 
Currently included plugins consist mostly of pretty silly, mostly semi-useful stuff we used on IRC. PRs and
[feedback](https://matrix.to/#/#nio-smith:pack.rocks) welcome. :-)

## Features
- ✔ transparent end-to-end encryption (EE2E)
- ✔ configurable command-prefix
- ✔ fuzzy command matching (for the autocorrect-victims among us)
- ✔ dynamic plugin-loading (on startup), just place your plugin in the `plugins`-directory
- ✔ autojoin channels on invite (can be restricted to specified accounts)
- ✔ silently ignores unknown commands to avoid clashes with other bots using the same command prefix
- ✔ dynamic population of `help`-command with plugins valid for the respective room
- ✔ resilience against temporary homeserver-outages (e.g. during restarts)
- ✔ resilience against exceptions caused by plugins
- ❌ cross-signing support
- ❌ dynamic plugin-loading (at runtime)
- ❌ user-management

### Plugins can
- ✔ use (almost) arbitrary python-code
- ✔ send room-messages
- ✔ add multiple commands
- ✔ track their sent messages
- ✔ hook into to received room-messages
- ✔ hook into to received reactions
- ✔ register methods for recurring execution (roughly once every 30s)
- ✔ limit commands to certain rooms
- ✔ use built-in persistent storage
- ✔ automatically be supplied with config-values from plugin-specific config-files at startup
- ❌ hook into other room-events

### Plugins must
- ✔ use async
- ✔ instantiate `Plugin`
- ❌ use `time.sleep()` - please use `asyncio.sleep()` instead

### Plugins should
- ✔ raise `ImportError`s with meaningful messages for missing 3rd-party modules
- ✔ handle any other exceptions themselves
- ✔ use [type hints](https://docs.python.org/3/library/typing.html)
- ✔ adhere to [PEP 8](https://www.python.org/dev/peps/pep-0008/) (except for
[maximum-line-length](https://www.python.org/dev/peps/pep-0008/#maximum-line-length) - anything up to 160 is fine by
 me) 

## Requirements
- python 3.8 or later
- [matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html) with end-to-end-encryption enabled
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) for fuzzy command matching and nick linking (yes, it's worth it)

### Current plugin 3rd party requirements
- `sonarr`: [requests](https://pypi.org/project/requests/) to query sonarr's API
- `translate`: [googletrans](https://pypi.org/project/googletrans/) to provide language detection and translation

## Plugins
- `echo`: echoes back text following the command.
- `help`: lists all available plugins. If called with a plugin as parameter, lists all available commands
- `meter`: accurately measures someones somethingness
- `oracle`: predicts the inevitable future
- `pick`: aids you in those really important life decisions
- `quote`: store quotes and provide several means to display them
- `roll`: the dice giveth and the dice taketh away
- `sampleplugin`: Just a simple sample, demonstrating the current possibilities of `Plugin`
- `sonarr`: provides commands to query sonarr's API
- `spruch`: famous quotes from even more famous people (german, sorry)
- `translate`: provides near-realtime translations of all room-messages via Google Translate

## Project structure

#### `main.py`

Initialises the config file, the bot store, and nio's AsyncClient (which is
used to retrieve and send events to a matrix homeserver). It also registering
some callbacks on the AsyncClient to tell it to call some functions when
certain events are received (such as an invite to a room, or a new message in a
room the bot is in).
It also performs login and syncs indefinitely.

#### `config.py`

This file reads a config file at a given path (hardcoded as `config.yaml` in
`main.py`), processes everything in it and makes the values available to the
rest of the bot's code so it knows what to do. Most of the options in the given
config file have default values, so things will continue to work even if an
option is left out of the config file. Obviously there are some config values
that are required though, like the homeserver URL, username, access token etc.
Otherwise the bot can't function.

#### `storage.py`

Creates (if necessary) and connects to a SQLite3 database and provides commands
to put or retrieve data from it. Table definitions should be specified in
`_initial_setup`, and any necessary migrations should be put in
`_run_migrations`. There's currently no defined method for how migrations
should work though.

#### `plugin.py`

The class used by all plugins, providing the following methods:
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
- `store_data`: persistently store data for later use
- `read_data`: read data from store
- `clear_data`: clear stored data
- `reply`: reply to a command with a message
- `reply_notice`: reply to a command with a notice
- `message`: send a message to a room
- `notice`: send a notice to a room
- `is_user_in_room`: checks if a given displayname is a member of the current room
- `link_user`: given a displayname, returns a link to the user (rendered as userpill in [Element](https://element.io))
- `add_config`: define
    - a config_item to look for in `<plugin_name>.yaml`
    - an optional default_value
    - if the value is required (must be in configuration or have a default value)
- `read_config`: read a config_item, \
        either returning the value found in the configuration file \
        or the default_value, if supplied
    
#### `pluginloader.py`

Handles dynamic (at startup) loading of any plugins in the `plugins`-directory.
Holds a list of all loaded plugins and serves as interface between the bot and the plugins. Any execution of the
 plugins' `command`s, `timer`s or `hook`s should be done through the `main.py`s `plugin_loader`.

#### `callbacks.py`

Holds callback methods which get run when the bot get a certain type of event
from the homserver during sync. The type and name of the method to be called
are specified in `main.py`. Currently there are two defined methods, one that
gets called when a message is sent in a room the bot is in, and another that
runs when the bot receives an invite to the room.

The message callback function, `message`, checks if the message was for the
bot, and whether it was a command. If both of those are true, the bot will
process that command.

The invite callback function, `invite`, processes the invite event and attempts
to join the room. This way, the bot will auto-join any room it is invited to.

#### `bot_commands.py`

Where all the bot's commands used to be defined. They should be provided by plugins now.

A `Command` object is created when a message comes in that's recognised as a
command from a user directed at the bot (either through the specified command
prefix (defined by the bot's config file), or through a private message
directly to the bot. The `process` command calls the pluginloader to find a matching command.

#### `message_responses.py`

Where responses to messages that are posted in a room (but not necessarily
directed at the bot) used to be specified. `callbacks.py` will listen for messages in
rooms the bot is in, and upon receiving one will create a new `Message` object
(which contains the message text, amongst other things) and calls `process()`
on it, which can send a message to the room as it sees fit.

Currently runs hooks for "m.room.message" registered by plugins, used e.g. by the `translate`-plugin to provide a
 translation for received room-messages. 

#### `chat_functions.py`

A separate file to hold helper methods related to messaging. Mostly just for
organisational purposes. Currently holds `send_text_to_room`, a helper
method for sending formatted messages to a room and `send_typing` which does the same including a brief typing
 notification (to make the bot seem almost like a real human being).

#### `errors.py`

Custom error types for the bot. Currently there's only one special type that's
defined for when a error is found while the config file is being processed.

#### `sample.config.yaml`

The sample configuration file. People running your bot should be advised to
copy this file to `config.yaml`, then edit it according to their needs. Be sure
never to check the edited `config.yaml` into source control since it'll likely
contain sensitive details like an access token!
