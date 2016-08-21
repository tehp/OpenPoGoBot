# -*- coding: utf-8 -*-

from __future__ import print_function
import random
import time

from app import Plugin
from app import kernel
from pokemongo_bot.human_behaviour import sleep


@kernel.container.register('catch_pokemon', ['@config.catch_pokemon', '@event_manager', '@logger'], tags=['plugin'])
class CatchPokemon(Plugin):
    def __init__(self, config, event_manager, logger):
        self.config = config
        self.event_manager = event_manager
        self.set_logger(logger, 'Catch')

        self.event_manager.add_listener('pokemon_found', self.pokemon_found)
        self.event_manager.add_listener('lure_pokemon_found', self.lure_pokemon_found)

    def pokemon_found(self, bot, encounters=None):
        # type: (PokemonGoBot, Optional[List[Encounter]]) -> None

        if encounters is None or len(encounters) == 0:
            return

        for pokemon_encounter in encounters:
            encounter_id = pokemon_encounter['encounter_id']
            spawn_point_id = pokemon_encounter['spawn_point_id']
            player_latitude = pokemon_encounter['latitude']
            player_longitude = pokemon_encounter['longitude']
            bot.api_wrapper.encounter(encounter_id=encounter_id,
                                      spawn_point_id=spawn_point_id,
                                      player_latitude=player_latitude,
                                      player_longitude=player_longitude)

            response = bot.api_wrapper.call()

            encounter_data = response["encounter"]
            status = encounter_data.status
            if status is 7:
                # Pokemon bag is full, fire event and return for now
                self.log("Pokemon bag is full; cannot catch.", color="red")
                bot.fire("pokemon_bag_full")
                return
            elif status is 1:
                pokemon = encounter_data.wild_pokemon

                if pokemon is None:
                    return

                combat_power = pokemon.combat_power
                pokemon_potential = pokemon.potential
                pokemon_num = pokemon.pokemon_id - 1
                pokemon_name = bot.pokemon_list[pokemon_num]["Name"]

                self.log("A wild {} appeared! [CP {}] [Potential {}]".format(pokemon_name, combat_power, pokemon_potential))

                balls_stock = bot.player_service.get_pokeballs()
                total_pokeballs = sum([balls_stock[ball_type] for ball_type in balls_stock])

                # Simulate app
                sleep(3)

                # TODO: This should probably be cleaned up
                should_continue_throwing = True
                while should_continue_throwing:
                    if total_pokeballs == 0:
                        self.log("No Pokeballs in inventory; cannot catch.", color="red")
                        return

                    pokeball = 0

                    if balls_stock[1] > 0:
                        pokeball = 1

                    if balls_stock[2] > 0:
                        if pokeball is 0 and combat_power <= 300 and balls_stock[2] < 10:
                            self.log('Great Ball stock is low... saving for pokemon with cp greater than 300')
                        elif combat_power > 300 or pokeball is 0:
                            pokeball = 2

                    if balls_stock[3] > 0:
                        if pokeball is 0 and combat_power <= 700 and balls_stock[3] < 10:
                            self.log('Ultra Ball stock is low... saving for pokemon with cp greater than 700')
                        elif combat_power > 700 or pokeball is 0:
                            pokeball = 3

                    if pokeball == 0:
                        self.log("No ball selected as all balls are low in stock. Saving for better Pokemon.", color="red")
                        bot.fire('no_balls')
                        return

                    self.log("Using {}... ({} left!)".format(bot.item_list[pokeball], balls_stock[pokeball]-1))

                    balls_stock[pokeball] -= 1
                    total_pokeballs -= 1
                    pos = {"latitude": encounter_data.latitude, "longitude": encounter_data.longitude}
                    should_continue_throwing = self.throw_pokeball(bot, encounter_id, pokeball, spawn_point_id, pokemon, pos)

                sleep(5)
            elif status is 6:
                return
            else:
                self.log("I don't know what happened! Maybe servers are down?", color="red")
                return

    def lure_pokemon_found(self, bot, encounters=None):
        # type: (PokemonGoBot, Optional[List[Encounter]]) -> None

        if encounters is None or len(encounters) == 0:
            return

        for pokemon_encounter in encounters:
            encounter_id = pokemon_encounter['encounter_id']
            fort_id = pokemon_encounter['fort_id']
            player_latitude = pokemon_encounter['latitude']
            player_longitude = pokemon_encounter['longitude']
            bot.api_wrapper.disk_encounter(encounter_id=encounter_id,
                                           fort_id=fort_id,
                                           player_latitude=player_latitude,
                                           player_longitude=player_longitude)

            response = bot.api_wrapper.call()

            encounter_data = response["disk_encounter"]
            status = encounter_data.status
            if status is 5:
                # Pokemon bag is full, fire event and return for now
                self.log("Pokemon bag is full; cannot catch.", color="red")
                bot.fire("pokemon_bag_full")
                return
            elif status is 1:
                pokemon = encounter_data.wild_pokemon

                if pokemon is None:
                    return

                combat_power = pokemon.combat_power
                pokemon_potential = pokemon.potential
                pokemon_num = pokemon.pokemon_id - 1
                pokemon_name = bot.pokemon_list[pokemon_num]["Name"]

                self.log("A lured {} appeared! [CP {}] [Potential {}]".format(pokemon_name, combat_power, pokemon_potential))

                balls_stock = bot.player_service.get_pokeballs()
                total_pokeballs = sum([balls_stock[ball_type] for ball_type in balls_stock])

                # Simulate app
                sleep(3)

                # TODO: This should probably be cleaned up
                should_continue_throwing = True
                while should_continue_throwing:
                    if total_pokeballs == 0:
                        self.log("No Pokeballs in inventory; cannot catch.", color="red")
                        return

                    pokeball = 0

                    if balls_stock[1] > 0:
                        pokeball = 1

                    if balls_stock[2] > 0:
                        if pokeball is 0 and combat_power <= 300 and balls_stock[2] < 10:
                            self.log('Great Ball stock is low... saving for pokemon with cp greater than 300')
                        elif combat_power > 300 or pokeball is 0:
                            pokeball = 2

                    if balls_stock[3] > 0:
                        if pokeball is 0 and combat_power <= 700 and balls_stock[3] < 10:
                            self.log('Ultra Ball stock is low... saving for pokemon with cp greater than 700')
                        elif combat_power > 700 or pokeball is 0:
                            pokeball = 3

                    if pokeball == 0:
                        self.log("No ball selected as all balls are low in stock. Saving for better Pokemon.", color="red")
                        bot.fire('no_balls')
                        return

                    self.log("Using {}... ({} left!)".format(bot.item_list[pokeball], balls_stock[pokeball]-1))

                    balls_stock[pokeball] -= 1
                    total_pokeballs -= 1
                    pos = {"latitude": encounter_data.latitude, "longitude": encounter_data.longitude}
                    should_continue_throwing = self.throw_pokeball(bot, encounter_id, pokeball, fort_id, pokemon, pos)

                sleep(5)
            elif status is 2 or status is 3 or status is 4:
                return
            else:
                self.log("I don't know what happened! Maybe servers are down?", color="red")
                return

    def throw_pokeball(self, bot, encounter_id, pokeball, spawn_point_id, pokemon, pos):
        # type: (PokemonGoBot, int, int, str, Pokemon) -> bool

        if random.random() > self.config["throw"]["spin"]:
            spin_modifier = 1
        else:
            spin_modifier = 0

        normalized_hit_position = self.get_hit()

        print("spin: " + str(spin_modifier))
        print("hit: " + str(normalized_hit_position))

        bot.api_wrapper.catch_pokemon(encounter_id=encounter_id,
                                      pokeball=pokeball,
                                      normalized_reticle_size=1.950 - random.random() / 200,
                                      spawn_point_id=spawn_point_id,
                                      hit_pokemon=True,
                                      spin_modifier=spin_modifier,
                                      normalized_hit_position=normalized_hit_position)
        response = bot.api_wrapper.call()
        if response is None:
            return False
        pokemon_catch_response = response["encounter"]
        status = pokemon_catch_response.status
        pokemon_data = bot.pokemon_list[pokemon.pokemon_id - 1]
        pokemon_name = pokemon_data["Name"]
        pokemon_id = pokemon_data["Number"]
        if status is 2:
            self.log('Failed to capture {}. Trying again!'.format(pokemon_name), 'yellow')
            bot.fire("pokemon_catch_failed", pokemon=pokemon)
            sleep(2)
            return True
        elif status is 3:
            self.log('Oh no! {} fled! :('.format(pokemon_name), 'red')
            bot.fire("pokemon_fled", pokemon=pokemon)
            return False
        elif status is 1:
            self.log('{} has been caught! (CP {}, IV {})'.format(pokemon_name, pokemon.combat_power, pokemon.potential), 'green')
            xp = pokemon_catch_response.xp
            stardust = pokemon_catch_response.stardust
            candy = pokemon_catch_response.candy
            bot.player_service.add_candy(pokemon_id, candy)
            self.log("Rewards: {} XP, {} Stardust, {} Candy".format(xp, stardust, candy), "green")
            bot.fire("pokemon_caught", pokemon=pokemon, position=pos)
            return False

    def get_spin(self):
        val = random.gauss(0.8, 0.15)
        while val < 0 or val > 1:
            val = random.gauss(0.8, 0.15)
        return val

    def get_hit(self):
        if self.config["throw"]["skill"] == "perfect":
            return 1
        else:
            if self.config["throw"]["skill"] == "better":
                med = 0.9
            else:
                med = 0.8

            val = random.gauss(med, 0.15)
            while val < 0 or val > 1:
                val = random.gauss(med, 0.15)
            return val

