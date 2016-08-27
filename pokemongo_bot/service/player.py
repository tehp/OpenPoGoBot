import os
from datetime import date
import json

from app import kernel
from pokemongo_bot.item_list import Item
from pokemongo_bot.human_behaviour import sleep


@kernel.container.register('player_service', ['@api_wrapper', '@event_manager', '@logger'])
class Player(object):
    def __init__(self, api_wrapper, event_manager, logger):
        self._api_wrapper = api_wrapper
        self._event_manager = event_manager
        self._logger = logger
        self._logged_in = False

        self._eggs = None
        self._egg_incubators = []
        self._candies = {}
        self._pokeballs = {
            Item.ITEM_POKE_BALL.value: 0,
            Item.ITEM_GREAT_BALL.value: 0,
            Item.ITEM_ULTRA_BALL.value: 0,
            Item.ITEM_MASTER_BALL.value: 0
        }
        self._player = None
        self._inventory = None
        self._pokemon = None

    def login(self):
        self._logged_in = self._api_wrapper.login()
        return self._logged_in

    def init(self):
        # mimic app
        self._api_wrapper.get_player()
        # self._api_wrapper.check_challenge()
        self._api_wrapper.call()

        self._api_wrapper.download_remote_config_version(plateform="IOS", app_version=3300)
        self._api_wrapper.get_inventory()
        self._api_wrapper.check_awarded_badges()
        self._api_wrapper.download_settings()
        # self._api_wrapper.check_challenge()
        self._api_wrapper.get_hatched_eggs()
        response_dict = self._api_wrapper.call()
        item_template_update = response_dict["DOWNLOAD_REMOTE_CONFIG_VERSION"]["item_templates_timestamp_ms"]

        self._api_wrapper.get_asset_digest(plateform="IOS", app_version=3300)
        self._api_wrapper.get_inventory()
        # self._api_wrapper.check_challenge()
        self._api_wrapper.check_awarded_badges()
        self._api_wrapper.download_settings()
        self._api_wrapper.get_hatched_eggs()
        self._api_wrapper.call()

        self.get_item_templates(item_template_update)

    def update(self, do_sleep=True):
        self._api_wrapper.get_inventory()
        # self._api_wrapper.check_challenge()
        self._api_wrapper.check_awarded_badges()
        self._api_wrapper.get_hatched_eggs()
        self._api_wrapper.download_settings()

        response_dict = self._api_wrapper.call()

        if do_sleep:
            sleep(2)

        if response_dict is None:
            self._log('Failed to retrieve player and inventory stats', color='red')
            return False

        self._player = self._api_wrapper.get_player_cache()

        self._inventory = response_dict['inventory']
        self._candies = response_dict['candy']
        self._pokemon = response_dict['pokemon']
        self._candies = response_dict['candy']
        self._eggs = response_dict['eggs']
        self._egg_incubators = response_dict['egg_incubators']

        for item_id in self._inventory:
            if item_id in self._pokeballs:
                self._pokeballs[item_id] = self._inventory[item_id]

        self._event_manager.fire('service_player_updated', data=self)

        return True

    def get_item_templates(self, timestamp=None):
        item_templates = None
        if timestamp is not None:
            last = 0
            if os.path.isfile("data/item_templates.json"):
                with open('data/item_templates.json') as data_file:
                    item_templates = json.load(data_file)
                    last = item_templates["timestamp_ms"]

            if last < timestamp:
                self._api_wrapper.download_item_templates()
                self._api_wrapper.get_hatched_eggs()
                self._api_wrapper.check_challenge()
                self._api_wrapper.get_inventory()
                self._api_wrapper.check_awarded_badges()
                self._api_wrapper.download_settings()
                response_dict = self._api_wrapper.call()
                item_templates = response_dict["DOWNLOAD_ITEM_TEMPLATES"]
                with open('data/item_templates.json', 'w') as outfile:
                    json.dump(item_templates, outfile)

        if item_templates is None and os.path.isfile("data/item_templates.json"):
            with open('data/item_templates.json') as data_file:
                item_templates = json.load(data_file)

        item_templates = item_templates["item_templates"] if item_templates is not None else None
        return item_templates

    def get_player(self):
        self.update()
        return self._player

    def get_inventory(self):
        self.update()
        return self._inventory

    def get_eggs(self):
        self.update()
        return self._eggs

    def get_egg_incubators(self):
        self.update()
        return self._egg_incubators

    def get_pokemon(self):
        self.update()
        return self._pokemon

    def get_candies(self):
        self.update()
        return self._candies

    def get_candy(self, pokemon_id):
        self.update()
        try:
            return self._candies[pokemon_id]
        except KeyError:
            return 0

    def add_candy(self, pokemon_id, pokemon_candies):
        pokemon_id = int(pokemon_id)
        if pokemon_id in self._candies:
            self._candies[pokemon_id] += int(pokemon_candies)
        else:
            self._candies[pokemon_id] = int(pokemon_candies)

    def get_pokeballs(self):
        self.update()
        return self._pokeballs

    def print_stats(self):
        if self.update() is True:
            self._log('')
            self._log('Username: {}'.format(self._player.username))
            self._log('Account creation: {}'.format(self._player.get_creation_date()))
            self._log('Bag storage: {}/{}'.format(self._inventory['count'], self._player.max_item_storage))
            self._log('Pokemon storage: {}/{}'.format(len(self._pokemon) + len(self._eggs), self._player.max_pokemon_storage))
            self._log('Stardust: {:,}'.format(self._player.stardust))
            self._log('Pokecoins: {}'.format(self._player.pokecoin))
            self._log('Poke Balls: {}'.format(self._pokeballs[1]))
            self._log('Great Balls: {}'.format(self._pokeballs[2]))
            self._log('Ultra Balls: {}'.format(self._pokeballs[3]))
            self._log('-- Level: {}'.format(self._player.level))
            self._log('-- Experience: {:,}'.format(self._player.experience))
            self._log('-- Experience until next level: {:,}'.format(self._player.next_level_xp - self._player.experience))
            self._log('-- Pokemon captured: {:,}'.format(self._player.pokemons_captured))
            self._log('-- Pokestops visited: {:,}'.format(self._player.poke_stop_visits))

    def heartbeat(self):
        self.update(do_sleep=False)

        if len(self._player.hatched_eggs):
            self._player.hatched_eggs.pop(0)
            self._log("[Egg] Hatched an egg!", "green")

    def get_hatched_eggs(self):
        self._api_wrapper.get_hatched_eggs().call()
        if len(self._player.hatched_eggs):
            self._player.hatched_eggs.pop(0)
            self._log("[Egg] Hatched an egg!", "green")

    def _log(self, text, color='black'):
        self._logger.log(text, color=color, prefix='#')
