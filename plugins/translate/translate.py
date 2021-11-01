# -*- coding: utf8 -*-
from core.plugin import Plugin
from nio import AsyncClient, RoomMessageText
from re import sub
from typing import List, Dict
import logging
from freetranslate.googletranslate import GoogleTranslate

logger = logging.getLogger(__name__)
plugin = Plugin("translate", "General", "Provide translations of all room-messages via Google Translate")


def setup():
    # Change settings in translate.yaml if required
    plugin.add_config("allowed_rooms", [], is_required=False)
    plugin.add_config("min_power_level", 50, is_required=False)
    plugin.add_config("default_source", ['any'], is_required=False)
    plugin.add_config("default_dest", 'en', is_required=False)
    plugin.add_config("default_bidirectional", False, is_required=False)

    plugin.add_command("translate", switch, "`translate [[bi] source_lang... dest_lang]` - translate text from one or more source_lang to dest_lang",
                       room_id=plugin.read_config("allowed_rooms"),
                       power_level=plugin.read_config("min_power_level"))


"""
roomsdb = {
    room_id: {
        "source_langs": ['any']
        "dest_lang": 'en'
        "bidirectional": False
    }
}
"""

LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'he': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
}


async def switch(command):
    """
    Enable or disable translations
    :param command:
    :return:
    """

    rooms_db: Dict[str, Dict[str, any]] = {}

    if await plugin.read_data("rooms_db"):
        rooms_db = await plugin.read_data("rooms_db")

    if len(command.args) == 0:
        source_langs: List[str] = plugin.read_config("default_source")
        dest_lang: str = plugin.read_config("default_dest")
        bidirectional: bool = plugin.read_config("default_bidirectional")

    else:
        try:
            if command.args[0] == 'bi':
                bidirectional = True
                source_langs = [command.args[1]]
                dest_lang = command.args[2]
            else:
                bidirectional = False
                source_langs = command.args[:-1]
                dest_lang = command.args[-1]
        except IndexError:
            await plugin.respond_notice(command, "Syntax: `!translate [[bi] source_lang... dest_lang]`")
            return False

    if plugin.has_hook("m.room.message", translate_message, [command.room.room_id]):
        plugin.del_hook("m.room.message", translate_message, room_id_list=[command.room.room_id])
        del rooms_db[command.room.room_id]
        await plugin.store_data("rooms_db", rooms_db)
        await plugin.respond_notice(command, "Translations disabled")

    elif plugin.read_config("allowed_rooms") == [] or command.room.room_id in plugin.read_config("allowed_rooms"):
        if dest_lang in LANGUAGES.keys() and source_langs == ['any'] or all(elem in LANGUAGES.keys() for elem in source_langs):
            rooms_db[command.room.room_id] = {"source_langs": source_langs, "dest_lang": dest_lang, "bidirectional": bidirectional}
            await plugin.store_data("rooms_db", rooms_db)
            plugin.add_hook("m.room.message", translate_message, room_id_list=[command.room.room_id], hook_type="dynamic")

            if bidirectional:
                message = f"Bidirectional translations ({source_langs[0]}<=>{dest_lang}) enabled.  \n"

            else:
                message = f"Unidirectional translations ({str(source_langs)}=>{dest_lang}) enabled.  \n"

            message += f"**ATTENTION**: *ALL* future messages in this room will be sent to Google Translate until disabled again."
            await plugin.respond_notice(command, message)
        else:
            await plugin.respond_notice(command, f"Invalid language specified.")


async def translate_message(client: AsyncClient, room_id: str, event: RoomMessageText):
    """
    Translate a received message is translation is active on room and language message matches defined source-languages
    :param client:
    :param room_id:
    :param event:
    :return:
    """

    rooms_db: Dict[str, Dict[str, any]] = {}

    if await plugin.read_data("rooms_db"):
        rooms_db = await plugin.read_data("rooms_db")

    if plugin.read_config("allowed_rooms") == [] or room_id in plugin.read_config("allowed_rooms"):
        # Remove special characters before translation
        message = sub(r'[^A-z0-9\-\.\?!:\sÄäÜüÖö]+', '', event.body)

        # Replace line breaks by spaces as freetrans doesn't seem to handle them
        message = message.replace("\n", " ")
        googletrans = GoogleTranslate()

        try:
            logger.debug(f"Detecting language for message: {message}")
            message_source_lang: str = await googletrans.detect(message)

        except Exception:
            del rooms_db[room_id]
            await plugin.store_data("rooms_db", rooms_db)
            plugin.del_hook("m.room.message", translate_message, room_id_list=[room_id])
            await plugin.send_notice(client, room_id, "Error in backend translation module. Translations disabled.")
            return

        if rooms_db[room_id]["bidirectional"]:
            languages: List[str] = [rooms_db[room_id]["source_langs"][0], rooms_db[room_id["dest_lang"]]]

            if message_source_lang in languages:
                languages.remove(message_source_lang)
                dest_lang = languages[0]
                translated = (await googletrans.translate(message, dest_lang)).translated_text
                await plugin.send_notice(client, room_id, translated)

        else:
            if message_source_lang != rooms_db[room_id]["dest_lang"] and \
                    (rooms_db[room_id]["source_langs"] == ['any'] or message_source_lang in rooms_db[room_id]["source_langs"]):
                translated = (await googletrans.translate(message, rooms_db[room_id]["dest_lang"])).translated_text
                await plugin.send_notice(client, room_id, translated)


setup()
