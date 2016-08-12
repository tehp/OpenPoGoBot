from app import service_container
from pokemongo_bot import Item
from pokemongo_bot import logger
from pokemongo_bot import sleep


@service_container.register('player_service', ['@api_wrapper'])
class Player(object):
    def __init__(self, api_wrapper):
        self._api_wrapper = api_wrapper
        self._logged_in = False

        self._eggs = None
        self._candies = 0
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

    def update(self):
        response_dict = self._api_wrapper.get_player().get_inventory().call()
        sleep(2)

        if response_dict is None:
            logger.log('[#] Failed to retrieve player and inventory stats', color='red')
            return False

        self._player = response_dict['player']
        self._inventory = response_dict['inventory']
        self._candies = response_dict['candy']
        self._pokemon = response_dict['pokemon']
        self._candies = response_dict['candy']
        self._eggs = response_dict['eggs']

        for item_id in self._inventory:
            if item_id in self._pokeballs:
                self._pokeballs[item_id] = self._inventory[item_id]

        return True

    def get_player(self):
        self.update()
        return self._player

    def get_inventory(self):
        self.update()
        return self._inventory

    def get_pokemon(self):
        self.update()
        return self._pokemon

    def get_candies(self):
        self.update()
        return self._candies

    def get_candy(self):
        self.update()
        return self._candies

    def get_pokeballs(self):
        self.update()
        return self._pokeballs

    def print_stats(self):

        if self.update() is True:
            balls_stock = self.get_pokeballs()

            logger.log('[#]')
            logger.log('[#] Username: {}'.format(self._player.username))
            logger.log('[#] Account creation: {}'.format(self._player.get_creation_date()))
            logger.log('[#] Bag storage: {}/{}'.format(self._inventory['count'], self._player.max_item_storage))
            logger.log('[#] Pokemon storage: {}/{}'.format(len(self._pokemon) + len(self._eggs), self._player.max_pokemon_storage))
            logger.log('[#] Stardust: {:,}'.format(self._player.stardust))
            logger.log('[#] Pokecoins: {}'.format(self._player.pokecoin))
            logger.log('[#] Poke Balls: {}'.format(balls_stock[1]))
            logger.log('[#] Great Balls: {}'.format(balls_stock[2]))
            logger.log('[#] Ultra Balls: {}'.format(balls_stock[3]))
            logger.log('[#] -- Level: {}'.format(self._player.level))
            logger.log('[#] -- Experience: {:,}'.format(self._player.experience))
            logger.log(
                '[#] -- Experience until next level: {:,}'.format(self._player.next_level_xp - self._player.experience))
            logger.log('[#] -- Pokemon captured: {:,}'.format(self._player.pokemons_captured))
            logger.log('[#] -- Pokestops visited: {:,}'.format(self._player.poke_stop_visits))
