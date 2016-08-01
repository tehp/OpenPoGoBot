# -*- coding: utf-8 -*-

from __future__ import print_function
import random
import time

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.event_manager import manager
from pokemongo_bot import logger


@manager.on("pokemon_found")
def pokemon_found(bot, encounters=None):
    # type: (PokemonGoBot, Optional[List[Encounter]]) -> None

    if encounters is None or len(encounters) == 0:
        return

    def log(text, color="black"):
        logger.log(text, color=color, prefix="Catch")

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
            log("Pokemon bag is full; cannot catch.", color="red")
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

            log("A wild {} appeared! [CP {}] [Potential {}]".format(pokemon_name, combat_power, pokemon_potential))

            balls_stock = bot.pokeball_inventory()
            total_pokeballs = sum([balls_stock[ball_type] for ball_type in balls_stock])

            # Simulate app
            sleep(3)

            # TODO: This should probably be cleaned up
            should_continue_throwing = True
            while should_continue_throwing:
                if total_pokeballs == 0:
                    log("No Pokeballs in inventory; cannot catch.", color="red")
                    return

                pokeball = 0

                if balls_stock[1] > 0:
                    pokeball = 1

                if balls_stock[2] > 0:
                    if pokeball is 0 and combat_power <= 300 and balls_stock[2] < 10:
                        log('Great Ball stock is low... saving for pokemon with cp greater than 300')
                    elif combat_power > 300 or pokeball is 0:
                        pokeball = 2

                if balls_stock[3] > 0:
                    if pokeball is 0 and combat_power <= 700 and balls_stock[3] < 10:
                        log('Ultra Ball stock is low... saving for pokemon with cp greater than 700')
                    elif combat_power > 700 or pokeball is 0:
                        pokeball = 3

                if pokeball == 0:
                    log("No ball selected as all balls are low in stock. Saving for better Pokemon.", color="red")
                    return

                log("Using {}... ({} left!)".format(bot.item_list[pokeball], balls_stock[pokeball]-1))

                balls_stock[pokeball] -= 1
                total_pokeballs -= 1
                should_continue_throwing = throw_pokeball(bot, encounter_id, pokeball, spawn_point_id,
                                                          combat_power, pokemon_potential, pokemon_name)

            time.sleep(5)
        elif status is 6:
            return
        else:
            log("I don't know what happened! Maybe servers are down?", color="red")
            return


def throw_pokeball(bot, encounter_id, pokeball, spawn_point_id, combat_power, pokemon_potential, pokemon_name):
    # type: (PokemonGoBot, int, int, str, int, float, str) -> bool

    def log(text, color="black"):
        logger.log(text, color=color, prefix="Catch")

    bot.api_wrapper.catch_pokemon(encounter_id=encounter_id,
                                  pokeball=pokeball,
                                  normalized_reticle_size=1.950 - random.random() / 200,
                                  spawn_point_id=spawn_point_id,
                                  hit_pokemon=True,
                                  spin_modifier=1,
                                  normalized_hit_position=1)
    response = bot.api_wrapper.call()
    if response is None:
        return False, None
    pokemon_catch_response = response["encounter"]
    status = pokemon_catch_response.status
    if status is 2:
        log('Failed to capture {}. Trying again!'.format(pokemon_name), 'yellow')
        sleep(2)
        return True
    elif status is 3:
        log('Oh no! {} fled! :('.format(pokemon_name), 'red')
        return False
    elif status is 1:
        log('{} has been caught! (CP {}, IV {})'.format(pokemon_name, combat_power, pokemon_potential), 'green')
        xp = pokemon_catch_response.xp
        stardust = pokemon_catch_response.stardust
        candy = pokemon_catch_response.candy
        log("Rewards: {} XP, {} Stardust, {} Candy".format(xp, stardust, candy), "green")
        return False
