Plugin: translate
===
Provide translations of all room-messages via Google Translate (using 
[freetranslate](https://pypi.org/project/freetranslate/0.2.0/), may break randomly)

## Commands

### translate
Usage: `translate [[bi] source_lang... dest_lang]`  
Toggle translation of all following messages in the room via Google Translate.  

Example: Enable translation using default values (or disable active translation):  
`translate`

Example: Bidirectional translation between german and english:  
`translate bi de en`

Example: Unidirectional translation from german and english to japanese:
`translate de en jp`

## Configuration
Sensible defaults can be provided in `translate.yaml`:  
- `allowed_rooms`: List of room-id the plugin is allowed to work in (if empty, all rooms are allowed)  
- `min_power_level`: minimum power level to activate translation (default: 50)
- `default_source`: list of default source language(s) to translate messages from,
if not specified when using `translate` (default: ['any'])  
- `default_dest`: default destination language to translate messages from, if not specified when using `translate` 
(default: en)  
- `default_bidirectional`: default to bidirectional translation, if not specified when using !translate (default: 
  False)  

## External Requirements
- [freetranslate](https://pypi.org/project/freetranslate/0.2.0/) for language detection and the actual translation
