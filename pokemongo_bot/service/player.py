from app import service_container
from pokemongo_bot.item_list import Item
from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep


@service_container.register('player_service', ['@api_wrapper'])
class Player(object):
    def __init__(self, api_wrapper):
        self._api_wrapper = api_wrapper
        self._logged_in = False

        self._eggs = None
        self._egg_incubators = []
        self._candies = {}
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
            logger.log('Failed to retrieve player and inventory stats', color='red', prefix='#')
            return False

        self._player = response_dict['player']
        self._inventory = response_dict['inventory']
        self._candies = response_dict['candy']
        self._pokemon = response_dict['pokemon']
        self._candies = response_dict['candy']
        self._eggs = response_dict['eggs']
        self._egg_incubators = response_dict['egg_incubators']

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

    def get_eggs(self):
        self.update()
        return self._eggs

    def get_egg_incubators(self):
        self.update()
        return self._egg_incubators

    def get_pokemon(self):
        self.update()
        return self._pokemon

    def get_candies(self):
        self.update()
        return self._candies

    def get_candy(self, pokemon_id):
        self.update()
        try:
            return self._candies[pokemon_id]
        except KeyError:
            return 0

    def add_candy(self, pokemon_id, pokemon_candies):
        self._candies[pokemon_id] += pokemon_candies

    def get_pokeballs(self):
        self.update()
        return self._pokeballs

    def print_stats(self):
        if self.update() is True:
            logger.log('', prefix='#')
            logger.log('Username: {}'.format(self._player.username), prefix='#')
            logger.log('Account creation: {}'.format(self._player.get_creation_date()), prefix='#')
            logger.log('Bag storage: {}/{}'.format(self._inventory['count'], self._player.max_item_storage), prefix='#')
            logger.log('Pokemon storage: {}/{}'.format(len(self._pokemon) + len(self._eggs), self._player.max_pokemon_storage), prefix='#')
            logger.log('Stardust: {:,}'.format(self._player.stardust), prefix='#')
            logger.log('Pokecoins: {}'.format(self._player.pokecoin), prefix='#')
            logger.log('Poke Balls: {}'.format(self._pokeballs[1]), prefix='#')
            logger.log('Great Balls: {}'.format(self._pokeballs[2]), prefix='#')
            logger.log('Ultra Balls: {}'.format(self._pokeballs[3]), prefix='#')
            logger.log('-- Level: {}'.format(self._player.level), prefix='#')
            logger.log('-- Experience: {:,}'.format(self._player.experience), prefix='#')
            logger.log(
                '-- Experience until next level: {:,}'.format(self._player.next_level_xp - self._player.experience), prefix='#')
            logger.log('-- Pokemon captured: {:,}'.format(self._player.pokemons_captured), prefix='#')
            logger.log('-- Pokestops visited: {:,}'.format(self._player.poke_stop_visits), prefix='#')

    def heartbeat(self):
        self._api_wrapper.get_hatched_eggs()
        self._api_wrapper.check_awarded_badges()

        self.update()

    def get_hatched_eggs(self):
        self._api_wrapper.get_hatched_eggs().call()

    def check_awarded_badges(self):
        self._api_wrapper.check_awarded_badges().call()
