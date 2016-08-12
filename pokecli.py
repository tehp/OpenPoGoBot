#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

from __future__ import print_function

import logging
import ssl
import sys

import colorama
import ruamel.yaml
from pgoapi import PGoApi

from app import service_container
from pokemongo_bot import logger
from pokemongo_bot.event_manager import manager
from pokemongo_bot.plugins import PluginManager

# Disable HTTPS certificate verification
if sys.version_info >= (2, 7, 9):
    # pylint: disable=protected-access
    ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore


def init_config():
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config', 'config.yml')
    if len(sys.argv) >= 2:
        if sys.argv[1][0] == '-':
            print("Command line arguments are deprecated. See README for details.")
            print("Usage: pokecli.py [path to config.yml]")
            exit(1)
        config_path = sys.argv[2]

    if not os.path.isfile(config_path):
        print("{} does not exist.".format(config_path))
        exit(1)

    with open(config_path, 'r') as config_file:
        config = ruamel.yaml.load(config_file.read(), ruamel.yaml.RoundTripLoader)
        return config


def main():
    # log settings
    # log format
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

    colorama.init()

    config = init_config()
    if not config:
        return

    logger.log('[x] PokemonGO Bot v1.0', 'green')
    logger.log('[x] Configuration initialized', 'yellow')

    try:
        service_container.register_singleton('config', config)
        service_container.register_singleton('pgoapi', PGoApi())
        service_container.register_singleton('plugin_manager', PluginManager('./plugins'))
        service_container.register_singleton('event_manager', manager)

        if config.path_finder in ['google', 'direct']:
            service_container.set_parameter('path_finder', config.path_finder)
        else:
            raise Exception('You must provide a path finder')

        if config.navigator in ['fort', 'waypoint', 'camper']:
            service_container.set_parameter('navigator', config.navigator)
        else:
            raise Exception('You must provide a navigator')

        #log = logging.getLogger(__name__)
        # bot = PokemonGoBot(config, api_wrapper, player_service, pokemon_service, plugin_manager, event_manager, mapper, stepper, navigator, log)
        bot = service_container.get('pokemongo_bot')
        bot.start()

        logger.log('[x] Starting PokemonGo Bot....', 'green')

        while True:
            bot.run()

    except KeyboardInterrupt:
        logger.log('[x] Exiting PokemonGo Bot', 'red')


if __name__ == '__main__':
    main()
