# -*- coding: utf-8 -*-

from __future__ import print_function
import random
import time

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger


def get_pokemon_ids_from_inventory(response_dict):
    id_list = []
    inventory_items = response_dict.get("responses", {}).get("GET_INVENTORY", {}).get("inventory_delta", {}).get(
        "inventory_items")
    if response_dict is not None:
        for item_data in inventory_items:
            pokemon = item_data.get("inventory_item_data", {}).get("pokemon_data")
            if pokemon is not None:
                if pokemon.get('is_egg', False):
                    continue
                id_list.append(pokemon['id'])

    return id_list


class PokemonCatchWorker(object):

    def __init__(self, pokemon, bot):
        self.pokemon = pokemon
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.item_list = bot.item_list
        self.inventory = bot.inventory

    def should_transfer(self, combat_power, pokemon_potential):
        return combat_power < self.config.cp and pokemon_potential < self.config.pokemon_potential

    def throw_pokeball(self, encounter_id, pokeball, spawnpoint_id, combat_power, pokemon_potential, pokemon_name):
        id_list_before_catching = self.get_pokemon_ids()
        self.api.catch_pokemon(
            encounter_id=encounter_id,
            pokeball=pokeball,
            normalized_reticle_size=1.950 - random.random() / 200,
            spawn_point_guid=spawnpoint_id,
            hit_pokemon=1,
            spin_modifier=1,
            NormalizedHitPosition=1)
        response_dict = self.api.call()
        pokemon_catch_response = response_dict.get('responses', {}).get('CATCH_POKEMON', {})
        status = pokemon_catch_response.get('status')
        if status is None:
            return False
        elif status is 2:
            logger.log(
                '[-] Attempted to capture {} - failed.. trying again!'.format(
                    pokemon_name), 'red')
            sleep(2)
            return True
        elif status is 3:
            logger.log(
                '[x] Oh no! {} vanished! :('.format(
                    pokemon_name), 'red')
            return False
        elif status is 1:
            if self.should_transfer(combat_power, pokemon_potential):
                logger.log(
                    '[x] Captured {}! [CP {}] [IV {}] - exchanging for candy'.format(
                        pokemon_name, combat_power,
                        pokemon_potential), 'green')
                id_list_after_catching = self.get_pokemon_ids()

                # Transfering Pokemon
                pokemon_to_transfer = list(set(id_list_after_catching) - set(id_list_before_catching))
                self.transfer_pokemon(pokemon_to_transfer[0])
                logger.log(
                    '[#] {} has been exchanged for candy!'.format(pokemon_name), 'green')
            else:
                logger.log(
                    '[x] Captured {}! [CP {}]'.format(pokemon_name, combat_power), 'green')
            return False
        else:
            return False

    def work(self):
        encounter_id = self.pokemon['encounter_id']
        spawnpoint_id = self.pokemon['spawnpoint_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']
        self.api.encounter(encounter_id=encounter_id,
                           spawnpoint_id=spawnpoint_id,
                           player_latitude=player_latitude,
                           player_longitude=player_longitude)
        response_dict = self.api.call()

        encounter = response_dict.get('responses', {}).get('ENCOUNTER', {})
        status = encounter.get('status', {})
        if encounter is None or status is None:
            return  # servers are down
        elif status is 7:
            logger.log('[x] Pokemon Bag is full!', 'red')
            self.bot.initial_transfer()
        elif status is 1:
            combat_power = 0
            total_iv = 0
            pokemon = encounter.get('wild_pokemon')
            if pokemon is not None:
                pokemon_data = pokemon.get('pokemon_data', {})
                combat_power = pokemon_data.get('cp')  # cp can be none
                iv_stats = ['individual_attack', 'individual_defense', 'individual_stamina']
                for individual_stat in iv_stats:
                    try:
                        total_iv += pokemon_data[individual_stat]
                    except KeyError:
                        continue
                pokemon_potential = round((total_iv / 45.0), 2)
                pokemon_num = int(pokemon['pokemon_data'][
                    'pokemon_id']) - 1
                pokemon_name = self.pokemon_list[int(pokemon_num)]['Name']
                logger.log('[#] A Wild {} appeared! [CP {}] [Potential {}]'.format(pokemon_name, combat_power if combat_power is not None else "unknown", pokemon_potential), 'yellow')

                # Simulate app
                sleep(3)

            balls_stock = self.bot.pokeball_inventory()
            should_continue_throwing = True
            while should_continue_throwing:
                pokeball = 0

                if balls_stock[1] > 0:
                    pokeball = 1

                if balls_stock[2] > 0:
                    if pokeball is 0 and combat_power <= 300 and balls_stock[2] < 10:
                        print('Great Ball stock is low... saving for pokemon with cp greater than 300')
                    elif combat_power > 300 or pokeball is 0:
                        pokeball = 2

                if balls_stock[3] > 0:
                    if pokeball is 0 and combat_power <= 700 and balls_stock[3] < 10:
                        print('Ultra Ball stock is low... saving for pokemon with cp greater than 700')
                    elif combat_power > 700 or pokeball is 0:
                        pokeball = 3

                if pokeball is 0:
                    logger.log(
                        '[x] Out of pokeballs, switching to farming mode...',
                        'red')
                    # Begin searching for pokestops.
                    self.config.mode = 'farm'
                    return -1

                logger.log('[x] Using {}... ({} left!)'.format(self.item_list[str(pokeball)], balls_stock[pokeball] - 1))

                balls_stock[pokeball] -= 1
                should_continue_throwing = self.throw_pokeball(encounter_id, pokeball, spawnpoint_id, combat_power, pokemon_potential, pokemon_name)
        time.sleep(5)

    def _transfer_low_cp_pokemon(self, value):
        self.api.get_inventory()
        response_dict = self.api.call()
        self._transfer_all_low_cp_pokemon(value, response_dict)

    def _transfer_all_low_cp_pokemon(self, value, response_dict):
        inventory_items = response_dict.get("responses", {}).get("GET_INVENTORY", {}).get("inventory_delta", {}).get(
            "inventory_items")
        if response_dict is not None:
            for item_data in inventory_items:
                item = item_data.get("inventory_item_data", {}).get("pokemon")
                if item is not None:
                    pokemon = item['inventory_item_data']['pokemon']
                    if 'cp' in pokemon and pokemon['cp'] < value:
                        self.api.release_pokemon(pokemon_id=pokemon['id'])
                        response_dict = self.api.call()
                    time.sleep(1.2)

    def transfer_pokemon(self, pid):
        self.api.release_pokemon(pokemon_id=pid)
        # Why do we need response_dict? Commenting out to pass pylint
        # response_dict = self.api.call()
        self.api.call()

    def get_pokemon_ids(self):
        self.api.get_inventory()
        response_dict = self.api.call()
        return get_pokemon_ids_from_inventory(response_dict)
