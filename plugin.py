import os.path
from os import remove, path
import pickle
from typing import List, Any, Dict, Callable, Union, Hashable
import datetime
import yaml
from chat_functions import send_text_to_room, send_reaction, send_replace
from asyncio import sleep
import logging
from nio import AsyncClient, JoinedMembersResponse, RoomMember, RoomSendResponse
from timer import Timer
from fuzzywuzzy import fuzz
import jsonpickle
logger = logging.getLogger(__name__)


class Plugin:

    def __init__(self, name: str, category: str, description: str):
        """
        commands (list[tuple]): list of commands in the form of (trigger: str, method: str, helptext: str)

        """
        self.category: str = category
        self.name: str = name
        self.description: str = description
        self.commands: Dict[str, PluginCommand] = {}
        self.help_texts: Dict[str, str] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.timers: List[Timer] = []
        self.rooms: List[str] = []

        if path.isdir(f"plugins/{self.name}"):
            self.is_directory_based: bool = True
            self.basepath: str = f"plugins/{self.name}/{self.name}"
        else:
            self.is_directory_based: bool = False
            self.basepath: str = f"plugins/{self.name}"

        self.plugin_data_filename: str = f"{self.basepath}.pkl"
        self.plugin_dataj_filename: str = f"{self.basepath}.json"
        self.config_items_filename: str = f"{self.basepath}.yaml"

        self.plugin_data: Dict[str, Any] = {}
        self.config_items: Dict[str, Any] = {}
        self.configuration: Union[Dict[Hashable, Any], list, None] = self.__load_config()

    def is_valid_for_room(self, room_id: str) -> bool:

        if self.rooms == [] or room_id in self.rooms:
            return True
        else:
            return False

    def get_help_text(self):
        # TODO: change to use of self.help_texts
        """
        Extract helptexts from commands

        :return:
        List[dict]: {command: helptext}
        """

        command_help: List[Dict] = []
        for command in self.commands:
            command_help.append({command[0]: command[2]})

        return command_help

    def add_command(self, command: str, method: Callable, help_text: str, room_id: List[str] = None, power_level: int = 0):
        """
        Adds a new command
        :param command: the actual name of the command, e.g. !help
        :param method: the method to be called when the command is received
        :param help_text: the command's helptext, e.g. as displayed by !help
        :param power_level: an optional matrix room power_level needed for users to be able to execute the command (defaults to 0, all users may execute the command)
        :param room_id: an optional room_id-list the command will be added on (defaults to none, command will be active on all rooms)
        :return:
        """

        plugin_command = PluginCommand(command, method, help_text, power_level, room_id)
        if command not in self.commands.keys():
            self.commands[command] = plugin_command
            self.help_texts[command] = help_text
            # Add rooms from command to the rooms the plugin is valid for
            if room_id:
                for room in room_id:
                    if room not in self.rooms:
                        self.rooms.append(room)
            logger.debug(f"Added command {command} to rooms {room_id}")
        else:
            logger.error(f"Error adding command {command} - command already exists")

    def get_commands(self):
        """
        Extract called methods from commands

        :return:
        dict: {command: method}
        """

        return self.commands

    def add_hook(self, event_type: str, method: Callable, room_id: List[str] = None):

        plugin_hook = PluginHook(event_type, method, room_id)
        if event_type not in self.hooks.keys():
            self.hooks[event_type] = [plugin_hook]
        else:
            self.hooks[event_type].append(plugin_hook)
        logger.debug(f"Added hook for {event_type} to rooms {room_id}")

    def get_hooks(self):

        return self.hooks

    def add_timer(self, method: Callable, frequency: str or datetime.timedelta or None = None):
        """

        :param method: the method to be called when the timer trigger
        :param frequency: frequency in which the timer should trigger
                can be:
                - datetime.timedelta: to specify timeperiods between triggers or
                - str:
                    - "weekly": run once a week roughly at Monday, 00:00
                    - "daily": run once a day roughly at midnight
                    - "hourly": run once an hour roughly at :00
                - None: triggers about every thirty seconds

        :return:
        """

        self.timers.append(Timer(f"{self.name}.{method.__name__}", method, frequency))

    def get_timers(self) -> List[Timer]:

        return self.timers

    def store_data(self, name: str, data: Any) -> bool:
        """
        Store data in plugins/<pluginname>.dill
        :param name: Name of the data to store, used as a reference to retrieve it later
        :param data: data to be stored
        :return:    True, if data was successfully stored
                    False, if data could not be stored
        """

        self.plugin_data[name] = data
        return self.__save_data_to_file()

    def read_data(self, name: str) -> Any:
        """
        Read data from self.plugin_data
        :param name: Name of the data to be retrieved
        :return: the previously stored data
        """

        if name in self.plugin_data:
            return self.plugin_data[name]
        else:
            return None

    def clear_data(self, name: str) -> bool:
        """
        Clear a specific field in self.plugin_data
        :param name: name of the field to be cleared
        :return:    True, if successfully cleared
                    False, if name not contained in self.plugin_data or data could not be saved to disk
        """

        if name in self.plugin_data:
            del self.plugin_data[name]
            return self.__save_data_to_file()
        else:
            return False

    def __load_pickle_data_from_file(self, filename: str) -> Dict[str, Any]:
        """
        Load data from a pickle-file
        :param filename: filename to load data from
        :return: loaded data
        """

        file = open(filename, "rb")
        data = pickle.load(file)
        file.close()
        return data

    def __load_json_data_from_file(self, filename: str, convert: bool = False) -> Dict[str, Any]:
        """
        Load data from a json-file
        :param filename: filename to load data from
        :param convert: If data needs to be converted from single-file to directory-based
        :return: loaded data
        """

        file = open(filename, "r")
        json_data: str = file.read()
        if convert and f"\"py/object\": \"plugins.{self.name}.{self.name}." not in json_data:
            json_data = json_data.replace(f"\"py/object\": \"plugins.{self.name}.", f"\"py/object\": \"plugins.{self.name}.{self.name}.")
        data = jsonpickle.decode(json_data)

        return data

    def _load_data_from_file(self) -> Dict[str, Any]:
        """
        Load plugin_data from file
        :return: Data read from file to be loaded into self.plugin_data
        """

        plugin_data_from_json: Dict[str, Any] = {}
        plugin_data_from_pickle: Dict[str, Any] = {}
        abandoned_data: bool = False

        try:
            if os.path.isfile(self.plugin_dataj_filename):
                # local json data found
                plugin_data_from_json = self.__load_json_data_from_file(self.plugin_dataj_filename, convert=True)
                if os.path.isfile(self.plugin_data_filename):
                    logger.warning(f"Data for {self.name} read from {self.plugin_dataj_filename}, but {self.plugin_data_filename} still exists. After "
                                   f"verifying, that {self.name} is running correctly, please remove {self.plugin_data_filename}")

            elif os.path.isfile(self.plugin_data_filename):
                # local pickle-data found
                logger.warning(f"Reading data for {self.name} from pickle. This should only happen once. Data will be stored in new format.")
                plugin_data_from_pickle = self.__load_pickle_data_from_file(self.plugin_data_filename)

            else:
                # no local data found, check for abandoned data
                if self.is_directory_based:
                    abandoned_json_file: str = f"plugins/{self.name}.json"
                    if os.path.isfile(abandoned_json_file):
                        abandoned_data = True
                        logger.warning(f"Loading abandoned data for {self.name} from {abandoned_json_file}. This should only happen once.")
                        plugin_data_from_json = self.__load_json_data_from_file(abandoned_json_file, convert=True)

        except Exception as err:
            logger.critical(f"Could not load plugin_data for {self.name}: {err}")
            return {}

        if abandoned_data:
            if 'abandoned_json_file' in locals() and os.path.isfile(abandoned_json_file):
                logger.warning(f"You may remove {abandoned_json_file} now, it is no longer being used.")
            self.__save_data_to_json_file(plugin_data_from_json, self.plugin_dataj_filename)

        if plugin_data_from_pickle != {} and not os.path.isfile(self.plugin_dataj_filename):
            logger.warning(f"Converting data for {self.name} to {self.plugin_dataj_filename}. This should only happen once.")
            if os.path.isfile(self.plugin_data_filename):
                logger.warning(f"You may remove {self.plugin_data_filename} now, it is no longer being used.")

        if plugin_data_from_pickle != {}:
            return plugin_data_from_pickle
        elif plugin_data_from_json != {}:
            return plugin_data_from_json
        else:
            return {}

    def __save_data_to_pickle_file(self, data: Dict[str, Any], filename: str):
        """
        Save data to a pickle-file
        :param data: data to save
        :param filename: filename to save the data to
        :return:    True, if data stored successfully
                    False, otherwise
        """
        try:
            pickle.dump(data, open(filename, "wb"))
            return True
        except Exception as err:
            logger.critical(f"Could not write plugin_data to {self.plugin_data_filename}: {err}")
            return False

    def __save_data_to_json_file(self, data: Dict[str, Any], filename: str):
        """
        Save data to a json file
        :param data: data to save
        :param filename: filename to save the data to
        :return:    True, if data stored successfully
                    False, otherwise
        """

        try:
            json_data = jsonpickle.encode(data)
            file = open(filename, "w")
            file.write(json_data)
            file.close()
            return True
        except Exception as err:
            logger.critical(f"Could not write plugin_data to {self.plugin_data_filename}: {err}")
            return False

    def __save_data_to_file(self) -> bool:
        """
        Save modified plugin_data to disk
        :return:    True, if data stored successfully
                    False, otherwise
        """

        if self.plugin_data != {}:
            """there is actual data to save"""
            return self.__save_data_to_json_file(self.plugin_data, self.plugin_dataj_filename)

        else:
            """no data to save, remove file"""
            if os.path.isfile(self.plugin_data_filename):
                try:
                    remove(self.plugin_data_filename)
                    return True
                except Exception as err:
                    logger.critical(f"Could not remove file {self.plugin_data_filename}: {err}")
                    return False

    async def message(self, client, room_id, message: str, delay: int = 0) -> str or None:
        """
        Send a message to a room, usually utilized by plugins to respond to commands
        :param client: AsyncClient used to send the message
        :param room_id: room_id to send to message to
        :param message: the actual message
        :param delay: optional delay with typing notification, 1..1000ms
        :return: the event_id of the sent message or None in case of an error
        """

        if delay > 0:
            if delay > 1000:
                delay = 1000

            await client.room_typing(room_id, timeout=delay)
            await sleep(float(delay/1000))
            await client.room_typing(room_id, typing_state=False)

        event_response: RoomSendResponse
        event_response = await send_text_to_room(client, room_id, message, notice=False)

        if event_response:
            return event_response.event_id
        else:
            return None

    async def reply(self, command, message: str, delay: int = 0) -> str or None:
        """
        Simplified version of self.message() to reply to commands
        :param command: the command object passed by the message we're responding to
        :param message: the actual message
        :param delay: optional delay with typing notification, 1..1000ms
        :return: the event_id of the sent message or None in case of an error
        """

        return await self.message(command.client, command.room.room_id, message, delay)

    async def notice(self, client, room_id: str, message: str) -> str or None:
        """
        Send a notice to a room, usually utilized by plugins to post errors, help texts or other messages not warranting pinging users
        :param client: AsyncClient used to send the message
        :param room_id: room_id to send to message to
        :param message: the actual message
        :return: the event_id of the sent message or None in case of an error
        """

        event_response: RoomSendResponse
        event_response = await send_text_to_room(client, room_id, message, notice=True)

        if event_response:
            return event_response.event_id
        else:
            return None

    async def reply_notice(self, command, message: str) -> str or None:
        """
        Simplified version of self.notice() to reply to commands
        :param command: the command object passed by the message we're responding to
        :param message: the actual message
        :return: the event_id of the sent message or None in case of an error
        """

        return await self.notice(command.client, command.room.room_id, message)

    async def react(self, client, room_id: str, event_id: str, reaction: str):
        """
        React to a specific event
        :param client: (nio.AsyncClient) The client to communicate to matrix with
        :param room_id: (str) room_id to send the reaction to (is this actually being used?)
        :param event_id: (str) event_id to react to
        :param reaction: (str) the reaction to send
        :return:
        """

        await send_reaction(client, room_id, event_id, reaction)

    async def replace(self, client, room_id: str, event_id: str, message: str) -> str or None:
        """
        Edits an event. send_replace() will check if the new content actualy differs before really sending the replacement
        :param client: (nio.AsyncClient) The client to communicate to matrix with
        :param room_id: (str) room_id of the original event
        :param event_id: (str) event_id to edit
        :param message: (str) the new message
        :return:    (str) the event-id of the new room-event, if the original event has been replaced or
                    None, if the event has not been edited
        """

        return await send_replace(client, room_id, event_id, message)

    async def is_user_in_room(self, command, display_name: str, strictness: str = "loose", fuzziness: int = 75) -> RoomMember or None:
        """
        Try to determine if a diven displayname is currently a member of the room
        :param command:
        :param display_name: displayname of the user
        :param strictness: how strict to match the nickname
                            strict: exact match
                            loose: case-insensitive match (default)
                            fuzzy: fuzzy matching
        :param fuzziness: if strictness == fuzzy, fuzziness determines the required percentage for a match
        :return:    RoomMember matching the displayname if found,
                    None otherwise
        """

        client: AsyncClient = command.client
        room_members: JoinedMembersResponse = await client.joined_members(command.room.room_id)

        room_member: RoomMember

        if strictness == "strict" or strictness == "loose":
            for room_member in room_members.members:

                if strictness == "strict":
                    if room_member.display_name.lower() == display_name.lower():
                        return room_member

                else:
                    """loose matching"""
                    if room_member.display_name.lower() == display_name.lower():
                        return room_member
            else:
                return None

        else:
            """attempt fuzzy matching"""
            ratios: Dict[int, RoomMember] = {}
            for room_member in room_members.members:
                score: int
                if (score := fuzz.ratio(display_name.lower(), room_member.display_name.lower())) >= fuzziness:
                    ratios[score] = room_member

            if ratios != {}:
                return ratios[max(ratios.keys())]
            else:
                return None

    async def link_user(self, command, display_name: str, strictness: str = "loose", fuzziness: int = 75) -> str or None:
        """
        Given a displayname and a command, returns a userlink
        :param command:
        :param display_name: displayname of the user
        :param strictness: how strict to match the nickname
                            strict: exact match
                            loose: case-insensitive match (default)
                            fuzzy: fuzzy matching
        :param fuzziness: if strictness == fuzzy, fuzziness determines the required percentage for a match
        :return:    string with the userlink-html-code if found,
                    None otherwise
        """

        user: RoomMember
        if user := await self.is_user_in_room(command, display_name, strictness, fuzziness):
            return f"<a href=\"https://matrix.to/#/{user.user_id}\">{user.display_name}</a>"
        else:
            return None

    def add_config(self, config_item: str, default_value: Any = None, is_required: bool = False) -> bool:
        """
        Add a config value to be searched for in the plugin-specific configuration file upon loading, raise KeyError exception if required config_item can't be
        found
        :param config_item: the name of the configuration Item
        :param default_value: The value to use if the item is not specified in the configuration
        :param is_required: specify whether the configuration has to be present in the config-file for successful loading
        :return:    True, if the config_item is stored and not a duplicate
                    False, if the config_item already exists
        """

        if config_item in self.config_items.keys():
            logger.warning(f"{self.name}: Configuration item {config_item} has been defined already")
            return False
        else:
            # check for the value in configuration file and apply it if found
            if self.configuration and self.configuration.get(config_item):
                self.config_items[config_item] = self.configuration.get(config_item)

            # otherwise apply default
            elif default_value:
                self.config_items[config_item] = default_value

            # if no value and no default, but item is not required, set it to None
            elif not is_required:
                self.config_items[config_item] = None

            # no value, no default, and item is required
            else:
                err_str: str = f"Required configuration item {config_item} for plugin {self.name} could not be found"
                logger.warning(err_str)
                raise KeyError(err_str)

        return True

    def read_config(self, config_item: str) -> Any:
        """
        Read and return a specific value from the configuration
        If the actual value hasn't been read from the configuration, return the default value
        :param config_item: the name of the configuration item to look for
        :return:    The value of the requested config_item
                    None, if the value could not be found or does not have a default value defined
        """

        try:
            return self.config_items[config_item]
        except KeyError:
            return None

    def __load_config(self) -> Union[Dict[Hashable, Any], list, None] or None:
        """
        Load the plugins configuration from a .yaml-file. The filename needs to match the plugins name
        e.g. the configuration for sample has to be provided in sample.yaml
        :return:    result of yaml.safe_load, if the config file has been successfully read
                    None, if there was an error reading the configuration
        """

        if path.exists(self.config_items_filename):
            try:
                with open(self.config_items_filename) as file_stream:
                    return yaml.safe_load(file_stream.read())
            except OSError as err:
                logger.info(f"Error loading {self.config_items_filename}: {format(err)}")
                return None
        else:
            return None


class PluginCommand:

    def __init__(self, command: str, method: Callable, help_text: str, power_level, room_id: List[str]):
        self.command: str = command
        self.method: Callable = method
        self.help_text: str = help_text
        self.power_level: int = power_level
        self.room_id: List[str] = room_id


class PluginHook:

    def __init__(self, event_type: str, method: Callable, room_id: List[str]):
        self.event_type: str = event_type
        self.method: Callable = method
        self.room_id: List[str] = room_id
