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

import os
import ssl
import sys

import colorama

# Disable HTTPS certificate verification
from app import kernel
from pokemongo_bot.bot import PokemonGoBot

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
        config_path = sys.argv[1]

    if not os.path.isfile(config_path):
        print("{} does not exist.".format(config_path))
        exit(1)

    return config_path


def main():
    # log settings
    # log format
    # logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

    colorama.init()

    config_dir = init_config()
    if not config_dir:
        return

    kernel.set_config_file(config_dir)
    kernel.boot()

    try:
        bot = kernel.container.get('pokemongo_bot')
        bot.start()

        while True:
            bot.run()

    except KeyboardInterrupt:
        logger = kernel.container.get('logger')
        logger.log('[x] Exiting PokemonGo Bot', 'red')


if __name__ == '__main__':
    main()
