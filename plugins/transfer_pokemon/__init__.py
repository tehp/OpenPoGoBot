from api.pokemon import Pokemon
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.event_manager import manager
from pokemongo_bot import logger


@manager.on("pokemon_bag_full", "pokemon_caught", priority=-1000)
def filter_pokemon(bot, transfer_list=None, pokemon=None):
    # type: (PokemonGoBot, Optional[List[Pokemon]], Pokemon) -> Dict[Str, List[Pokemon]]

    def log(text, color="black"):
        logger.log(text, color=color, prefix="Transfer")

    if transfer_list is None:
        bot.api_wrapper.get_player().get_inventory()
        response_dict = bot.api_wrapper.call()
        transfer_list = response_dict['pokemon']

    new_transfer_list = []
    indexed_pokemon = dict()
    for deck_pokemon in transfer_list:

        # ignore deployed pokemon
        if deck_pokemon.deployed_fort_id is not None:
            continue

        pokemon_num = deck_pokemon.pokemon_id
        if pokemon_num not in indexed_pokemon:
            indexed_pokemon[pokemon_num] = list()
        indexed_pokemon[pokemon_num].append(deck_pokemon)

    if bot.config.cp or bot.config.pokemon_potential:
        ignore_list = bot.config.ign_init_trans.split(',')
        log(
            "Transferring {} Pokemon with CP NOT above {} and IV NOT above {} and excluding {}.".format(
                ("caught" if isinstance(pokemon, Pokemon) else "all"),
                bot.config.cp,
                bot.config.pokemon_potential,
                ignore_list
            )
        )

        groups = list(indexed_pokemon.keys())
        for group in groups:

            # If we've been given a caught pokemon, only process that group
            if isinstance(pokemon, Pokemon) and group != pokemon.pokemon_id:
                del indexed_pokemon[group]
                continue

            # check if ID or species name is in ignore list or if it's our only pokemon of this type
            if str(group) in ignore_list or bot.pokemon_list[group - 1] in ignore_list or len(indexed_pokemon[group]) < 2:
                del indexed_pokemon[group]
            else:
                # only keep everything below specified CP
                group_transfer_list = []
                for deck_pokemon in indexed_pokemon[group]:
                    within_cp = (bot.config.cp == 0 or deck_pokemon.combat_power >= bot.config.cp)
                    within_potential = (bot.config.pokemon_potential == 0 or deck_pokemon.potential >= bot.config.pokemon_potential)
                    if not within_cp and not within_potential:
                        group_transfer_list.append(deck_pokemon)

                # Check if we are trying to remove all the pokemon in this group.
                if len(group_transfer_list) == len(indexed_pokemon[group]):
                    # Sort by CP and keep the best one
                    indexed_pokemon[group].sort(key=lambda current_pokemon: current_pokemon.combat_power)
                    indexed_pokemon[group] = indexed_pokemon[group][:-1]
                else:
                    indexed_pokemon[group] = group_transfer_list

        for group in indexed_pokemon:
            for deck_pokemon in indexed_pokemon[group]:
                new_transfer_list.append(deck_pokemon)

    else:
        log("Transferring all duplicate Pokemon, keeping the highest CP for each.")

        for group in indexed_pokemon:
            # There's only one, keep it
            if len(indexed_pokemon[group]) < 2:
                continue

            # Sort by CP and keep the best one
            indexed_pokemon[group].sort(key=lambda current_pokemon: current_pokemon.combat_power)
            new_transfer_list += indexed_pokemon[group][:-1]

    return {"transfer_list": new_transfer_list}


@manager.on("pokemon_bag_full", "transfer_pokemon", "pokemon_caught", priority=1000)
def transfer_pokemon(bot, transfer_list=None):
    # type: (PokemonGoBot, Optional[List[Pokemon]]) -> None

    def log(text, color="black"):
        logger.log(text, color=color, prefix="Transfer")

    if transfer_list is None or len(transfer_list) == 0:
        log("No Pokemon to transfer.", color="yellow")

    for index, pokemon in enumerate(transfer_list):
        pokemon_num = pokemon.pokemon_id
        pokemon_name = bot.pokemon_list[pokemon_num - 1]["Name"]
        pokemon_cp = pokemon.combat_power
        pokemon_potential = pokemon.potential
        log("Transferring {0} (#{1}) with CP {2} and IV {3} ({4}/{5})".format(pokemon_name,
                                                                              pokemon_num,
                                                                              pokemon_cp,
                                                                              pokemon_potential,
                                                                              index+1,
                                                                              len(transfer_list)))

        bot.api_wrapper.release_pokemon(pokemon_id=pokemon.unique_id).call()
        sleep(2)

    log("Transferred {} Pokemon.".format(len(transfer_list)))
