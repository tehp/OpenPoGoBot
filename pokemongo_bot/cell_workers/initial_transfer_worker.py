from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep


class InitialTransferWorker(object):
    def __init__(self, bot):
        # type: (PokemonGoBot) -> None
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api_wrapper = bot.api_wrapper

    def work(self):
        logger.log('[x] Initial Transfer.')
        ignlist = self.config.ign_init_trans.split(',')

        if self.config.cp:
            logger.log('[x] Will NOT transfer anything above CP {} or these {}'.format(
                self.config.cp, ignlist))
        else:
            logger.log('[x] Preparing to transfer all Pokemon duplicates, keeping the highest CP of each one type.')

        pokemon_groups = self._initial_transfer_get_groups()

        for group_id in pokemon_groups:

            group_cp = list(pokemon_groups[group_id].keys())

            if len(group_cp) > 1:
                group_cp.sort()
                group_cp.reverse()

                pokemon = self.pokemon_list[int(group_id - 1)]
                pokemon_name = pokemon['Name']
                pokemon_num = pokemon['Number'].lstrip('0')

                for i in range(1, len(group_cp)):

                    if (self.config.cp and group_cp[i] > self.config.cp) or (pokemon_name in ignlist or pokemon_num in ignlist):
                        continue

                    logger.log('[x] Transferring #{} ({}) with CP {}'.format(group_id, pokemon_name, group_cp[i]))
                    self.api_wrapper.release_pokemon(pokemon_id=pokemon_groups[group_id][group_cp[i]]).call()

                    sleep(2)

        logger.log('[x] Transferring Done.')

    def _initial_transfer_get_groups(self):
        pokemon_groups = {}
        self.api_wrapper.get_player().get_inventory()
        response_dict = self.api_wrapper.call()
        pokemon_list = response_dict['pokemon']

        for pokemon in pokemon_list:
            group_id = pokemon.pokemon_id
            group_pokemon = pokemon.unique_id
            group_pokemon_cp = pokemon.combat_power

            if group_id not in pokemon_groups:
                pokemon_groups[group_id] = {}

            pokemon_groups[group_id].update({group_pokemon_cp: group_pokemon})
        return pokemon_groups
