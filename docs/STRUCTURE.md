Project structure
===

#### `main.py`

Initialises the config file, the bot store, and nio's AsyncClient (which is
used to retrieve and send events to a matrix homeserver). It also registering
some callbacks on the AsyncClient to tell it to call some functions when
certain events are received (such as an invite to a room, or a new message in a
room the bot is in).
It also performs login and syncs indefinitely.

#### `sample.config.yaml`

The sample configuration file. People running your bot should be advised to
copy this file to `config.yaml`, then edit it according to their needs. Be sure
never to check the edited `config.yaml` into source control since it'll likely
contain sensitive details like an access token!

#### `core/bot_commands.py`

Where all the bot's commands used to be defined. They should be provided by plugins now.

A `Command` object is created when a message comes in that's recognised as a
command from a user directed at the bot (either through the specified command
prefix (defined by the bot's config file), or through a private message
directly to the bot. The `process` command calls the pluginloader to find a matching command.

#### `core/callbacks.py`

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

#### `core/chat_functions.py`

A separate file to hold helper methods related to messaging. Mostly just for
organisational purposes. Currently holds `send_text_to_room`, a helper
method for sending formatted messages to a room and `send_typing` which does the same including a brief typing
 notification (to make the bot seem almost like a real human being).

#### `core/config.py`

This file reads a config file at a given path (hardcoded as `config.yaml` in
`main.py`), processes everything in it and makes the values available to the
rest of the bot's code so it knows what to do. Most of the options in the given
config file have default values, so things will continue to work even if an
option is left out of the config file. Obviously there are some config values
that are required though, like the homeserver URL, username, access token etc.
Otherwise the bot can't function.

#### `core/errors.py`

Custom error types for the bot. Currently there's only one special type that's
defined for when a error is found while the config file is being processed.

#### `core/plugin.py`

The class used by all plugins, providing plugins with interface methods as described in
[plugins/PLUGINS.md](../plugins/README.md)

#### `core/pluginloader.py`

Handles dynamic (at startup) loading of any plugins in the `plugins`-directory.
Holds a list of all loaded plugins and serves as interface between the bot and the plugins. Any execution of the
 plugins' `command`s, `timer`s or `hook`s should be done through the `main.py`s `plugin_loader`.

#### `core/storage.py`

Creates (if necessary) and connects to a SQLite3 database and provides commands
to put or retrieve data from it. Table definitions should be specified in
`_initial_setup`, and any necessary migrations should be put in
`_run_migrations`. There's currently no defined method for how migrations
should work though.

#### `core/timer.py`
Timers are used to by plugins to call recurring methods. 

