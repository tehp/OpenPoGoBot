# -*- coding: utf-8 -*-

from __future__ import print_function
import datetime
import json
import logging
import random
import sys
import time

import googlemaps
from googlemaps.exceptions import ApiError

from pokemongo_bot import logger, cell_workers, human_behaviour, item_list, stepper
from pokemongo_bot.event_manager import manager
from pokemongo_bot.cell_workers import WalkTowardsFortWorker
from pokemongo_bot.utils import filtered_forts, distance, convert_to_utf8
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.stepper import Stepper
from pokemongo_bot.plugins import PluginManager
from api import PoGoApi
from geopy.geocoders import GoogleV3  # type: ignore
# Uncomment for type annotations on Python 3
# from typing import Any, List, Dict, Union, Tuple
# from api.pokemon import Pokemon
# from api.worldmap import Cell


class PokemonGoBot(object):
    process_ignored_pokemon = False

    def __init__(self, config):
        self.config = config
        self.pokemon_list = json.load(open('data/pokemon.json'))
        self.item_list = {}
        for item_id, item_name in json.load(open('data/items.json')).iteritems():
            self.item_list[int(item_id)] = item_name

        self.log = None
        self.stepper = None
        self.api_wrapper = None
        self.ignores = []
        self.position = (0, 0, 0)
        self.plugin_manager = None
        self.last_session_check = time.gmtime()

    def _init_plugins(self):
        # create a plugin manager
        self.plugin_manager = PluginManager('./plugins')

        # load all plugin modules
        for plugin in self.plugin_manager.get_available_plugins():
            if plugin not in self.config.exclude_plugins:
                self.plugin_manager.load_plugin(plugin)
            else:
                logger.log("Not loading plugin \"{}\"".format(plugin))

        loaded_plugins = sorted(self.plugin_manager.get_loaded_plugins().keys())
        logger.log("Plugins loaded: {}".format(loaded_plugins), color="green", prefix="Plugins")
        logger.log("Events available: {}".format(manager.get_registered_events()), color="green", prefix="Events")

    def start(self):
        self._setup_logging()
        self._init_plugins()
        self._setup_api()
        self._setup_ignored_pokemon()
        self.stepper = Stepper(self)
        random.seed()

    def fire(self, event, *args, **kwargs):
        # type: (str, *Any, **Any) -> None
        manager.fire_with_context(event, self, *args, **kwargs)

    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, pokemon_only):
        # type: (Cell, bool) -> None

        self.fire("pokemon_found", encounters=cell.catchable_pokemon + cell.wild_pokemon)

        if not pokemon_only:
            # TODO: Refactor WalkTowardsFortWorker
            # self.fire("pokestops_found", pokestops=cell.pokestops)

            pokestops = filtered_forts(self.position[0], self.position[1], cell.pokestops)

            for pokestop in pokestops:
                walk_worker = WalkTowardsFortWorker(pokestop, self)
                walk_worker.work()

                self.fire("pokestop_arrived", pokestop=pokestop)

    def _setup_logging(self):
        self.log = logging.getLogger(__name__)
        # log settings
        # log format
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(module)10s] [%(levelname)5s] %(message)s')

        if self.config.debug:
            logging.getLogger("requests").setLevel(logging.DEBUG)
            logging.getLogger("pgoapi").setLevel(logging.DEBUG)
            logging.getLogger("rpc_api").setLevel(logging.DEBUG)
        else:
            logging.getLogger("requests").setLevel(logging.ERROR)
            logging.getLogger("pgoapi").setLevel(logging.ERROR)
            logging.getLogger("rpc_api").setLevel(logging.ERROR)

    @staticmethod
    def same_minute(current_time, last_time):

        # Time Structure
        # (tm_year=2016, tm_mon=7, tm_mday=28, tm_hour=9, tm_min=26, tm_sec=57, tm_wday=3, tm_yday=210, tm_isdst=0)

        current_time_list = [
            current_time.tm_year,
            current_time.tm_mon,
            current_time.tm_mday,
            current_time.tm_hour,
            current_time.tm_min
        ]

        last_time_list = [
            last_time.tm_year,
            last_time.tm_mon,
            last_time.tm_mday,
            last_time.tm_hour,
            last_time.tm_min
        ]
        return bool(current_time_list == last_time_list)

    def _setup_api(self):
        # instantiate api
        self.api_wrapper = PoGoApi(provider=self.config.auth_service, username=self.config.username,
                                   password=self.config.password)
        # provide player position on the earth

        self._set_starting_position()

        while not self.api_wrapper.login():
            logger.log('Login Error, server busy', 'red')
            logger.log('Waiting 15 seconds before trying again...')
            time.sleep(15)

        logger.log('[+] Login to Pokemon Go successful.', 'green')

        # chain subrequests (methods) into one RPC call

        # get player profile call
        # ----------------------
        response_dict = self.update_player_and_inventory()

        if response_dict is not None:
            player = response_dict['player']
            inventory = response_dict['inventory']
            pokemon = response_dict['pokemon']
            creation_date = player.get_creation_date()

            balls_stock = self.pokeball_inventory()

            pokecoins = player.pokecoin
            stardust = player.stardust

            logger.log('[#]')
            logger.log('[#] Username: {}'.format(player.username))
            logger.log('[#] Acccount Creation: {}'.format(creation_date))
            logger.log('[#] Bag Storage: {}/{}'.format(inventory["count"], player.max_item_storage))
            logger.log('[#] Pokemon Storage: {}/{}'.format(len(pokemon), player.max_pokemon_storage))
            logger.log('[#] Stardust: {}'.format(stardust))
            logger.log('[#] Pokecoins: {}'.format(pokecoins))
            logger.log('[#] PokeBalls: {}'.format(balls_stock[1]))
            logger.log('[#] GreatBalls: {}'.format(balls_stock[2]))
            logger.log('[#] UltraBalls: {}'.format(balls_stock[3]))
            logger.log('[#] -- Level: {}'.format(player.level))
            logger.log('[#] -- Experience: {}'.format(player.experience))
            logger.log('[#] -- Experience until next level: {}'.format(player.next_level_xp - player.experience))
            logger.log('[#] -- Pokemon Captured: {}'.format(player.pokemons_captured))
            logger.log('[#] -- Pokestops Visited: {}'.format(player.poke_stop_visits))
        # Testing
        # self.drop_item(Item.ITEM_POTION.value,1)
        # exit(0)

        if self.config.initial_transfer:
            self.fire("pokemon_bag_full")

        if self.config.recycle_items:
            self.fire("item_bag_full")

        logger.log('[#]')
        self.update_player_and_inventory()

    def _setup_ignored_pokemon(self):
        pass
        # try:
        #     with open("./data/catch-ignore.yml", 'r') as ignore_file:
        #         self.ignores = yaml.load(ignore_file)['ignore']
        #         if len(self.ignores) > 0:
        #             self.process_ignored_pokemon = True
        # except Exception:
        #     pass

    def update_player_and_inventory(self):
        # type: () -> Dict[str, object]
        self.api_wrapper.get_player().get_inventory()
        return self.api_wrapper.call()

    def pokeball_inventory(self):
        balls_stock = {Item.ITEM_POKE_BALL.value: 0,
                       Item.ITEM_GREAT_BALL.value: 0,
                       Item.ITEM_ULTRA_BALL.value: 0,
                       Item.ITEM_MASTER_BALL.value: 0}

        result = self.api_wrapper.get_inventory().call()
        if result is None:
            return balls_stock

        inventory_list = result["inventory"]

        for item_id in inventory_list:
            if item_id in balls_stock:
                balls_stock[item_id] = inventory_list[item_id]
        return balls_stock

    def _set_starting_position(self):

        if self.config.test:
            return

        if self.config.location_cache:
            try:
                #
                # save location flag used to pull the last known location from
                # the location.json
                with open('data/last-location-%s.json' % self.config.username) as last_location_file:
                    location_json = json.load(last_location_file)

                    self.position = (location_json['lat'], location_json['lng'], 0.0)
                    self.api_wrapper.set_position(*self.position)

                    logger.log('')
                    logger.log('[x] Last location flag used. Overriding passed in location')
                    logger.log('[x] Last in-game location was set as: {}'.format(self.position))
                    logger.log('')

                    return
            except IOError:
                if not self.config.location:
                    sys.exit("No cached Location. Please specify initial location.")
                else:
                    self._read_config_location()
        else:
            self._read_config_location()

        logger.log('[x] Position in-game set as: {}'.format(self.position))
        logger.log('')

    def _read_config_location(self):
        self.position = self._get_pos_by_name(self.config.location)
        self.api_wrapper.set_position(*self.position)
        logger.log('')
        logger.log(u'[x] Address found: {}'.format(self.config.location))

    def _get_pos_by_name(self, location_name):
        # type: (str) -> Tuple[float, float, float]
        if location_name.count(',') == 1:
            try:
                logger.log("[x] Fetching altitude from google")
                parts = location_name.split(',')

                pos_lat = float(parts[0])
                pos_lng = float(parts[1])

                # we need to ask google for the altitude
                gmaps = googlemaps.Client(key=self.config.gmapkey)
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
        geolocator = GoogleV3(api_key=self.config.gmapkey)
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

    def get_pokemon_count(self):
        # type: () -> int
        response_dict = self.update_player_and_inventory()
        if response_dict is None:
            return 0
        return len(response_dict["pokemon"])

    def get_item_count(self):
        # type: () -> int
        response_dict = self.update_player_and_inventory()
        if response_dict is None:
            return 0
        return response_dict["inventory"]["count"]
