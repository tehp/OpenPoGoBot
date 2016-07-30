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
from pokemongo_bot.cell_workers import PokemonCatchWorker, SeenFortWorker, InitialTransferWorker, WalkTowardsFortWorker, \
    RecycleItemsWorker
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
        self.item_list = json.load(open('data/items.json'))
        self.pokemon_list = json.load(open('data/pokemon.json'))

        self.log = None
        self.stepper = None
        self.api_wrapper = None
        self.ignores = []
        self.position = (0, 0, 0)
        self.plugin_manager = None
        self.last_session_check = time.gmtime()

    def _init_plugins(self):
        # create a plugin manager
        self.plugin_manager = PluginManager('./plugins', log=logger)

        # load all plugin modules
        for plugin in self.plugin_manager.get_available_plugins():
            if plugin not in self.config.exclude_plugins:
                self.plugin_manager.load_plugin(plugin)
            else:
                logger.log("Not loading plugin \"{}\"".format(plugin))

    def start(self):
        self._setup_logging()
        self._setup_api()
        self._setup_ignored_pokemon()
        self._init_plugins()
        self.stepper = Stepper(self)
        random.seed()

    def fire(self, event, *args, **kwargs):
        # type: (str, *Any, **Any) -> None
        manager.fire_with_context(event, self, *args, **kwargs)

    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, include_fort_on_path):
        # type: (Cell, bool) -> None

        self._remove_ignored_pokemon(cell)

        if self.config.mode in ["all", "poke"]:
            pass

        if (self.config.mode == "all" or self.config.mode == "poke") and len(cell.catchable_pokemon) > 0:
            logger.log('[#] Something rustles nearby!')
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            cell.catchable_pokemon.sort(key=lambda x: x.get("time_until_hidden_ms", 0))
            for pokemon in cell.catchable_pokemon:
                if self.catch_pokemon(pokemon) == PokemonCatchWorker.NO_POKEBALLS:
                    break

        if (self.config.mode == "all" or self.config.mode == "poke") and len(cell.wild_pokemon) > 0:
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            # cell.wild_pokemon.sort(key=lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
            cell.wild_pokemon.sort(key=lambda x: x.get("time_until_hidden_ms", 0))
            for pokemon in cell.wild_pokemon:
                if self.catch_pokemon(pokemon) == PokemonCatchWorker.NO_POKEBALLS:
                    break
        if include_fort_on_path:
            # Only include those with a lat/long
            pokestops = [pokestop for pokestop in cell.pokestops if
                         pokestop.latitude is not None and pokestop.longitude is not None]
            # gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]

            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            pokestops.sort(key=lambda x: distance(self.position[0], self.position[1], x.latitude, x.longitude))
            for pokestop in pokestops:
                walk_worker = WalkTowardsFortWorker(pokestop, self)
                walk_worker.work()

                if self.config.mode == "all" or self.config.mode == "farm":
                    spinner_worker = SeenFortWorker(pokestop, self)
                    spinner_worker.work()

    def catch_pokemon(self, pokemon):
        # type: (Pokemon) -> str
        catch_worker = PokemonCatchWorker(pokemon, self)
        return_value = catch_worker.work()

        if return_value == PokemonCatchWorker.BAG_FULL:
            transfer_worker = InitialTransferWorker(self)
            transfer_worker.work()

        return return_value

    def _work_on_forts(self, position, map_cells):
        # type: (Tuple[float, float], List[Cell]) -> None
        forts = filtered_forts(position[0], position[1], sum([cell.pokestops for cell in map_cells], []))
        if forts:
            walk_worker = WalkTowardsFortWorker(forts[0], self)
            walk_worker.work()

            spinner_worker = SeenFortWorker(forts[0], self)
            spinner_worker.work()

    def _remove_ignored_pokemon(self, cell):
        # type: (Cell) -> None
        if self.process_ignored_pokemon:
            wild_pokemons = cell.wild_pokemon
            catchable_pokemons = cell.catchable_pokemon
            for pokemon in wild_pokemons[:]:
                pokemon_id = pokemon['pokemon_data']['pokemon_id']
                pokemon_name = [x for x in self.pokemon_list if int(x.get('Number')) == pokemon_id][0]['Name']

                if pokemon_name in self.ignores:
                    wild_pokemons.remove(pokemon)

            for pokemon in catchable_pokemons[:]:
                pokemon_id = pokemon['pokemon_id']
                pokemon_name = [x for x in self.pokemon_list if int(x.get('Number')) == pokemon_id][0]['Name']

                if pokemon_name in self.ignores:
                    catchable_pokemons.remove(pokemon)

    def _work_on_catchable_pokemon(self, map_cells):
        # type: (List[Cell]) -> None
        for cell in map_cells:
            catchable_pokemon = cell.catchable_pokemon
            if len(catchable_pokemon) > 0:
                logger.log('[#] Something rustles nearby!')
                # Sort all by distance from current pos- eventually this should
                # build graph & A* it
                catchable_pokemon.sort(
                    key=lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
                for pokemon in catchable_pokemon:
                    with open('web/catchable-%s.json' % self.config.username, 'w') as outfile:
                        json.dump(pokemon, outfile)
                    worker = PokemonCatchWorker(pokemon, self)
                    if worker.work() == -1:
                        break
                    with open('web/catchable-%s.json' % self.config.username, 'w') as outfile:
                        json.dump({}, outfile)

    def _work_on_wild_pokemon(self, map_cells):
        for cell in map_cells:
            if 'wild_pokemons' in cell and len(cell['wild_pokemons']) > 0:
                # Sort all by distance from current pos- eventually this should
                # build graph & A* it
                cell['wild_pokemons'].sort(
                    key=lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
                for pokemon in cell['wild_pokemons']:
                    worker = PokemonCatchWorker(pokemon, self)
                    if worker.work() == -1:
                        break

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
            logger.log('[#] Bag Storage: {}/{}'.format(len(inventory), player.max_item_storage))
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
            worker = InitialTransferWorker(self)
            worker.work()

        if self.config.recycle_items:
            recycle_worker = RecycleItemsWorker(self)
            recycle_worker.work()

        logger.log('[#]')
        self.update_player_and_inventory()

    def print_player_data(self, player):
        # @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(player['creation_timestamp_ms'] / 1e3)

        balls_stock = self.pokeball_inventory()

        pokecoins = player['currencies'][0].get('amount', '0')
        stardust = player['currencies'][1].get('amount', '0')

        logger.log('[#]')
        logger.log('[#] Username: {username}'.format(**player))
        logger.log('[#] Account Creation: {}'.format(creation_date))
        logger.log('[#] Bag Storage: {}/{}'.format(self.get_item_count(), player['max_item_storage']))
        logger.log('[#] Pokemon Storage: {}/{}'.format(self.get_pokemon_count(), player['max_pokemon_storage']))
        logger.log('[#] Stardust: {}'.format(stardust))
        logger.log('[#] Pokecoins: {}'.format(pokecoins))
        logger.log('[#] PokeBalls: {}'.format(balls_stock[1]))
        logger.log('[#] GreatBalls: {}'.format(balls_stock[2]))
        logger.log('[#] UltraBalls: {}'.format(balls_stock[3]))

    def _setup_ignored_pokemon(self):
        pass
        # try:
        #     with open("./data/catch-ignore.yml", 'r') as ignore_file:
        #         self.ignores = yaml.load(ignore_file)['ignore']
        #         if len(self.ignores) > 0:
        #             self.process_ignored_pokemon = True
        # except Exception:
        #     pass

    def drop_item(self, item_id, count):
        self.api_wrapper.recycle_inventory_item(item_id=item_id, count=count)
        self.api_wrapper.call()

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
        return len(response_dict["inventory"])
