# OpenPoGoBot
[![Build Status](https://travis-ci.org/OpenPoGo/OpenPoGoBot.svg?branch=master)](https://travis-ci.org/OpenPoGo/OpenPoGoBot)
[![Build status](https://ci.appveyor.com/api/projects/status/2w4vvuyto0cos54r/branch/master?svg=true)](https://ci.appveyor.com/project/wchill/openpogobot/branch/master)
[![codecov](https://codecov.io/gh/OpenPoGo/OpenPoGoBot/branch/master/graph/badge.svg)](https://codecov.io/gh/OpenPoGo/OpenPoGoBot)
[![Dependency Status](https://www.versioneye.com/user/projects/57ac766d89a974004123d9f4/badge.svg?style=flat-square)](https://www.versioneye.com/user/projects/57ac766d89a974004123d9f4)

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
 * Incubate eggs

## Installation

### Requirements

- [Python 2.7.x](http://docs.python-guide.org/en/latest/starting/installation/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) (Optional)
- `encrypt` shared library (OS Dependent, see below)
- [protobuf 3](https://github.com/google/protobuf) (OS Dependent, see below)

### `Encrypt` shared library

With the changes to the API on 3 August 2016, API map requests are required to have a `Signature` field in the request body. This requires that the `encrypt` shared library is in the bot directory, as it is needed to encrypt one of the fields.

You will need to either find `encrypt.c` or the appropriate shared library for your system. The bot will automatically attempt to load the following filenames; another filename can be specified using config options as described below.
We can not distribute `encrypt.c` for legal reasons. Check [pgoapi.com](http://pgoapi.com/).

- OS X: `libencrypt-darwin.so`
- Windows: `encrypt.dll`
- Linux: `libencrypt.so`

To build the shared library for Windows, run `lib/build_dll.bat`, rename the resulting binary to `encrypt.dll` and move to the bot folder.

To build the shared library for OS X or Linux, in the `lib` folder run `make`, rename the resulting binary as needed and move to the bot folder.

Note that if you are running a 32-bit version of Python, you must have a 32-bit version of the library, and vice versa for 64-bit. On Windows, failure to do so will result in `WindowsError: [Error 193] %1 is not a valid Win32 application`.

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
$ python pokecli.py [path to config yml]
```

__What happened to the command line arguments?!__
The command line arguments have been removed in favour of yml config files.

### Command Line Example
```
$ python pokecli.py config/config.yml
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

#### Socket Plugin

The socket plugin exposes a server on port `8000` that allow communication to your browser.
Once launched, just to to [http://openpogoui.nicontoso.eu](http://openpogoui.nicontoso.eu) to show progress on a map.
You can then click on settings (lower right) to modify map settings.  

---------

### Plugins
Here are the available plugins:

|     **Plugins**    |
|:------------------:|
| `catch_pokemon`    |
| `egg_incubator`    |
| `recycle_items`    |
| `spin_pokestop`    |
| `transfer_pokemon` |
| `socket`           |


## Testing
Please see the [testing documentation](docs/testing.md) on how to run and write the tests.

## Credits
- [tejado](https://github.com/tejado) for the API
- [Mila432](https://github.com/Mila432/Pokemon_Go_API) for the login secrets
- [elliottcarlson](https://github.com/elliottcarlson) for the Google Auth PR
- [AeonLucid](https://github.com/AeonLucid/POGOProtos) for improved protos
- [AHAAAAAAA](https://github.com/AHAAAAAAA/PokemonGo-Map) for parts of the s2sphere stuff
- [PokemonGoF](https://github.com/PokemonGoF/PokemonGo-bot) and all contributors for the original bot this fork is based on
- [/r/PokemonGoDev](https://github.com/keyphact/pgoapi) and all reverse engineering contributors for fixes for the new API changes
