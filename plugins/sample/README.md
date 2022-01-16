Plugin: sample
===
Collection of several sample commands to illustrate usage and maybe serve as a plugin template. The commands enabled 
by this plugin don't serve any actual purpose.

## Commands

### sample
Usage: `sample`  
A simple sample command, producing a simple sample output

### sample_store
Usage: `sample_store <message to store>`  
Store a message persistently

### sample_read
Usage: `sample_read`  
Read the stored message

### sample_clear
Usage: `sample_clear`  
Clear the stored message

### sample_link_user
Usage: `sample_link_user <username>`  
Given a displayname, try to produce a userlink

### sample_reaction_test
Usage: `sample_reaction_test`  
Post a message and record reactions to this message

### sample_react
Usage: `sample_react`  
Post reactions to a command

### sample_replace
Usage: `sample_replace`  
Post a message and edit it afterwards

### sample_add_command
Usage: `sample_add_command`  
Dynamically adds an active command `sample_remove_command`

### sample_remove_command
Usage: `sample_remove_command`  
Remove the command added by `sample_add_command`

### sample_sleep
Usage: `sample_sleep`
Sleep for five seconds, then post a message, to test parallel execution of commands

### sample_send_image
Usage: `sample_send_image`  
Generate a small image and post it

### sample_fetch_image
Usage: `sample_fetch_image`
Fetch a test image and post it

### sample_list_servers_on_room
Usage: `sample_list_servers_on_room`  
List servers on current room

### sample_list_rooms_for_server
Usage: `sample_count_rooms_for_server`  
Post a count of rooms shared with users on a given server

## Configuration
Configuration options in `sample.yaml`  
- `default_message`: a string to read from the configuration when `read_configuration` command is used (default: "this is the default message")

## External Requirements
- none
