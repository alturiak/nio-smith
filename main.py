#!/usr/bin/env python3

import logging
import asyncio
from time import sleep

from nio import (
    AsyncClient,
    AsyncClientConfig,
    RoomMessageText,
    InviteEvent,
    LocalProtocolError, LoginResponse, LoginError)
from callbacks import Callbacks
from config import Config
from storage import Storage
from aiohttp.client_exceptions import (
    ServerDisconnectedError,
    ClientConnectionError)
import plugins.sabnzbdapi

logger = logging.getLogger(__name__)
client = ""


async def run_plugins(response):

    await plugins.sabnzbdapi.watchjobs(client)


async def main():
    # TODO: this really needs to be replaced
    # probably using https://docs.python.org/3.8/library/functools.html#functools.partial
    global client

    # Read config file
    config = Config("config.yaml")

    # Configure the database
    store = Storage(config.database_filepath)

    # Configuration options for the AsyncClient
    client_config = AsyncClientConfig(
        max_limit_exceeded=0,
        max_timeouts=0,
        store_sync_tokens=True
    )

    # Initialize the matrix client
    client = AsyncClient(
        config.homeserver_url,
        config.user_id,
        device_id=config.device_id,
        store_path=config.store_filepath,
        config=client_config,
    )

    # Set up event callbacks
    callbacks = Callbacks(client, store, config)
    client.add_event_callback(callbacks.message, (RoomMessageText,))
    client.add_event_callback(callbacks.invite, (InviteEvent,))
    client.add_response_callback(run_plugins)

    while True:
        try:
            loginresponse = await client.login(password=config.user_password, device_name=config.device_name)
            if type(loginresponse) == LoginError:
                print(loginresponse)
                return False
            try:
                await client.keys_upload()
            except LocalProtocolError:
                pass

            await client.sync_forever(timeout=30000, full_state=True)

        except (ClientConnectionError, ServerDisconnectedError):
            print("Disconnected from Server, reconnecting in 15s...")
            await client.close()
            sleep(15)


asyncio.get_event_loop().run_until_complete(main())
