from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.event_manager import manager


def log(text, color="black"):
    manager.fire("logging", text=text, color=color, prefix="Transfer")


@manager.on("pokemon_bag_full", priority=-1000)
def filter_pokemon(bot=None, transfer_list=None):
    # type: (PokemonGoBot, Optional[List[Pokemon]]) -> Dict[Str, List[Pokemon]]

    if transfer_list is None:
        bot.api_wrapper.get_player().get_inventory()
        response_dict = bot.api_wrapper.call()
        transfer_list = response_dict['pokemon']

    new_transfer_list = []
    indexed_pokemon = dict()
    for pokemon in transfer_list:

        # ignore deployed pokemon
        if pokemon.deployed_fort_id is not None:
            continue

        pokemon_num = pokemon.pokemon_id
        if pokemon_num not in indexed_pokemon:
            indexed_pokemon[pokemon_num] = list()
        indexed_pokemon[pokemon_num].append(pokemon)

    if bot.config.cp and False:
        ignore_list = bot.config.ign_init_trans.split(',')
        log("Transferring all Pokemon below {} CP, excluding {}.".format(bot.config.cp, ignore_list))

        groups = indexed_pokemon.keys()
        for group in groups:
            # check if ID or species name is in ignore list
            if str(group) in ignore_list or bot.pokemon_list[group - 1] in ignore_list:
                del indexed_pokemon[group]
            else:
                # only keep everything below specified CP
                indexed_pokemon[group] = [pokemon for pokemon in indexed_pokemon[group] if pokemon.combat_power < bot.config.cp]

        for group in indexed_pokemon:
            for pokemon in indexed_pokemon[group]:
                new_transfer_list.append(pokemon)

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


@manager.on("pokemon_bag_full", "transfer_pokemon", priority=1000)
def transfer_pokemon(bot=None, transfer_list=None):
    # type: (PokemonGoBot, Optional[List[Pokemon]]) -> None

    if transfer_list is None or len(transfer_list) == 0:
        log("No Pokemon to transfer.", color="yellow")

    for index, pokemon in enumerate(transfer_list):
        pokemon_num = pokemon.pokemon_id
        pokemon_name = bot.pokemon_list[pokemon_num - 1]["Name"]
        pokemon_cp = pokemon.combat_power
        log("Transferring {0} (#{1}) with CP {2} ({3}/{4})".format(pokemon_name,
                                                                   pokemon_num,
                                                                   pokemon_cp,
                                                                   index+1,
                                                                   len(transfer_list)))

        bot.api_wrapper.release_pokemon(pokemon_id=pokemon.unique_id).call()
        sleep(2)

    log("Transferred {} Pokemon.".format(len(transfer_list)))
