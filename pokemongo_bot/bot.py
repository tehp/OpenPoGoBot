# -*- coding: utf-8 -*-

from __future__ import print_function
import json
import logging
import random
import sys
import time

from app import kernel
from pokemongo_bot.navigation.path_finder import DirectPathFinder, GooglePathFinder
from pokemongo_bot.service import Player, Pokemon
from pokemongo_bot.utils import filtered_forts, distance
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.mapper import Mapper
from pokemongo_bot.stepper import Stepper
from pokemongo_bot.event_manager import EventManager
from pokemongo_bot.navigation import CamperNavigator, FortNavigator, WaypointNavigator


# Uncomment for type annotations on Python 3
# from typing import Any, List, Dict, Union, Tuple
# from api.pokemon import Pokemon
# from api.worldmap import Cell

@kernel.container.register('pokemongo_bot', ['@config.core', '@api_wrapper', '@player_service', '@pokemon_service', '@event_manager', '@mapper', '@stepper', '%navigator%', '@logger'])
class PokemonGoBot(object):
    process_ignored_pokemon = False

    def __init__(self, config, api_wrapper, player_service, pokemon_service, event_manager, mapper, stepper, navigator, logger):
        # type: (Namespace, PoGoApi, Player, Pokemon, EventManager, Mapper, Stepper, Navigator, Logger) -> None
        self.config = config
        self.api_wrapper = api_wrapper
        self.player_service = player_service
        self.pokemon_service = pokemon_service
        self.event_manager = event_manager
        self.mapper = mapper
        self.stepper = stepper
        self.navigator = navigator
        self.logger = logger

        self.pokemon_list = json.load(open('data/pokemon.json'))
        self.item_list = {}
        for item_id, item_name in json.load(open('data/items.json')).items():
            self.item_list[int(item_id)] = item_name

        self.position = (0.0, 0.0, 0.0)
        self.last_session_check = time.gmtime()

        self.logger.log('[x] PokemonGO Bot v1.0', color='green')
        self.logger.log('[x] Configuration initialized', color='yellow')

    def start(self):
        self._setup_logging()
        self._setup_api()
        random.seed()

        self.stepper.start(*self.position)

        self.player_service.print_stats()

        self.fire('bot_initialized')

        self.player_service.update()

    def _setup_logging(self):
        # log settings
        # log format
        logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

        if self.config['debug']:
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("pgoapi").setLevel(logging.DEBUG)
            logging.getLogger("rpc_api").setLevel(logging.DEBUG)
        else:
            logging.getLogger("requests").setLevel(logging.ERROR)
            logging.getLogger("pgoapi").setLevel(logging.ERROR)
            logging.getLogger("rpc_api").setLevel(logging.ERROR)

    def _setup_api(self):
        # provide player position on the earth
        self._set_starting_position()

        while not self.player_service.login():
            self.logger.log('Login Error, server busy', color='red')
            self.logger.log('Waiting 15 seconds before trying again...')
            time.sleep(15)

        self.logger.log('[+] Login to Pokemon Go successful.', color='green')

    def run(self):
        map_cells = self.mapper.get_cells(
            self.stepper.current_lat,
            self.stepper.current_lng
        )

        # Work on all the initial cells
        self.work_on_cells(map_cells)

        for destination in self.navigator.navigate(map_cells):
            position_lat = self.stepper.current_lat
            position_lng = self.stepper.current_lng

            steps = self.stepper.get_route_between(
                position_lat,
                position_lng,
                destination.target_lat,
                destination.target_lng,
                destination.target_alt
            )
            destination.set_steps(steps)

            self.fire("route", route=steps)

            self.fire("walking_started",
                      coords=(destination.target_lat, destination.target_lng, destination.target_alt))

            for step in self.stepper.step(destination):
                self.fire("position_updated", coordinates=step)
                self.player_service.heartbeat()

                self.work_on_cells(
                    self.mapper.get_cells(
                        self.stepper.current_lat,
                        self.stepper.current_lng
                    )
                )

            self.fire("walking_finished",
                      coords=(destination.target_lat, destination.target_lng, destination.target_alt))

    def work_on_cells(self, map_cells):
        # type: (Cell, bool) -> None
        encounters = []
        pokestops = []
        for cell in map_cells:
            encounters += cell.catchable_pokemon + cell.wild_pokemon
            pokestops += cell.pokestops

        if len(encounters):
            self.fire("pokemon_found", encounters=encounters)
        if len(pokestops):
            self.fire("pokestops_found", pokestops=pokestops)

    def fire(self, event, *args, **kwargs):
        # type: (str, *Any, **Any) -> None
        self.event_manager.fire_with_context(event, self, *args, **kwargs)

    def _set_starting_position(self):
        if self.config["mapping"]["location_cache"]:
            try:
                #
                # save location flag used to pull the last known location from
                # the location.json
                with open('data/last-location-%s.json' % self.config["login"]["username"]) as last_location_file:
                    location_json = json.load(last_location_file)

                    self.position = (location_json['lat'], location_json['lng'], 0.0)
                    self.api_wrapper.set_position(*self.position)

                    self.logger.log('')
                    self.logger.log('[x] Last location flag used. Overriding passed in location')
                    self.logger.log('[x] Last in-game location was set as: {}'.format(self.position))
                    self.logger.log('')

                    return
            except IOError:
                if not self.config["mapping"]["location"]:
                    sys.exit("No cached Location. Please specify initial location.")

        # Fallback to location in configuration
        self.position = self.mapper.find_location(self.config["mapping"]["location"])
        self.api_wrapper.set_position(*self.position)
        self.logger.log('')
        self.logger.log(u'[x] Address found: {}'.format(self.config["mapping"]["location"]))
        self.logger.log('[x] Position in-game set as: {}'.format(self.position))
        self.logger.log('')

    def get_username(self):
        # type: () -> str
        player = self.player_service.get_player()
        if player is None:
            return "Unknown"
        return player.username
