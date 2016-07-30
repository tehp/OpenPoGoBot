# -*- coding: utf-8 -*-

from __future__ import print_function
import random
import time

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger


def get_pokemon_ids_from_inventory(response_dict):
    if response_dict is None:
        return []
    id_list = []
    pokemon_list = response_dict["pokemon"]
    for pokemon in pokemon_list:
        id_list.append(pokemon.unique_id)
    return id_list


class PokemonCatchWorker(object):
    BAG_FULL = 'bag_full'
    NO_POKEBALLS = 'no_pokeballs'

    def __init__(self, pokemon, bot):
        self.pokemon = pokemon
        self.api_wrapper = bot.api_wrapper
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.item_list = bot.item_list

    def should_transfer(self, combat_power, pokemon_potential):
        # type: (int, float) -> bool
        return combat_power < self.config.cp and pokemon_potential < self.config.pokemon_potential

    def throw_pokeball(self, encounter_id, pokeball, spawn_point_id, combat_power, pokemon_potential, pokemon_name):
        # type: (int, int, str, int, float, str) -> bool
        id_list_before_catching = self.get_pokemon_ids()
        self.api_wrapper.catch_pokemon(encounter_id=encounter_id,
                                       pokeball=pokeball,
                                       normalized_reticle_size=1.950 - random.random() / 200,
                                       spawn_point_id=spawn_point_id,
                                       hit_pokemon=True,
                                       spin_modifier=1,
                                       normalized_hit_position=1)
        response = self.api_wrapper.call()
        if response is None:
            return False
        pokemon_catch_response = response["encounter"]
        status = pokemon_catch_response.status
        if status is 2:
            logger.log('[-] Attempted to capture {} - failed.. trying again!'.format(pokemon_name), 'red')
            sleep(2)
            return True
        elif status is 3:
            logger.log('[x] Oh no! {} vanished! :('.format(pokemon_name), 'red')
            return False
        elif status is 1:
            self.bot.fire('pokemon_caught',
                          name=pokemon_name,
                          combat_power=combat_power,
                          pokemon_potential=pokemon_potential)
            if self.should_transfer(combat_power, pokemon_potential):
                id_list_after_catching = self.get_pokemon_ids()

                # Transferring Pokemon
                pokemon_to_transfer = list(set(id_list_after_catching) - set(id_list_before_catching))
                self.transfer_pokemon(pokemon_to_transfer[0])
                logger.log('[#] {} has been exchanged for candy!'.format(pokemon_name), 'green')
            return False
        else:
            return False

    def work(self):
        encounter_id = self.pokemon['encounter_id']
        spawnpoint_id = self.pokemon['spawn_point_id']
        player_latitude = self.pokemon['latitude']
        player_longitude = self.pokemon['longitude']
        self.api_wrapper.encounter(encounter_id=encounter_id,
                                   spawn_point_id=spawnpoint_id,
                                   player_latitude=player_latitude,
                                   player_longitude=player_longitude)
        response_dict = self.api_wrapper.call()

        if response_dict is None:
            return

        encounter = response_dict['encounter']
        status = encounter.status
        if encounter is None or status is None:
            return  # servers are down
        elif status is 7:
            logger.log('[x] Pokemon Bag is full!', 'red')
            return self.BAG_FULL
        elif status is 1:
            pokemon = encounter.wild_pokemon

            if pokemon is None:
                return

            combat_power = pokemon.combat_power
            total_iv = pokemon.attack + pokemon.defense + pokemon.stamina
            pokemon_potential = round((total_iv / 45.0), 2)
            pokemon_num = pokemon.pokemon_id - 1
            pokemon_name = self.pokemon_list[pokemon_num]['Name']
            self.bot.fire('before_catch_pokemon', name=pokemon_name,
                          combat_power=combat_power if combat_power is not None else "unknown",
                          pokemon_potential=pokemon_potential)

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
                    logger.log('[x] Out of pokeballs, switching to farming mode...', 'red')
                    # Begin searching for pokestops.
                    self.config.mode = 'farm'
                    return self.NO_POKEBALLS

                self.bot.fire('use_pokeball',
                              pokeball_name=self.item_list[str(pokeball)],
                              number_left=balls_stock[pokeball] - 1)

                balls_stock[pokeball] -= 1
                should_continue_throwing = self.throw_pokeball(encounter_id, pokeball, spawnpoint_id, combat_power,
                                                               pokemon_potential, pokemon_name)
        time.sleep(5)

    def _transfer_low_cp_pokemon(self, value):
        self.api_wrapper.get_inventory()
        response_dict = self.api_wrapper.call()
        if response_dict is not None:
            pokemon_list = response_dict["pokemon"]
            for pokemon in pokemon_list:
                if pokemon.combat_power < value:
                    self.transfer_pokemon(pokemon.unique_id)
                time.sleep(1.2)

    def transfer_pokemon(self, pid):
        self.api_wrapper.release_pokemon(pokemon_id=pid).call()

    def get_pokemon_ids(self):
        self.api_wrapper.get_inventory()
        response_dict = self.api_wrapper.call()
        return get_pokemon_ids_from_inventory(response_dict)
