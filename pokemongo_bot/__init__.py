# -*- coding: utf-8 -*-

from __future__ import print_function
from math import radians, sqrt, sin, cos, atan2
import datetime
import json
import logging
import random
import sys
import threading

import googlemaps

from pokemongo_bot import logger, cell_workers, human_behaviour, item_list, stepper
from pokemongo_bot.cell_workers import PokemonCatchWorker, SeenFortWorker, InitialTransferWorker, WalkTowardsFortWorker
from pokemongo_bot.cell_workers.utils import filtered_forts, distance
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.item_list import Item
from pokemongo_bot.stepper import Stepper
from pokemongo_bot.plugins import PluginManager
from pgoapi import PGoApi
from geopy.geocoders import GoogleV3


class PokemonGoBot(object):
    process_ignored_pokemon = False

    def __init__(self, config):
        self.config = config
        self.item_list = json.load(open('data/items.json'))
        self.pokemon_list = json.load(open('data/pokemon.json'))

        self.log = None
        self.stepper = None
        self.api = None
        self.inventory = []
        self.ignores = []
        self.position = (0, 0, 0)
        self.plugin_manager = None

    def _init_plugins(self):
        # create a plugin manager
        self.plugin_manager = PluginManager('./plugins', log=logger)

        # load all plugin modules
        for plugin in self.plugin_manager.get_available_plugins():
            self.plugin_manager.load_plugin(plugin)

    def start(self):
        self._setup_logging()
        self._setup_api()
        self._setup_ignored_pokemon()
        self._init_plugins()
        self.stepper = Stepper(self)
        random.seed()

    def take_step(self):
        self.stepper.take_step()

    def work_on_cell(self, cell, include_fort_on_path):
        self._remove_ignored_pokemon(cell)

        if (self.config.mode == "all" or self.config.mode == "poke") and 'catchable_pokemons' in cell and len(cell['catchable_pokemons']) > 0:
            logger.log('[#] Something rustles nearby!')
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            cell['catchable_pokemons'].sort(key=lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))

            user_web_catchable = 'web/catchable-%s.json' % (self.config.username)
            for pokemon in cell['catchable_pokemons']:
                with open(user_web_catchable, 'w') as outfile:
                    json.dump(pokemon, outfile)

                if self.catch_pokemon(pokemon) == PokemonCatchWorker.NO_POKEBALLS:
                    break
                with open(user_web_catchable, 'w') as outfile:
                    json.dump({}, outfile)

        if (self.config.mode == "all" or self.config.mode == "poke") and 'wild_pokemons' in cell and len(cell['wild_pokemons']) > 0:
            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            cell['wild_pokemons'].sort(key=lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
            for pokemon in cell['wild_pokemons']:
                if self.catch_pokemon(pokemon) == PokemonCatchWorker.NO_POKEBALLS:
                    break
        if include_fort_on_path:
            if 'forts' in cell:
                # Only include those with a lat/long
                forts = [fort for fort in cell['forts'] if 'latitude' in fort and 'type' in fort]
                # gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]

                # Sort all by distance from current pos- eventually this should
                # build graph & A* it
                forts.sort(key=lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
                for fort in forts:
                    walk_worker = WalkTowardsFortWorker(fort, self)
                    walk_worker.work()

                    if (self.config.mode == "all" or self.config.mode == "farm"):
                        spinner_worker = SeenFortWorker(fort, self)
                        spinner_worker.work()

    def catch_pokemon(self, pokemon):
        catch_worker = PokemonCatchWorker(pokemon, self)
        return_value = catch_worker.work()

        if return_value == PokemonCatchWorker.BAG_FULL:
            transfer_worker = InitialTransferWorker(self)
            transfer_worker.work()

        return return_value

    def _work_on_forts(self, position, map_cells):
        forts = filtered_forts(position[0], position[1], sum([cell.get("forts", []) for cell in map_cells], []))
        if forts:
            walk_worker = WalkTowardsFortWorker(forts[0], self)
            walk_worker.work()

            spinner_worker = SeenFortWorker(forts[0], self)
            spinner_worker.work()

    def _remove_ignored_pokemon(self, map_cells):
        if self.process_ignored_pokemon:
            try:
                for cell in map_cells:
                    for pokemon in cell['wild_pokemons'][:]:
                        pokemon_id = pokemon['pokemon_data']['pokemon_id']
                        pokemon_name = [x for x in self.pokemon_list if int(x.get('Number')) == pokemon_id][0]['Name']

                        if pokemon_name in self.ignores:
                            cell['wild_pokemons'].remove(pokemon)
            except KeyError:
                pass

            try:
                for cell in map_cells:
                    for pokemon in cell['catchable_pokemons'][:]:
                        pokemon_id = pokemon['pokemon_id']
                        pokemon_name = [x for x in self.pokemon_list if int(x.get('Number')) == pokemon_id][0]['Name']

                        if pokemon_name in self.ignores:
                            cell['catchable_pokemons'].remove(pokemon)
            except KeyError:
                pass

    def _work_on_catchable_pokemon(self, map_cells):
        for cell in map_cells:
            if 'catchable_pokemons' in cell and len(cell['catchable_pokemons']) > 0:
                logger.log('[#] Something rustles nearby!')
                # Sort all by distance from current pos- eventually this should
                # build graph & A* it
                cell['catchable_pokemons'].sort(
                    key=lambda x: distance(self.position[0], self.position[1], x['latitude'], x['longitude']))
                for pokemon in cell['catchable_pokemons']:
                    with open('web/catchable-%s.json' % (self.config.username), 'w') as outfile:
                        json.dump(pokemon, outfile)
                    worker = PokemonCatchWorker(pokemon, self)
                    if worker.work() == -1:
                        break
                    with open('web/catchable-%s.json' % (self.config.username), 'w') as outfile:
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

    def _setup_api(self):
        # instantiate pgoapi
        self.api = PGoApi()
        # provide player position on the earth

        self._set_starting_position()

        if not self.api.login(self.config.auth_service,
                              str(self.config.username),
                              str(self.config.password)):
            logger.log('Login Error, server busy', 'red')
            exit(0)

        # chain subrequests (methods) into one RPC call

        # get player profile call
        # ----------------------
        self.api.get_player()

        response_dict = self.api.call()
        # print('Response dictionary: \n\r{}'.format(json.dumps(response_dict, indent=2)))

        player = response_dict['responses']['GET_PLAYER']['player_data']

        # @@@ TODO: Convert this to d/m/Y H:M:S
        creation_date = datetime.datetime.fromtimestamp(
            player['creation_timestamp_ms'] / 1e3)

        balls_stock = self.pokeball_inventory()

        pokecoins = player['currencies'][0].get('amount', '0')
        stardust = player['currencies'][1].get('amount', '0')

        logger.log('[#]')
        logger.log('[#] Username: {username}'.format(**player))
        logger.log('[#] Acccount Creation: {}'.format(creation_date))
        logger.log('[#] Bag Storage: {}/{}'.format(
            self.get_inventory_count('item'), player['max_item_storage']))
        logger.log('[#] Pokemon Storage: {}/{}'.format(
            self.get_inventory_count('pokemon'), player[
                'max_pokemon_storage']))
        logger.log('[#] Stardust: {}'.format(stardust))
        logger.log('[#] Pokecoins: {}'.format(pokecoins))
        logger.log('[#] PokeBalls: {}'.format(balls_stock[1]))
        logger.log('[#] GreatBalls: {}'.format(balls_stock[2]))
        logger.log('[#] UltraBalls: {}'.format(balls_stock[3]))

        # Testing
        # self.drop_item(Item.ITEM_POTION.value,1)
        # exit(0)
        self.get_player_info()

        if self.config.initial_transfer:
            worker = InitialTransferWorker(self)
            worker.work()

        logger.log('[#]')
        self.update_inventory()

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
        self.api.recycle_inventory_item(item_id=item_id, count=count)
        self.api.call()

    def update_inventory(self):
        self.api.get_inventory()
        response = self.api.call()
        self.inventory = list()
        try:
            inventory_items = response['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
            for item in inventory_items:
                try:
                    item_data = item['inventory_item_data']['item']
                    if 'item_id' not in item_data or 'count' not in item_data:
                        continue
                    self.inventory.append(item_data)
                except KeyError:
                    pass
        except KeyError:
            pass

    def pokeball_inventory(self):
        self.api.get_player().get_inventory()

        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        with open('web/inventory-{}.json'.format(self.config.username), 'w') as outfile:
            json.dump(inventory_dict, outfile)

        # get player balls stock
        # ----------------------
        balls_stock = {Item.ITEM_POKE_BALL.value: 0,
                       Item.ITEM_GREAT_BALL.value: 0,
                       Item.ITEM_ULTRA_BALL.value: 0,
                       Item.ITEM_MASTER_BALL.value: 0}

        for item in inventory_dict:
            try:
                item_id = item['inventory_item_data']['item']['item_id']
                item_count = item['inventory_item_data']['item']['count']
                if item_id in balls_stock:
                    balls_stock[item_id] = item_count
            except KeyError:
                continue
        return balls_stock

    def _set_starting_position(self):

        if self.config.test:
            return

        if self.config.location_cache:
            try:
                #
                # save location flag used to pull the last known location from
                # the location.json
                with open('data/last-location-%s.json' % (self.config.username)) as last_location_file:
                    location_json = json.load(last_location_file)

                    self.position = (location_json['lat'], location_json['lng'], 0.0)
                    self.api.set_position(*self.position)

                    logger.log('')
                    logger.log('[x] Last location flag used. Overriding passed in location')
                    logger.log('[x] Last in-game location was set as: {}'.format(self.position))
                    logger.log('')

                    return
            except Exception:
                if not self.config.location:
                    sys.exit("No cached Location. Please specify initial location.")
                else:
                    pass

        #
        # this will fail if the location.json isn't there or not valid.
        # Still runs if location is set.
        self.position = self._get_pos_by_name(self.config.location)
        self.api.set_position(*self.position)
        logger.log('')
        logger.log(u'[x] Address found: {}'.format(self.config.location.decode(
            'utf-8')))
        logger.log('[x] Position in-game set as: {}'.format(self.position))
        logger.log('')

    def _get_pos_by_name(self, location_name):
        geolocator = GoogleV3(api_key=self.config.gmapkey)
        loc = geolocator.geocode(location_name, timeout=10)

        # self.log.info('Your given location: %s', loc.address.encode('utf-8'))
        # self.log.info('lat/long/alt: %s %s %s', loc.latitude, loc.longitude, loc.altitude)

        return (loc.latitude, loc.longitude, loc.altitude)

    def heartbeat(self):
        self.api.get_player()
        self.api.get_hatched_eggs()
        self.api.get_inventory()
        self.api.check_awarded_badges()
        self.api.call()

    def get_inventory_count(self, what):
        self.api.get_inventory()
        response_dict = self.api.call()

        pokecount = 0
        itemcount = 1
        try:
            inventory_items = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
            for item in inventory_items:
                # print('item {}'.format(item))
                if 'inventory_item_data' in item:
                    item_data = item['inventory_item_data']
                    if 'pokemon_data' in item_data:
                        pokecount += 1
                    if 'item' in item_data and 'count' in item_data['item']:
                        itemcount += item_data['item']['count']
        except KeyError:
            pass

        if 'pokemon' in what:
            return pokecount
        if 'item' in what:
            return itemcount
        return 0

    def get_player_info(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        try:
            inventory_items = response_dict['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
            for item in inventory_items:
                # print('item {}'.format(item))
                try:
                    player_stats = item['inventory_item_data']['player_stats']

                    if 'experience' not in player_stats:
                        player_stats['experience'] = 0

                    if 'level' in player_stats:
                        logger.log('[#] -- Level: {level}'.format(**player_stats))

                    if 'next_level_xp' in player_stats:
                        nextlvlxp = int(player_stats['next_level_xp']) - int(player_stats['experience'])
                        logger.log('[#] -- Experience: {experience}'.format(**player_stats))
                        logger.log('[#] -- Experience until next level: {}'.format(nextlvlxp))

                    if 'pokemons_captured' in player_stats:
                        logger.log('[#] -- Pokemon Captured: {pokemons_captured}'.format(**player_stats))

                    if 'poke_stop_visits' in player_stats:
                        logger.log('[#] -- Pokestops Visited: {poke_stop_visits}'.format(**player_stats))
                except KeyError:
                    pass
        except KeyError:
            pass
