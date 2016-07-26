import json

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot import logger


class InitialTransferWorker(object):
    def __init__(self, bot):
        self.config = bot.config
        self.pokemon_list = bot.pokemon_list
        self.api = bot.api

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

            group_cp = pokemon_groups[group_id].keys()

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
                    self.api.release_pokemon(pokemon_id=pokemon_groups[group_id][group_cp[i]])

                    # Not using the response from API at the moment; commenting out to pass pylint
                    # response_dict = self.api.call()
                    self.api.call()

                    sleep(2)

        logger.log('[x] Transferring Done.')

    def _initial_transfer_get_groups(self):
        pokemon_groups = {}
        self.api.get_player().get_inventory()
        inventory_req = self.api.call()
        inventory_dict = inventory_req['responses']['GET_INVENTORY']['inventory_delta']['inventory_items']
        with open('web/inventory-%s.json' % (self.config.username), 'w') as outfile:
            json.dump(inventory_dict, outfile)

        for pokemon in inventory_dict:
            try:
                pokemon_data = pokemon['inventory_item_data']['pokemon_data']
                group_id = pokemon_data['pokemon_id']
                group_pokemon = pokemon_data['id']
                group_pokemon_cp = pokemon_data['cp']

                if group_id not in pokemon_groups:
                    pokemon_groups[group_id] = {}

                pokemon_groups[group_id].update({group_pokemon_cp: group_pokemon})
            except KeyError:
                continue
        return pokemon_groups
