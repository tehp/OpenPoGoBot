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
    usage: pokecli.py [-h] -a AUTH_SERVICE -u USERNAME -p PASSWORD -l LOCATION [-lc] [-c] [-m] [-w] [--distance_unit] [--initial-transfer] [--maxsteps] [-cp] [-iv] [-d] [-t]

    optional arguments:
      -h, --help                                    Show this help message and exit
      -j, --config-json                             Load a config JSON file. Any arguments specified on command line override those specified in the file.
      -a AUTH_SERVICE, --auth-service AUTH_SERVICE  Auth Service ('ptc' or 'google')
      -u USERNAME, --username USERNAME              Username
      -p PASSWORD, --password PASSWORD              Password
      -l LOCATION, --location LOCATION              Location (Address or 'xx.yyyy,zz.ttttt')
      -lc, --location-cache                         Bot will start at last known location
      -m MODE, --mode MODE                          Set farming Mode for the bot ('all', 'poke', 'farm')
      -w SPEED,  --walk SPEED                       Walk instead of teleport with given speed (meters per second max 4.16 because of walking end on 15km/h)
      -du UNIT, --distance-unit UNIT                Set the unit to display distance in (e.g, km for kilometers, mi for miles, ft for feet)
      -it, --initial-transfer                       Start the bot with a pokemon clean up, keeping only the higher CP of each pokemon. It respects -c as upper limit to release.
      -ig LIST, --ign-init-trans LIST               Pass a list of pokemon to ignore during initial transfer (e.g. 017,049,001)
      -ms MAX_STEP, --max-steps MAX_STEP            Set the steps around your initial location (DEFAULT 5 mean 25 cells around your location)
      -cp COMBAT_POWER, --combat-power COMBAT_POWER Transfer Pokemon that have CP less than this value (default 100)",
      -iv IV, --pokemon-potential IV                Set the ratio for the IV values to transfer (DEFAULT 0.4 eg. 0.4 will transfer a pokemon with IV 0.3)
      -ri, --recycle-items                          Recycle unneeded items automatically
      -if LIST, --item-filter LIST                  Pass a list of unwanted items to recycle when collected at a Pokestop (e.g, [\"101\",\"102\",\"103\",\"104\"] to recycle potions when collected). Requires --recycle-items. 
      -ep LIST, --exclude-plugins LIST              Pass a list of plugins to exclude from the loading process (e.g, logger,web).
      -k KEY, --gmapkey KEY                         Set a google maps API key to use
      -d, --debug                                   Debug Mode
      -t, --test                                    Only parse the specified location

### Command Line Example
    Pokemon Trainer Club (PTC) account:
    $ python2 pokecli.py -a ptc -u tejado -p 1234 --location "New York, Washington Square"
    Google Account:
    $ python2 pokecli.py -a google -u tejado -p 1234 --location "New York, Washington Square"

### Bot Configuration via JSON
    To load arguments for the bot from a JSON file, use the ``--config-json`` argument with the name of a file.
    Any other command line arguments specified will override the parameters specified in the loaded JSON file.

    Example - this will load config.json but use cp=1000 and iv=0.7 even if already defined in config.json:
    $ python2 pokecli.py --config-json config.json -cp 1000 -iv 0.7

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
### How do I use the map??
You can either view the map via opening the html file, or by serving it with SimpleHTTPServer (runs on localhost:8000)  
To use SimpleHTTPServer:  
```$ python -m SimpleHTTPServer [port]```
The default port is 8080, you can change that by giving a port number.
Anything above port 1000 does not require root.
You will need to set your username(s) in the userdata.js file before opening:  
Copy userdata.js.example to userdata.js and edit with your favorite text editor.
put your username in the quotes instead of "username"
If using multiple usernames format like this:  
```var users = ["username1","username2"];```

---------



## Credits
- [tejado](https://github.com/tejado) for the API
- [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets
- [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
- [AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos
- [AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff
- [PokemonGoF](https://github.com/PokemonGoF/PokemonGo-bot) and all contributors for the original bot this fork is based on
