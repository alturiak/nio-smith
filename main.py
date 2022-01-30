#!/usr/bin/env python3

import logging
import asyncio
import os
import sys
import traceback
from time import time
from asyncio import sleep

from nio import (
    AsyncClient,
    AsyncClientConfig,
    RoomMessageText,
    InviteEvent,
    LocalProtocolError,
    LoginError,
    UnknownEvent,
)
from core.callbacks import Callbacks
from core.config import Config
from core.storage import Storage
from aiohttp.client_exceptions import ServerDisconnectedError, ClientConnectionError

from core.pluginloader import PluginLoader

logger = logging.getLogger(__name__)
client: AsyncClient
plugin_loader: PluginLoader
timestamp: float = time()


async def run_plugins(response):

    global plugin_loader
    global client
    global timestamp

    timestamp = await plugin_loader.run_timers(client, timestamp)


async def main():

    # TODO: this really needs to be replaced
    # probably using https://docs.python.org/3.8/library/functools.html#functools.partial
    global client
    global plugin_loader

    # Read user-configured options from a config file.
    # A different config file path can be specified as the first command line argument
    if len(sys.argv) > 1:
        config_path: str = sys.argv[1]
        if not os.path.isfile(config_path):
            logger.fatal(f"Configuration file {config_path} doesn't exist, exiting.")
            exit(1)
    else:
        config_path: str = "config.yaml"

    # Read user-configured plugin-directory
    if len(sys.argv) > 2:
        plugin_dir: str = sys.argv[2]
        if not os.path.isdir(plugin_dir):
            logger.fatal(f"Plugin directory {plugin_dir} doesn't exist, exiting.")
            exit(1)
    else:
        plugin_dir: str = "plugins"

    # Read config file
    config = Config(config_path)

    # Configure the database
    store = Storage(config.database_filepath)

    # Configuration options for the AsyncClient
    client_config = AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True,
        encryption_enabled=config.enable_encryption,
    )

    # Initialize the matrix client
    client = AsyncClient(
        config.homeserver_url,
        config.user_id,
        device_id=config.device_id,
        store_path=config.store_filepath,
        config=client_config,
    )

    # instantiate the pluginLoader
    plugin_loader = PluginLoader(config, plugin_dir)
    await plugin_loader.load_plugin_data()
    await plugin_loader.load_plugin_state()

    # Set up event callbacks
    callbacks = Callbacks(client, store, config, plugin_loader)
    client.add_event_callback(callbacks.message, (RoomMessageText,))
    client.add_event_callback(callbacks.invite, (InviteEvent,))
    client.add_event_callback(callbacks.event_unknown, (UnknownEvent,))
    client.add_response_callback(run_plugins)

    # Keep trying to reconnect on failure (with some time in-between)
    error_retries: int = 0
    while True:
        try:
            # Try to login with the configured username/password
            try:
                login_response = await client.login(
                    password=config.user_password,
                    device_name=config.device_name,
                )

                # Check if login failed
                if type(login_response) == LoginError:
                    logger.error(f"Failed to login: {login_response.message}, retrying in 15s... ({error_retries})")
                    # try logging in a few times to work around temporary login errors during homeserver restarts
                    if error_retries < 3:
                        error_retries += 1
                        await sleep(15)
                        continue
                    else:
                        return False
                else:
                    error_retries = 0

            except LocalProtocolError as e:
                # There's an edge case here where the user enables encryption but hasn't installed
                # the correct C dependencies. In that case, a LocalProtocolError is raised on login.
                # Warn the user if these conditions are met.
                if config.enable_encryption:
                    logger.fatal(
                        "Failed to login and encryption is enabled. Have you installed the correct dependencies? "
                        "https://github.com/poljar/matrix-nio#installation"
                    )
                    return False
                else:
                    # We don't know why this was raised. Throw it at the user
                    logger.fatal(f"Error logging in: {e}")

            # Login succeeded!

            # Sync encryption keys with the server
            # Required for participating in encrypted rooms
            if client.should_upload_keys:
                await client.keys_upload()

            logger.info(f"Logged in as {config.user_id}")
            await client.sync_forever(timeout=30000, full_state=True)

        except (
            ClientConnectionError,
            ServerDisconnectedError,
            AttributeError,
            asyncio.TimeoutError,
        ) as err:
            logger.debug(err)
            logger.debug(traceback.print_exc())
            logger.warning(f"Unable to connect to homeserver, retrying in 15s...")

            # Sleep so we don't bombard the server with login requests
            await sleep(15)
        finally:
            # Make sure to close the client connection on disconnect
            await client.close()


asyncio.get_event_loop().run_until_complete(main())
