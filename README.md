# OpenPoGoBot
[![Build Status](https://travis-ci.org/OpenPoGo/OpenPoGoBot.svg?branch=master)](https://travis-ci.org/OpenPoGo/OpenPoGoBot)

  A quick note:
  
  This is a fork of the project [PokemonGo-Bot](https://github.com/PokemonGoF/PokemonGo-Bot) by [PokemonGoF](https://github.com/PokemonGoF).
  
  The goal of this fork is to progress the bot in an organized manner, and to promote a clean and functional codebase. As a result, OpenPoGoBot will be more reliable and secure than PokemonGo-Bot.

--------

## Table of Contents
- [Contributing](#contributing)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [FAQ](#faq)
- [Plugins](#plugins)

## Contributing
See [CONTRIBUTING.md](https://github.com/OpenPoGo/OpenPoGoBot/blob/master/CONTRIBUTING.md)

## Features
 * Spin Pokestops
 * Catch Pokemon
 * Release low cp pokemon
 * Walk to a location
 * Catch nearby pokemon when you have pokeballs available
 * Switch between catching pokemon and farming pokestops automatically
 * Filter certain pokemon
 * Use superior ball types when necessary
 * When out of normal pokeballs, use the next type of ball unless there are less than 10 of that type, in which case start automatically farming pokestops
 * Bot Navigation via Google Directions API


## Installation

### Requirements

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Optional)
- [protobuf 3](https://github.com/google/protobuf) (OS Dependent, see below)

### Protobuf 3 installation

- OS X:  `brew update && brew install --devel protobuf`
- Windows: Download protobuf 3.0: [here](https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip) and unzip `bin/protoc.exe` into a folder in your PATH.
- Linux: `apt-get install python-protobuf`


### Install
```
git clone --recursive https://www.github.com/OpenPoGo/OpenPoGoBot
cd OpenPoGoBot
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

## Usage

```
$ python pokecli.py [flags]
```

####  Flags
| Flag                          | Short Flag         | Description                                                                                                                                                                 |
|-------------------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| --help                        | -h                 | Show this help message and exit                                                                                                                                             |
| --config-json                 | -j                 | Load a config JSON file. Any arguments specified on command line override those specified in the file.                                                                      |
| --auth-service [AUTH_SERVICE] | -a [AUTH_SERVICE]  | Auth Service ('ptc' or 'google')                                                                                                                                            |
| --username [USERNAME]         | -u [USERNAME]      | Username                                                                                                                                                                    |
| --password [PASSWORD]         | -p [PASSWORD]      | Password                                                                                                                                                                    |
| --location [LOCATION]         | -l [LOCATION]      | Location (Address or 'xx.yyyy,zz.ttttt')                                                                                                                                    |
| --location-cache              | -lc                | Bot will start at last known location                                                                                                                                       |
| --walk [SPEED]                | -w [SPEED]         | Walk instead of teleport with given speed (meters per second max 4.16 because of walking end on 15km/h)                                                                     |
| --distance-unit [UNIT]        | -du [UNIT]         | Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)                                                                                     |
| --initial-transfer            | -it                | Start the bot with a pokemon clean up, keeping only the higher CP of each pokemon. It respects -c as upper limit to release.                                                |
| --ign-init-trans [LIST]       | -ig [LIST]         | Pass a list of pokemon to ignore during initial transfer (e.g. 017,049,001)                                                                                                 |
| --max-steps [MAX_STEP]        | -ms [MAX_STEP]     | Set the steps around your initial location (DEFAULT 5 mean 25 cells around your location)                                                                                   |
| --combat-power [COMBAT_POWER] | -cp [COMBAT_POWER] | Transfer Pokemon that have CP less than this value (default 100)",                                                                                                          |
| --pokemon-potential [IV]      | -iv [IV]           | Set the ratio for the IV values to transfer (DEFAULT 0.4 eg. 0.4 will transfer a pokemon with IV 0.3)                                                                       |
| --recycle-items               | -ri                | Recycle unneeded items automatically                                                                                                                                        |
| --exclude-plugins [LIST]      | -ep [LIST]         | Pass a list of plugins to exclude from the loading process (e.g, logger,web).                                                                                               |
| --gmapkey [KEY]               | -k [KEY]           | Set a google maps API key to use                                                                                                                                            |
| --google-directions           | -gd                | Bot will use directions from google maps API to navigate                                                                                                                    |
| --debug                       | -d                 | Debug Mode                                                                                                                                                                  |
| --test                        | -t                 | Only parse the specified location                                                                                                                                           |
| --fill-incubators             | -fi                | Fill incubators with eggs                                                                                                                                                   |
| --use-all-incubators          | -ai                | Use all incubators or only unlimited one                                                                                                                                    |


### Command Line Example
Pokemon Trainer Club (PTC) account:
```
$ python2 pokecli.py -a ptc -u tejado -p 1234 --location "New York, Washington Square"
```
Google Account:
```
$ python2 pokecli.py -a google -u tejado -p 1234 --location "New York, Washington Square"
```

### Bot Configuration via JSON
To load arguments for the bot from a JSON file, use the ``--config-json`` argument with the name of a file.
Any other command line arguments specified will override the parameters specified in the loaded JSON file.

Example - this will load config.json but use cp=1000 and iv=0.7 even if already defined in config.json:
```
$ python2 pokecli.py --config-json config.json -cp 1000 -iv 0.7
```

### JSON Options


### Advance Releasing Configuration
To edit the pokemon release configuration, copy the file ``release_config.json.example`` and rename it to ``release_config.json``

Edit this file however you want, but keep in mind:

1. Pokemon names should always be capitalized and are case-sensitive
2. The ``any`` configuration effects every pokemon
   

## FAQ

### What's IV ?
Here's the [introduction](http://bulbapedia.bulbagarden.net/wiki/Individual_values)
### Losing Starter Pokemon and others
You can use -cp 1 to protect your first stage low CP pokemon.
### Set GEO Location
Use either `-l "lat, long"` or `--location "lat, long"` 
### Google login issues (Login Error, Server busy)?

Try to generate an [app password](!https://support.google.com/accounts/answer/185833?hl=en) and set is as
```
-p "<your-app-password>"
```
This error is mostly occurs for those who using 2 factor authentication but either way for the purpose of security would be nice to have a separate password for the bot app.


### FLEE
The status code "3" corresponds to "Flee" - meaning your Pokemon has ran away.
   {"responses": { "CATCH_POKEMON": { "status": 3 } }
### Why aren't my pokemon showing up in my Pokedex?
Finish the tutorial on a smartphone. This will then allow everything to be visible.
### Where's `--mode`/`-m`?
Now, instead of using `--mode` you need to exclude plugins. If you don't want to catch pokemon, exclude the `catch_pokemon` plugin  (`-ep catch_pokemon`), and if you don't want to farm pokestops just exclude the `spin_pokestop` plugin (`-ep spin_pokestop`). Alternatively, you can modify your configuration JSON file to do the same thing.

### How can I have the bot ignore certain pokemon?
Create the following filter
```
./data/catch-ignore.yml
```
Its a yaml file with a list of names so make it look like
```
ignore:
  - Pidgey
  - Rattata
  - Pidgeotto
  - Spearow
  - Ekans
  - Zubat
```
### How do I use the map?

The web plugin uses `Flask` to open a server on port `8000`. Before visiting the site, you will need to set your username(s) in the `userdata.js` file:

1. Copy `userdata.js.example` to `userdata.js` 
2. Open the `userdata.js` file in your editor.
3. Edit the the username to match yours.
4. Change other settings if you want.
5. Browse `http://localhost:8000` and enjoy!

If you are using multiple usernames, the format is like this:  
```
var users = ["username1","username2"];
```

---------

## Plugins
Here are the available plugins:

|     **Plugins**    |
|:------------------:|
| `catch_pokemon`    |
| `recycle_items`    |
| `spin_pokestop`    |
| `transfer_pokemon` |
| `web`              |


## Credits
- [tejado](https://github.com/tejado) for the API
- [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets
- [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
- [AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos
- [AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff
- [PokemonGoF](https://github.com/PokemonGoF/PokemonGo-bot) and all contributors for the original bot this fork is based on
