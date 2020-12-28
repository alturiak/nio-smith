Nio Smith
===
[![#nio-smith](https://img.shields.io/matrix/nio-smith:matrix.org?color=blue&label=%23nio-smith)](https://matrix.to/#/!rdBDrHapAsYdvmgGMP:pack.rocks?via=pack.rocks)

A modular bot for [@matrix-org](https://github.com/matrix-org), written in python using
[matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html), supporting end-to-end-encryption out of the box.
It's based on the lovely [nio-template](https://github.com/anoadragon453/nio-template) and tries to incorporate most
 of [@anoadragon453](https://github.com/anoadragon453) 's improvements.

Be advised: the bot (and it's name ;-) is a work in progress, but basic functionality exists. Huge or small rewrites of
 any part of the project may or may not happen soon(ish).

Please see [BREAKING.md](BREAKING.md) for a list of breaking changes.
 
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

See [PLUGINS.md](PLUGINS.md) for further details on plugin capabilities.

## Requirements
- python 3.8 or later
- [libolm](https://gitlab.matrix.org/matrix-org/olm)    
- [matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html) with end-to-end-encryption enabled
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) for fuzzy command matching and nick linking (yes, it's worth it)

See [PLUGINS.md](PLUGINS.md) for further details on additional plugin requirements.


## Setup
[SETUP.md](SETUP.md) contains a short guide on getting you started with the bot.

## Project Structure
Please see [STRUCTURE.md](STRUCTURE.md) for a description of the project structure and included files.
