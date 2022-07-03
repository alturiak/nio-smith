# -*- coding: utf8 -*-
import datetime
import random
import ssl
import socket
from typing import Dict, List, Tuple
import pytz
import requests
from nio import AsyncClient

from core.bot_commands import Command
from core.plugin import Plugin
import logging

logger = logging.getLogger(__name__)
plugin = Plugin(
    "federation_status",
    "Matrix",
    "Keeps track of federation status with all homeservers in the bot's rooms",
)


def setup():
    """
    This just moves the initial setup-commands to the top for better readability
    :return: -
    """

    plugin.add_config("room_list", default_value=None, is_required=False)
    plugin.add_config("warn_cert_expiry", default_value=7, is_required=True)
    plugin.add_config("server_max_age", default_value=60, is_required=True)
    plugin.add_config("server_ignore_list", default_value=None, is_required=True)
    plugin.add_config(
        "federation_tester_url",
        default_value="https://federationtester.matrix.org",
        is_required=True,
    )
    plugin.add_command(
        "federation",
        command_federation_status,
        "Displays the current status of all federating servers in the room",
        room_id=plugin.read_config("room_list"),
    )
    plugin.add_command("federation_update", update_federation_status, "Update all known server's data")

    plugin.add_timer(update_federation_status, frequency=datetime.timedelta(minutes=5))


class Server:
    def __init__(self, server_name: str):
        self.server_name: str = server_name
        self.last_update: datetime.datetime or None = None
        self.last_alive: datetime.datetime or None = None
        self.cert_expiry: datetime.datetime or None = None
        self.last_posted_warning: datetime.datetime = datetime.datetime(1970, 1, 1)
        self.software: str or None = None
        self.version: str or None = None

        self.federation_test()
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

        return await self.cert_expiry < datetime.datetime.now()

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

        # server is currently offline and hasn't been offline for more than a week
        if not self.currently_alive and self.last_alive and self.last_alive > datetime.datetime.now() - datetime.timedelta(days=7):
            return True

        # certificate will expire in less than 10 minutes
        elif self.cert_expiry < datetime.datetime.now() + datetime.timedelta(minutes=10):
            return True

        # server hasn't been updated for more than server_max_age (+-5 minutes to distribute updates a little)
        elif not await self.last_updated_within(datetime.timedelta(minutes=plugin.read_config("server_max_age") + random.randint(-5, 5))):
            return True

        else:
            return False

    async def needs_warning(self) -> bool:
        """
        Warn once, if a certificate expiration date is known, is in the future, but less than warn_steps away
        :return:
        """

        # TODO: only report servers that have been offline for more than 5 minutes, but report expired certs immediately?

        warn_steps: List[datetime.timedelta] = [
            datetime.timedelta(minutes=10),
            datetime.timedelta(days=1),
            datetime.timedelta(days=plugin.read_config("warn_cert_expiry")),
        ]

        step: datetime.timedelta
        if not self.cert_expiry:
            return False
        else:
            for step in warn_steps:
                if datetime.datetime.now() < self.cert_expiry < (datetime.datetime.now() + step) and self.last_posted_warning < (
                    datetime.datetime.now() - step
                ):
                    return True
            return False

    def federation_test(self):
        """
        Do a federation_test for the given server
        :return:   Tuple of:    last_update: timestamp of the last successful update,
                                last_alive: timestamp of the servers last successful check,
                                cert_expiry: timestamp of the server's certificate expiry date
        """

        api_parameters = {"server_name": self.server_name}
        logger.debug(f"Updating {self.server_name}")

        try:
            response: requests.Response = requests.get(
                plugin.read_config("federation_tester_url") + "/api/report",
                params=api_parameters,
            )
        except requests.exceptions.ConnectionError as err:
            logger.warning(f"Connection to federation-tester failed: {err}")
            return

        if response.status_code == 200:
            federation_data: Dict[str, any] = response.json()
            self.last_update = datetime.datetime.now()
            self.software = federation_data.get("Version").get("name")
            self.version = federation_data.get("Version").get("version")
            # check certificates of all hosts and store the smallest expiry date
            host: str
            port: int
            hosts: List[Tuple[str, int]] = []
            if federation_data.get("WellKnownResult").get("m.server"):
                # read host and port from well-known, strip trailing '.' from host
                host = federation_data.get("WellKnownResult").get("m.server").split(":")[0].rstrip(".")
                if len(federation_data.get("WellKnownResult").get("m.server").split(":")) > 1:
                    port = int(federation_data.get("WellKnownResult").get("m.server").split(":")[1])
                else:
                    port = 8448
                hosts = [(host, port)]
            else:
                # read hosts from DNS-Result, strip trailing '.', default to Port 8448 for now
                for host in federation_data.get("DNSResult").get("Hosts").keys():
                    hosts.append((host.rstrip("."), 8448))

            min_expire_date: datetime.datetime = datetime.datetime(year=2500, month=1, day=1)
            for (host, port) in hosts:
                try:
                    expire_date: datetime.datetime or None = ssl_expiry_datetime(host, port)
                except ssl.SSLCertVerificationError:
                    expire_date = None
                if expire_date:
                    min_expire_date = min(expire_date, min_expire_date)
            self.cert_expiry = min_expire_date

            if federation_data.get("FederationOK"):
                self.last_alive = datetime.datetime.now()
                self.currently_alive = True
            else:
                self.currently_alive = False


