# -*- coding: utf8 -*-
import datetime
from typing import Dict, List

import requests
from nio import AsyncClient

from core.bot_commands import Command
from core.plugin import Plugin
import logging

logger = logging.getLogger(__name__)
plugin = Plugin("federation_status", "Matrix", "Keeps track of federation status with all homeservers in the bot's rooms")


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """

    plugin.add_config("room_list", default_value=[], is_required=False)
    plugin.add_config("warn_cert_expiry", default_value=7, is_required=True)
    plugin.add_config("server_max_age", default_value=60, is_required=True)
    plugin.add_config("federation_tester_url", default_value="https://federationtester.matrix.org", is_required=True)
    plugin.add_command("federation_status", command_federation_status, "Displays the current status of all federating servers in the room",
                       room_id=plugin.read_config("room_list"))

    plugin.add_timer(update_federation_status, frequency=datetime.timedelta(minutes=5))


class Server:
    def __init__(self, server_name: str):
        self.server_name: str = server_name
        self.last_update: datetime.datetime or None = None
        self.last_alive: datetime.datetime or None = None
        self.cert_expiry: datetime.datetime or None = None
        self.federation_test()
        self.last_posted_warning: datetime.datetime = datetime.datetime(1970, 1, 1)
        self.currently_alive: bool = self.is_alive()

    def is_alive(self) -> bool:
        """
        Checks if the server is currently alive, e.g. if last_alive >= last_update.
        :return:
        """

        if self.last_alive and self.last_update:
            return self.last_alive >= self.last_update

    async def time_until_expire(self) -> datetime.timedelta:
        """
        Returns the time left until the server's cert expires
        :return:
        """

        return self.cert_expiry - datetime.datetime.now()

    async def is_expired(self) -> bool:
        """
        Checks if the server's certificate is currently expired
        :return:
        """

        return await self.time_until_expire() < datetime.timedelta(0)

    async def last_updated_within(self, timeframe: datetime.timedelta) -> bool:
        """
        Checks whether the server has been successfully updated within the given timeframe
        :param timeframe:
        :return:
        """

        return self.last_update > (datetime.datetime.now() - timeframe)

    async def needs_update(self) -> bool:
        """
        Checks whether the server's data needs to be updates
        :return:
        """

        return not await self.last_updated_within(datetime.timedelta(minutes=plugin.read_config("server_max_age")))

    async def needs_warning(self) -> bool:
        """
        Check whether a new warning is warranted
        :return:
        """

        return self.last_posted_warning < self.last_alive

    def federation_test(self):
        """
        Do a federation_test for the given server
        :return:   Tuple of:    last_update: timestamp of the last successful update,
                                last_alive: timestamp of the servers last successful check,
                                cert_expiry: timestamp of the server's certificate expiry date
        """

        api_parameters = {"server_name": self.server_name}

        try:
            response: requests.Response = requests.get(plugin.read_config("federation_tester_url") + "/api/report", params=api_parameters)
        except requests.exceptions.ConnectionError as err:
            logger.warning(f"Connection to federation-tester failed: {err}")
            return

        if response.status_code == 200:
            federation_data: Dict[str, any] = response.json()
            self.last_update = datetime.datetime.now()
            if federation_data.get("FederationOK"):
                self.last_alive = datetime.datetime.now()
                self.currently_alive = True
            else:
                self.currently_alive = False
            # TODO: get certificate expire date for all servers?


async def update_federation_status(client: AsyncClient):
    """
    Regularly check last_update timestamps of each server and get an updated status if older than server_max_age
    :param client:
    :return:
    """

    # get a list of shared servers on rooms the plugin is active for
    shared_servers: List[str] = await plugin.get_connected_servers(client, plugin.read_config("room_list"))
    server_list_saved: Dict[str, Server] or None = await plugin.read_data("server_list")
    data_changed: bool = False

    if not server_list_saved:
        server_list_new: Dict[str, Server] = {}
        # get initial server status and save it
        for server_name in shared_servers:
            server_list_new[server_name] = Server(server_name)
        await plugin.store_data("server_list", server_list_new)

    else:
        # delete data for servers we're not federating with anymore
        server_names_saved: List[str] = list(server_list_saved.keys())
        for server_name in server_names_saved:
            if server_name not in shared_servers:
                del server_list_saved[server_name]
                data_changed = True
        del server_names_saved

        # check for changes
        previously_dead_servers: List[str] = []
        previously_alive_servers: List[str] = []
        new_dead_servers: List[str] = []
        new_alive_servers: List[str] = []

        for server in server_list_saved.values():
            if server.currently_alive:
                previously_alive_servers.append(server.server_name)
            else:
                previously_dead_servers.append(server.server_name)

        # update servers' status if required
        server_list_new: Dict[str, Server] = server_list_saved
        for server in server_list_new.values():
            if not server.currently_alive or await server.needs_update():
                # check status of server, always update if server was dead before
                server.federation_test()
                data_changed = True
                if server.currently_alive and server.server_name not in previously_alive_servers:
                    new_alive_servers.append(server.server_name)
                if not server.currently_alive and server.server_name not in previously_dead_servers:
                    new_dead_servers.append(server.server_name)

        # announce any changes
        room_list: List[str] = plugin.read_config("room_list")
        if not room_list:
            room_list = [x for x in client.rooms]

        for room_id in room_list:
            if new_dead_servers and [value for value in new_dead_servers if value in await plugin.get_connected_servers(client, [room_id])]:
                await plugin.send_notice(client, room_id, f"Federation warning: {', '.join(new_dead_servers)} failed. Expect message delays.")
            if new_alive_servers and [value for value in new_alive_servers if value in await plugin.get_connected_servers(client, [room_id])]:
                await plugin.send_notice(client, room_id, f"Federation recovery: {', '.join(new_alive_servers)} succeeded. Users back online.")

        if data_changed:
            await plugin.store_data("server_list", server_list_new)


async def command_federation_status(command: Command):
    """
    Displays the current status of all federating servers in the room
    :param command:
    :return:
    """
    pass


setup()
