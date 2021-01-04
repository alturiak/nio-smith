Nio Smith
===
[![Built with matrix-nio](https://img.shields.io/badge/built%20with-matrix--nio-brightgreen)](https://github.com/poljar/matrix-nio)
[![#nio-smith](https://img.shields.io/matrix/nio-smith:matrix.org?color=blue&label=Join%20%23nio-smith)](https://matrix.to/#/!rdBDrHapAsYdvmgGMP:pack.rocks?via=pack.rocks)

A plugin-based bot for [@matrix-org](https://github.com/matrix-org),  
written in python using
[matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html),  
supporting end-to-end-encryption out of the box.  
It's based on the lovely [nio-template](https://github.com/anoadragon453/nio-template) by [@anoadragon453](https://github.com/anoadragon453)

Pull Requests and [feedback](https://matrix.to/#/#nio-smith:pack.rocks) welcome. :-)

## Plugins
See [docs/PLUGINS.md](docs/PLUGINS.md) for further details on plugin capabilities.

## Features
- ✔ transparent end-to-end encryption (E2EE)
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

## Setup
[docs/SETUP.md](docs/SETUP.md) contains a short guide on getting you started with the bot.

## Requirements
- python 3.8 or later
- [libolm](https://gitlab.matrix.org/matrix-org/olm)    
- [matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html) with end-to-end-encryption enabled
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) for fuzzy command matching and nick linking (yes, it's worth it)

See [docs/PLUGINS.md](docs/PLUGINS.md) for further details on additional plugin requirements.

## Breaking changes
Please see [docs/BREAKING.md](docs/BREAKING.md) for a list of breaking changes.

## Project Structure
Please see [docs/STRUCTURE.md](docs/STRUCTURE.md) for a description of the project structure and included files.