def ssl_expiry_datetime(host: str, port=8448) -> datetime.datetime or None:
    """
    Connects to a host on the given port and retrieves it's TLS-certificate.
    :param host: a hostname or IP-Address
    :param port: the port to connect to
    :return: datetime.datime of the certificates expiration
    """

    ssl_date_fmt: str = r"%b %d %H:%M:%S %Y %Z"
    context: ssl.SSLContext = ssl.create_default_context()
    conn: ssl.SSLSocket = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=host)
    # 3 second timeout because Lambda has runtime limitations
    conn.settimeout(3.0)
    try:
        conn.connect((host, port))
        ssl_info: Dict or Tuple or None = conn.getpeercert()
        if ssl_info:
            expiry_date: datetime.datetime = datetime.datetime.strptime(ssl_info["notAfter"], ssl_date_fmt)
            # add timezone offset
            timezone = pytz.timezone("CET")
            offset = timezone.utcoffset(expiry_date)
            expiry_date = expiry_date + offset
            return expiry_date
        else:
            return None
    except socket.timeout:
        return None


async def update_federation_status(client_or_command: AsyncClient or Command):
    """
    Regularly check last_update timestamps of each server and get an updated status if older than server_max_age
    :param client:
    :return:
    """

    client: AsyncClient
    forced_update: bool = False
    if isinstance(client_or_command, AsyncClient):
        # we're called by timer
        client = client_or_command
    else:
        # we're called by command, force an update
        client = client_or_command.client
        forced_update = True

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
        server_names_saved: List[str] = list(server_list_saved.keys())

        # delete data for servers we're not federating with anymore
        for server_name in server_names_saved:
            if server_name not in shared_servers:
                del server_list_saved[server_name]
                data_changed = True

        # add new servers
        for server_name in shared_servers:
            if server_name not in server_names_saved:
                server_list_saved[server_name] = Server(server_name)
        del server_names_saved

        # check for changes
        previously_dead_servers: List[str] = []
        previously_alive_servers: List[str] = []
        new_dead_servers: List[str] = []
        new_alive_servers: List[str] = []
        need_warning_servers: List[Tuple[str, datetime.datetime]] = []

        for server in server_list_saved.values():
            if server.currently_alive:
                previously_alive_servers.append(server.server_name)
            else:
                previously_dead_servers.append(server.server_name)

        # update servers' status if required
        server_list_new: Dict[str, Server] = server_list_saved
        for server in server_list_new.values():
            if forced_update or await server.needs_update():
                server.federation_test()
                data_changed = True
                if server.currently_alive and server.server_name not in previously_alive_servers:
                    new_alive_servers.append(server.server_name)

                if not server.currently_alive and server.server_name not in previously_dead_servers:
                    new_dead_servers.append(server.server_name)

                if await server.needs_warning():
                    need_warning_servers.append((server.server_name, server.cert_expiry))
                    server.last_posted_warning = datetime.datetime.now()

        # announce any changes
        room_list: List[str] = plugin.read_config("room_list")
        if not room_list:
            room_list = [x for x in client.rooms]

        for room_id in room_list:
            for server in new_dead_servers:
                if server not in plugin.read_config("server_ignore_list"):
                    try:
                        user_ids: List[str] = (await plugin.get_users_on_servers(client, [server], [room_id]))[server]
                        message: str = f"Federation error: {server} offline.  \n"
                        message += f"Isolated users: {', '.join([await plugin.link_user_by_id(client, room_id, user_id) for user_id in user_ids])}."
                        await plugin.send_notice(client, room_id, message)
                    except KeyError:
                        pass

            for server in new_alive_servers:
                if server not in plugin.read_config("server_ignore_list"):
                    try:
                        user_ids: List[str] = (await plugin.get_users_on_servers(client, [server], [room_id]))[server]
                        message: str = f"Federation recovery: {server} back online.  \n"
                        message += f"Welcome back, {', '.join([await plugin.link_user_by_id(client, room_id, user_id) for user_id in user_ids])}."
                        await plugin.send_notice(client, room_id, message)
                    except KeyError:
                        pass

            expire_date: datetime.datetime
            for server, expire_date in need_warning_servers:
                if server not in plugin.read_config("server_ignore_list"):
                    try:
                        user_ids: List[str] = (await plugin.get_users_on_servers(client, [server], [room_id]))[server]
                        message: str = f"Federation warning: {server}'s certificate will expire on {expire_date} (in {expire_date - datetime.datetime.now()})  \n"
                        message += (
                            f"{', '.join([await plugin.link_user_by_id(client, room_id, user_id) for user_id in user_ids])} will be isolated until "
                            f"the server's certificate has been renewed."
                        )
                        await plugin.send_message(client, room_id, message)
                    except KeyError:
                        pass

        if data_changed:
            await plugin.store_data("server_list", server_list_new)


