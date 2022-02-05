Plugin: pick
===
Pick a random item from a given list of items.  
Ported from Hydralisk/Pyrate. Original author: [Dingo](https://matrix.to/#/@dingo:pack.rocks).

## Commands

### pick
Usage: `pick <list of items> [:<message to add to result>]`  
Pick an item from the list and respond with a random or the supplied message.  

Example: simply pick between two options   
user: `!pick python, java`  
bot: `Result: python`  

Example: pick between two options and respond with the given message  
user: `!pick python, java: is the better programming language for my project`  
bot: `python is the better programming language for my project`  

Example: pick between two options and place the pick at a certain place in the response  
user: `!pick , not: python is %s useful`  
bot: `python is useful`

## Configuration
- none

## External Requirements
- none
