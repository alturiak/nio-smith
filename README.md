Nio Smith
===
[![Built with matrix-nio](https://img.shields.io/badge/built%20with-matrix--nio-brightgreen)](https://github.com/poljar/matrix-nio)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/nio-smith/badge/?version=latest)](https://nio-smith.readthedocs.io/en/latest/?badge=latest)
[![#nio-smith](https://img.shields.io/matrix/nio-smith:matrix.org?color=blue&label=Join%20%23nio-smith)](https://matrix.to/#/!rdBDrHapAsYdvmgGMP:pack.rocks?via=pack.rocks)

A plugin-based bot for [@matrix-org](https://github.com/matrix-org),  
written in python using
[matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html),  
supporting end-to-end-encryption out of the box.  
It's based on the lovely [nio-template](https://github.com/anoadragon453/nio-template) by [@anoadragon453](https://github.com/anoadragon453)

Pull Requests and [feedback](https://matrix.to/#/#nio-smith:pack.rocks) welcome. :-)

## Plugins
See [plugins/README.md](plugins/README.md) for further details on plugin capabilities.

## Features
- ✔ dynamic plugin-loading (on startup), just place your plugin in the `plugins`-directory
- ✔ transparent end-to-end encryption (E2EE)
- ✔ configurable command-prefix
- ✔ fuzzy command matching (for the autocorrect-victims among us)
- ✔ silently ignores unknown commands to avoid clashes with other bots using the same command prefix
- ✔ dynamic population of `help`-command with plugins valid for the respective room
- ✔ autojoin channels on invite (can be restricted to specified accounts)
- ✔ resilience against temporary homeserver-outages (e.g. during restarts)
- ✔ resilience against exceptions caused by plugins
- ✔ simple rate-limiting to avoid losing events to homeserver-side ratelimiting
- ❌ cross-signing support
- ❌ dynamic plugin-loading (at runtime)
- ❌ user-management

## Setup
[docs/SETUP.md](docs/SETUP.md) contains a short guide on getting you started with the bot.

## Requirements
- python 3.8 or later (be aware that specific plugins might require newer python versions).
- [libolm](https://gitlab.matrix.org/matrix-org/olm)    
- [matrix-nio](https://matrix-nio.readthedocs.io/en/latest/nio.html) with end-to-end-encryption enabled
- [fuzzywuzzy](https://github.com/seatgeek/fuzzywuzzy) for fuzzy command matching and nick linking (yes, it's worth it)
- [Pillow](https://pypi.org/project/Pillow/) for image-handling
- [blurhash-python](https://pypi.org/project/blurhash-python/) to generate blurhashes of image files
- [aiofiles](https://pypi.org/project/aiofiles/) for file-handling
- [requests](https://pypi.org/project/requests/) for fetching images

See [plugins/README.md](plugins/README.md) for further details on additional plugin requirements.

## Breaking changes
Please see [docs/BREAKING.md](docs/BREAKING.md) for a list of breaking changes.

## Project Structure
Please see [docs/STRUCTURE.md](docs/STRUCTURE.md) for a description of the project structure and included files.
