# -*- coding: utf-8 -*-

from __future__ import print_function
import json
import logging
import random
import sys
import time

import googlemaps
from googlemaps.exceptions import ApiError

from app import service_container
from pokemongo_bot import logger, human_behaviour, item_list
from pokemongo_bot.utils import filtered_forts, distance
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.plugins import PluginManager
from pokemongo_bot.navigation import FortNavigator, WaypointNavigator, CamperNavigator
from geopy import geocoders


# Uncomment for type annotations on Python 3
# from typing import Any, List, Dict, Union, Tuple
# from api.pokemon import Pokemon
# from api.worldmap import Cell

@service_container.register('pokemongo_bot', ['@config', '@api_wrapper', '@player_service', '@pokemon_service', '@plugin_manager', '@event_manager', '@mapper', '@stepper', '%navigator%'])
class PokemonGoBot(object):
    process_ignored_pokemon = False

    def __init__(self, config, api_wrapper, player_service, pokemon_service, plugin_manager, event_manager, mapper, stepper, navigator):
        # type: (Namespace, PoGoApi, Player, Pokemon, PluginManager, EventManager, Mapper, Stepper, Navigator) -> None
        self.config = config
        self.api_wrapper = api_wrapper
        self.player_service = player_service
        self.pokemon_service = pokemon_service
        self.plugin_manager = plugin_manager
        self.event_manager = event_manager
        self.mapper = mapper
        self.stepper = stepper
        self.navigator = navigator

        self.pokemon_list = json.load(open('data/pokemon.json'))
        self.item_list = {}
        for item_id, item_name in json.load(open('data/items.json')).items():
            self.item_list[int(item_id)] = item_name

        self.position = (0.0, 0.0, 0.0)
        self.last_session_check = time.gmtime()

    def start(self):
        self._setup_logging()
        self._setup_plugins()
        self._setup_api()
        random.seed()

        self.stepper.start(*self.position)

        self.fire('bot_initialized')

        logger.log('[#]')
        self.player_service.update()

    def _setup_logging(self):
        # log settings
        # log format
        logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

        if self.config["debug"]:
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("pgoapi").setLevel(logging.DEBUG)
            logging.getLogger("rpc_api").setLevel(logging.DEBUG)
        else:
            logging.getLogger("requests").setLevel(logging.ERROR)
            logging.getLogger("pgoapi").setLevel(logging.ERROR)
            logging.getLogger("rpc_api").setLevel(logging.ERROR)

    def _setup_plugins(self):
        # load all plugin modules
        for plugin in self.plugin_manager.get_available_plugins():
            if plugin not in self.config["plugins"]["exclude"]:
                self.plugin_manager.load_plugin(plugin)
            else:
                logger.log("Not loading plugin \"{}\"".format(plugin), color="red", prefix="Plugins")

        loaded_plugins = sorted(self.plugin_manager.get_loaded_plugins().keys())
        sleep(2)
        logger.log("Plugins loaded: {}".format(loaded_plugins), color="green", prefix="Plugins")
        if self.config["debug"]:
            logger.log("Events available: {}".format(self.event_manager.get_registered_events()), color="green", prefix="Events")
            self.event_manager.print_all_event_pipelines()

    def _setup_api(self):
        # provide player position on the earth
        self._set_starting_position()

        while not self.player_service.login():
            logger.log('Login Error, server busy', 'red')
            logger.log('Waiting 15 seconds before trying again...')
            time.sleep(15)

        logger.log('[+] Login to Pokemon Go successful.', 'green')

        self.player_service.print_stats()

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

            destination.set_steps(
                self.stepper.get_route_between(
                    position_lat,
                    position_lng,
                    destination.target_lat,
                    destination.target_lng,
                    destination.target_alt
                )
            )

            self.fire("walking_started",
                      coords=(destination.target_lat, destination.target_lng, destination.target_alt))

            for step in self.stepper.step(destination):
                self.fire("position_updated", coordinates=step)
                self.heartbeat()

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

    def add_candies(self, name=None, pokemon_candies=None):
        for pokemon in self.pokemon_list:
            if pokemon['Name'] is not name:
                continue
            else:
                previous_evolutions = pokemon.get("Previous evolution(s)", [])
                if previous_evolutions:
                    candy_name = previous_evolutions[0]['Number']
                else:
                    candy_name = pokemon.get("Number")

                if self.candies.get(candy_name, None) is not None:
                    self.candies[candy_name] += pokemon_candies
                else:
                    self.candies[candy_name] = pokemon_candies
                logger.log("[#] Added {} candies for {}".format(pokemon_candies,
                                                                self.pokemon_list[int(candy_name) - 1]['Name']),
                           'green')
                break

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

                    logger.log('')
                    logger.log('[x] Last location flag used. Overriding passed in location')
                    logger.log('[x] Last in-game location was set as: {}'.format(self.position))
                    logger.log('')

                    return
            except IOError:
                if not self.config["mapping"]["location"]:
                    sys.exit("No cached Location. Please specify initial location.")
                else:
                    self._read_config_location()
        else:
            self._read_config_location()

        logger.log('[x] Position in-game set as: {}'.format(self.position))
        logger.log('')

    def _read_config_location(self):
        self.position = self._get_pos_by_name(self.config["mapping"]["location_cache"])
        self.api_wrapper.set_position(*self.position)
        logger.log('')
        logger.log(u'[x] Address found: {}'.format(self.config["mapping"]["location_cache"]))

    def _get_pos_by_name(self, location_name):
        # type: (str) -> Tuple[float, float, float]
        if location_name.count(',') == 1:
            try:
                logger.log("[x] Fetching altitude from google")
                parts = location_name.split(',')

                pos_lat = float(parts[0])
                pos_lng = float(parts[1])

                # we need to ask google for the altitude
                gmaps = googlemaps.Client(key=self.config["mapping"]["gmapkey"])
                response = gmaps.elevation((pos_lat, pos_lng))

                if len(response) and "elevation" in response[0]:
                    return pos_lat, pos_lng, response[0]["elevation"]
                else:
                    raise ValueError
            except ApiError:
                logger.log("[x] Could not fetch altitude from google. Trying geolocator.")
            except ValueError:
                logger.log("[x] Location was not Lat/Lng.")

        # Fallback to geolocation if no Lat/Lng can be found
        geolocator = geocoders.GoogleV3(api_key=self.config["mapping"]["gmapkey"])
        loc = geolocator.geocode(location_name, timeout=10)

        # self.log.info('Your given location: %s', loc.address.encode('utf-8'))
        # self.log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

        return loc.latitude, loc.longitude, loc.altitude

    def heartbeat(self):
        self.api_wrapper.get_player()
        self.api_wrapper.get_hatched_eggs()
        self.api_wrapper.get_inventory()
        self.api_wrapper.check_awarded_badges()
        self.api_wrapper.call()

    def get_username(self):
        # type: () -> str
        player = self.player_service.get_player()
        if player is None:
            return "Unknown"
        return player.username

    def get_position(self):
        return self.position
