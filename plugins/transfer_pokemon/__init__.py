from app import Plugin
from app import kernel
from pokemongo_bot.human_behaviour import sleep


@kernel.container.register('transfer_pokemon', ['@config.transfer_pokemon', '@event_manager', '@logger'],
                           tags=['plugin'])
class TransferPokemon(Plugin):
    def __init__(self, config, event_manager, logger):
        self.config = config
        self.event_manager = event_manager
        self.set_logger(logger, 'Transfer')

        if self.config["transfer_on_start"]:
            self.event_manager.add_listener('bot_initialized', self.transfer_on_bot_start)

        self.event_manager.add_listener('pokemon_bag_full', self.filter_deployed_pokemon, priority=-50)
        self.event_manager.add_listener('pokemon_bag_full', self.filter_favorited_pokemon, priority=-40)
        self.event_manager.add_listener('pokemon_caught', self.wrap_pokemon_in_list, priority=-30)

        self.event_manager.add_listener('pokemon_caught', self.filter_pokemon_by_ignore_list, priority=-20)
        self.event_manager.add_listener('pokemon_bag_full', self.filter_pokemon_by_ignore_list, priority=-20)

        self.event_manager.add_listener('pokemon_caught', self.filter_pokemon_by_cp_iv, priority=-10)
        self.event_manager.add_listener('pokemon_bag_full', self.filter_pokemon_by_cp_iv, priority=-10)

        self.event_manager.add_listener('pokemon_caught', self.transfer_pokemon, priority=0)
        self.event_manager.add_listener('transfer_pokemon', self.transfer_pokemon, priority=0)
        self.event_manager.add_listener('pokemon_bag_full', self.transfer_pokemon, priority=0)

    @staticmethod
    def transfer_on_bot_start(bot):
        bot.fire("pokemon_bag_full")

    @staticmethod
    def get_transfer_list(bot, transfer_list=None):
        if transfer_list is None:
            transfer_list = bot.player_service.get_pokemon()

        return None if len(transfer_list) == 0 else transfer_list

    def get_indexed_pokemon(self, bot, transfer_list=None):
        transfer_list = self.get_transfer_list(bot, transfer_list)
        if transfer_list is None:
            return None

        indexed_pokemon = dict()
        for deck_pokemon in transfer_list:
            pokemon_num = deck_pokemon.pokemon_id
            if pokemon_num not in indexed_pokemon:
                indexed_pokemon[pokemon_num] = list()
            indexed_pokemon[pokemon_num].append(deck_pokemon)

        return indexed_pokemon

    # Filters Pokemon deployed at gyms
    # Never disable as it might lead to a ban!
    def filter_deployed_pokemon(self, bot, transfer_list=None, filter_list=None):
        # type: (PokemonGoBot, Optional[List[Pokemon]]), Optional[List[str]] -> Dict[Str, List]

        filter_list = [] if filter_list is None else filter_list
        transfer_list = self.get_transfer_list(bot, transfer_list)
        if transfer_list is None:
            return False

        new_transfer_list = [deck_pokemon for deck_pokemon in transfer_list if deck_pokemon.deployed_fort_id is None]

        if len(new_transfer_list) != len(transfer_list):
            filter_list.append("excluding Pokemon at gyms")

        return {"transfer_list": new_transfer_list, "filter_list": filter_list}

    # Filters favorited Pokemon
    # Never disable as it might lead to a ban!
    def filter_favorited_pokemon(self, bot, transfer_list=None, filter_list=None):
        # type: (PokemonGoBot, Optional[List[Pokemon]]), Optional[List[str]] -> Dict[Str, List]

        filter_list = [] if filter_list is None else filter_list
        transfer_list = self.get_transfer_list(bot, transfer_list)
        if transfer_list is None:
            return False

        new_transfer_list = [deck_pokemon for deck_pokemon in transfer_list if deck_pokemon.favorite is False]

        if len(new_transfer_list) != len(transfer_list):
            filter_list.append("excluding favorited Pokemon")

        return {"transfer_list": new_transfer_list, "filter_list": filter_list}

    # Wraps a caught Pokemon into a list for transferring
    @staticmethod
    def wrap_pokemon_in_list(transfer_list=None, pokemon=None):
        if pokemon is None:
            return

        if transfer_list is None:
            transfer_list = []

        transfer_list.append(pokemon)
        return {"transfer_list": transfer_list}

    # Filters Pokemon based on ignore/always keep list
    def filter_pokemon_by_ignore_list(self, bot, transfer_list=None, filter_list=None):
        # type: (PokemonGoBot, Optional[List[Pokemon]]), Optional[List[str]] -> Dict[Str, List]

        if self.config["use_always_keep_filter"] is False:
            return

        filter_list = [] if filter_list is None else filter_list
        transfer_list = self.get_transfer_list(bot, transfer_list)
        if transfer_list is None:
            return False

        always_keep_list = self.config["always_keep"]

        new_transfer_list = []
        excluded_species = set()
        for pokemon in transfer_list:
            species_num = pokemon.pokemon_id
            species_name = bot.pokemon_list[species_num - 1]["Name"]
            if species_name not in always_keep_list or isinstance(always_keep_list[species_name], dict) and "keep" in always_keep_list[species_name] and always_keep_list[species_name]["keep"] is False:
                new_transfer_list.append(pokemon)
            else:
                excluded_species.add(species_name)

        if len(new_transfer_list) != len(transfer_list):
            if len(excluded_species) > 1:
                excluded_species_list = list(excluded_species)
                filter_list.append(
                    "excluding " + "s, ".join(excluded_species_list[:-1]) + "s and " + excluded_species_list[-1] + "s")
            else:
                filter_list.append("excluding " + excluded_species.pop() + "s")

        return {"transfer_list": new_transfer_list, "filter_list": filter_list}

    # TODO: Fix this function to use dependency injection for release rules
    def filter_pokemon_by_cp_iv(self, bot, transfer_list=None, filter_list=None):
        # type: (PokemonGoBot, Optional[List[Pokemon]]), Optional[List[str]] -> Dict[Str, List]

        if self.config["use_cp_iv_filter"] is False:
            return

        filter_list = [] if filter_list is None else filter_list
        filter_list.append("according to per-species CP/IV rules")

        transfer_list = self.get_transfer_list(bot, transfer_list)
        if transfer_list is None:
            return False

        cp_iv_rules = self.config["cp_iv_rules"]
        default_rules = cp_iv_rules["default"]

        indexed_pokemon = self.get_indexed_pokemon(bot, transfer_list)

        pokemon_groups = list(indexed_pokemon.keys())
        for pokemon_group in pokemon_groups:

            # skip if it's our only pokemon of this type
            if len(indexed_pokemon[pokemon_group]) < 2:
                del indexed_pokemon[pokemon_group]
                continue

            # Load rules for this group. If rule doesnt exist make one with default settings.
            pokemon_name = bot.pokemon_list[pokemon_group - 1]["Name"]
            pokemon_rules = cp_iv_rules.get(pokemon_name, default_rules)
            cp_threshold = pokemon_rules['release_below_cp']
            iv_threshold = pokemon_rules['release_below_iv']
            rules_logic = pokemon_rules['logic']

            # only keep everything below specified CP
            group_transfer_list = []
            for deck_pokemon in indexed_pokemon[pokemon_group]:

                # is the Pokemon's CP less than our set threshold?
                within_cp = (deck_pokemon.combat_power <= cp_threshold)

                # is the Pokemon's IV less than our set threshold?
                within_potential = (deck_pokemon.potential <= iv_threshold)

                # if we are using AND logic and both are true, transfer
                if rules_logic == 'and' and (within_cp and within_potential):
                    group_transfer_list.append(deck_pokemon)

                # if we are using OR logic and either is true, transfer
                elif rules_logic == 'or' and (within_cp or within_potential):
                    group_transfer_list.append(deck_pokemon)

            # Check if we are trying to remove all the pokemon in this group.
            if len(group_transfer_list) == len(indexed_pokemon[pokemon_group]):
                # Sort by CP * potential and keep the best one
                indexed_pokemon[pokemon_group].sort(key=lambda p: p.combat_power * p.potential)
                indexed_pokemon[pokemon_group] = indexed_pokemon[pokemon_group][:-1]
            else:
                indexed_pokemon[pokemon_group] = group_transfer_list

        new_transfer_list = []
        pokemon_groups = list(indexed_pokemon.keys())
        for pokemon_group in pokemon_groups:
            for deck_pokemon in indexed_pokemon[pokemon_group]:
                new_transfer_list.append(deck_pokemon)

        return {"transfer_list": new_transfer_list, "filter_list": filter_list}

    def transfer_pokemon(self, bot, transfer_list=None, filter_list=None):
        # type: (PokemonGoBot, Optional[List[Pokemon]], Optional[List[str]]) -> None

        filter_list = [] if filter_list is None else filter_list

        if transfer_list is None or len(transfer_list) == 0:
            return False

        output_str = "Transferring {} Pokemon".format(len(transfer_list))

        # Print out the list of filters used
        filter_list = filter_list[::-1]
        if len(filter_list) > 1:
            output_str += " " + ", ".join(filter_list[:-1]) + " and " + filter_list[-1]
        elif len(filter_list) == 1:
            output_str += " " + filter_list[0]

        self.log(output_str)

        for index, pokemon in enumerate(transfer_list):
            pokemon_num = pokemon.pokemon_id
            pokemon_name = bot.pokemon_list[pokemon_num - 1]["Name"]
            pokemon_cp = pokemon.combat_power
            pokemon_potential = pokemon.potential
            self.log(
                "Transferring {0} (#{1}) with CP {2} and IV {3} ({4}/{5})".format(
                    pokemon_name,
                    pokemon_num,
                    pokemon_cp,
                    pokemon_potential,
                    index + 1,
                    len(transfer_list)
                )
            )

            bot.api_wrapper.release_pokemon(pokemon_id=pokemon.unique_id)
            sleep(2)
            bot.player_service.add_candy(pokemon_num, 1)
            bot.fire('after_transfer_pokemon', pokemon=pokemon)

        self.log("Transferred {} Pokemon.".format(len(transfer_list)))
