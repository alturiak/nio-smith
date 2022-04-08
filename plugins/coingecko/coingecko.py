from core.plugin import Plugin
import logging
from core.bot_commands import Command

from pycoingecko import CoinGeckoAPI

logger = logging.getLogger(__name__)

plugin = Plugin("coingecko", "CryptoCurrency", "Get data from the Coingecko API")


def setup():
    plugin.add_command(
        "cgprice",
        cgprice_command,
        "fetch price for coin [default in eur €]",
    )
    plugin.add_command("cgdetails", cgdetails_command, "get details for coin")


class CoinNotFound(BaseException):
    def __init__(self, msg: str):
        self.message = msg + " [List of supported coins](https://api.coingecko.com/api/v3/coins/list). Use `symbol` if its the only option without spaces"


class VersusCurrencyNotFound(BaseException):
    def __init__(self, msg: str):
        self.message = msg + " [List of supported versus currencies](https://api.coingecko.com/api/v3/simple/supported_vs_currencies)"


class Coingecko:
    def __init__(self):
        plugin.add_config(config_item="default_versus_currency", default_value="eur")
        self.api = CoinGeckoAPI()
        self.default_versus_currency = plugin.read_config(config_item="default_versus_currency")

    async def validate_coin(self, coin: str, retry: bool = True) -> str:
        """
        validates/normalizes the coin to the corresponding coingecko coin_id and returns it\n
        recursively tries to find valid coin in local store before sending a new api request\n
        raises CoinNotFound
        """
        available_coins_list = await plugin.read_data("available_coins_list")
        if not available_coins_list:
            available_coins_list = self.api.get_coins_list()
            await plugin.store_data("available_coins_list", available_coins_list)
            retry = False
        # available_coins_list = list(filter(lambda coin: not "binance-peg" in coin["id"], available_coins_list))
        available_coins_list = [c for c in available_coins_list if "binance-peg" not in c["id"]]
        if coin not in [coin["id"] for coin in available_coins_list]:
            if coin not in [coin["name"].lower() for coin in available_coins_list]:
                if coin not in [coin["symbol"].lower() for coin in available_coins_list]:
                    if retry:
                        await plugin.store_data("available_coins_list", self.api.get_coins_list())
                        return await self.validate_coin(coin, False)
                    else:
                        raise CoinNotFound(f"Coin '{coin}' not found.")
                else:
                    coin = next(filter(lambda c: c["symbol"].lower() == coin, available_coins_list))["id"]
            else:
                coin = next(filter(lambda c: c["name"].lower() == coin, available_coins_list))["id"]
        return coin

    async def validate_versus_currency(self, versus_currency: str, retry: bool = True) -> str:
        """
        validates the versus currency and returns it\n
        recursively tries to find valid versus_currency in local store before sending a new api request\n
        raises VersusCurrencyNotFound
        """
        available_versus_currencies = await plugin.read_data("available_versus_currencies")
        if not available_versus_currencies:
            available_versus_currencies = self.api.get_supported_vs_currencies()
            await plugin.store_data("available_versus_currencies", available_versus_currencies)
            retry = False
        if versus_currency not in available_versus_currencies:
            if retry:
                await plugin.store_data("available_versus_currencies", self.api.get_supported_vs_currencies())
                return await self.validate_versus_currency(versus_currency, False)
            else:
                raise VersusCurrencyNotFound(f"versus currency '{versus_currency}' not found")
        return versus_currency

    async def get_price_for_coin(self, coin: str, versus_currency: str) -> float:
        coin = await self.validate_coin(coin)
        versus_currency = await self.validate_versus_currency(versus_currency)
        return self.api.get_price(coin, versus_currency)[coin][versus_currency]

    async def get_chart_for_coin(self, coin: str) -> str:
        coin = await self.validate_coin(coin)
        coin_infos: dict = self.api.get_coin_by_id(coin)
        coin_name = coin_infos["name"]
        coin_symbol = coin_infos["symbol"]
        coin_rank = coin_infos["market_cap_rank"]
        homepage = coin_infos["links"]["homepage"][0]
        price_euro = coin_infos["market_data"]["current_price"]["eur"]
        price_usd = coin_infos["market_data"]["current_price"]["usd"]
        price_sats = coin_infos["market_data"]["current_price"]["sats"]
        price_change_24h = coin_infos["market_data"]["price_change_24h"]
        price_change_percentage_24h = coin_infos["market_data"]["price_change_percentage_24h"]
        market_cap_change_24h = coin_infos["market_data"]["market_cap_change_24h"]
        market_cap_change_percentage_24h = coin_infos["market_data"]["market_cap_change_percentage_24h"]

        if price_change_24h >= 0:
            price_change_color = "green"
            price_change_emoji = "📈"
            price_change_plus = "+"
        else:
            price_change_color = "red"
            price_change_emoji = "📉"
            price_change_plus = ""

        if market_cap_change_24h >= 0:
            market_cap_change_color = "green"
            market_cap_change_emoji = "📈"
            market_cap_change_plus = "+"
        else:
            market_cap_change_color = "red"
            market_cap_change_emoji = "📉"
            market_cap_change_plus = ""

        if not "e" in str(price_euro) and "." in str(price_euro):
            price_euro = round(price_euro, len([c for c in str(price_euro).split(".")[1] if c == "0"]) + 2)
        if not "e" in str(price_usd) and "." in str(price_usd):
            price_usd = round(price_usd, len([c for c in str(price_usd).split(".")[1] if c == "0"]) + 2)
        if not "e" in str(price_sats) and "." in str(price_sats):
            price_sats = round(price_sats, len([c for c in str(price_sats).split(".")[1] if c == "0"]) + 2)

        return (
            f"<div><b><a href='{homepage}'>{coin_name}</a></b><br />"
            + f"{coin_symbol} | rank#{coin_rank}"
            + "</div><div>Price:<ul>"
            + f"<li>Euro: {price_euro}€</li>"
            + f"<li>Dollar: ${price_usd}</li>"
            + f"<li>Satoshi: {price_sats} sats</li>"
            + "</ul></div><div>"
            + "Price change (last 24h):<br />"
            + f"<font color='{price_change_color}'>{price_change_plus}${price_change_24h} | "
            + f"{price_change_plus}{round(price_change_percentage_24h, 2)}% |</font> {price_change_emoji}"
            + "</div><div>"
            + "Market Cap change (last 24h):<br />"
            + f"<font color='{market_cap_change_color}'>{market_cap_change_plus}${market_cap_change_24h} | "
            + f"{market_cap_change_plus}{round(market_cap_change_percentage_24h, 2)}% |</font> {market_cap_change_emoji}"
            + "</div>"
        )


CG = Coingecko()


async def cgprice_command(command: Command):
    if not command.args:
        return await plugin.respond_notice(command, "Usage: `cgprice <coin> [<versus_currency>]`")

    coin: str = command.args[0]
    versus_currency: str = CG.default_versus_currency if len(command.args) < 2 else command.args[1]
    try:
        response = f"1 {coin} = {await CG.get_price_for_coin(coin.lower(), versus_currency.lower())} {versus_currency}"
    except (CoinNotFound, VersusCurrencyNotFound) as exception:
        response = exception.message

    await plugin.respond_message(command, response)


async def cgdetails_command(command: Command):
    if not command.args:
        return await plugin.respond_message(command, "Usage: `cgdetails <coin>`")
    try:
        res = await CG.get_chart_for_coin(command.args[0].lower())
    except CoinNotFound as exception:
        res = exception.message
    await plugin.respond_message(command, res)


setup()