async def command_federation_status(command: Command):
    """
    Displays the current status of all federating servers in the room
    :param command:
    :return:
    """

    message: str = ""
    room_list: List[str] = []

    if len(command.args) == 1 and command.args[0] == "global":
        message += f"Federation status (all known rooms):  \n"
    elif len(command.args) == 0:
        message += f"Federation status (this room only):  \n"
        room_list = [command.room.room_id]
    else:
        await plugin.respond_notice(command, "Usage: `federation [global]`")
        return

    server_list_saved: Dict[str, Server] or None = await plugin.read_data("server_list")
    server: Server
    server_name: str

    for server_name in await plugin.get_connected_servers(command.client, room_list):
        server = server_list_saved[server_name]
        if not server.currently_alive:
            message += f"<font color=red>{server.server_name} offline (last alive: {server.last_alive})</font>. "
        elif (datetime.datetime.now() + datetime.timedelta(days=plugin.read_config("warn_cert_expiry"))) > server.cert_expiry:
            message += f"<font color=yellow>{server.server_name} warning</font>. "
        else:
            message += f"<font color=green>{server.server_name} online</font>. "
        if server.software:
            message += f"**Server**: {server.software} ({server.version}). "
        if server.cert_expiry:
            message += f"**Cert expiry**: {server.cert_expiry} ({server.cert_expiry - datetime.datetime.now()}). "

        num_users: int = len((await plugin.get_users_on_servers(command.client, [server.server_name], room_list))[server_name])
        message += f"**Users**: {num_users}.  \n"

    await plugin.respond_notice(command, message)


setup()
