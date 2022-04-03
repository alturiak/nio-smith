# Plugin: coingecko

Crypto Currency price related commands. Utilizes the free [CoinGeckoAPI](https://www.coingecko.com/en/api)

## Commands

### cgprice

Usage: `cgprice <coin> [<versus_currency>]`  
Fetches the latest price data for `<coin>` in `<versus_currency>` (defaults to `eur` if not specified in config or command)

### cgdetails

Usage: `cgdetails <coin>`  
Fetches latest price in eur, usd and satoshi for `<coin>` aswell as price and market cap change over the last 24h

## Configuration

Configuration options in `coingecko.yaml`

- `default_versus_currency`: default versus currency to use if nothing was specified in the `cgprice` command. If not set in config, this will default to `eur`. A full list of available versus_currencies can be found [via the CoinGeckoAPI endpoint](https://api.coingecko.com/api/v3/simple/supported_vs_currencies)

## External Requirements

- pycoingecko^=2.2.0
