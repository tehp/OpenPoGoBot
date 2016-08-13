import unittest

from mock import Mock, patch

from api.player import Player as PlayerData
from pokemongo_bot import Item
from pokemongo_bot.service.player import Player
from pokemongo_bot.tests import create_test_config, create_mock_api_wrapper

def answer(x):
    ints = x
    while ints > 10:
        parts = [int(i) for i in str(ints).split()]
        ints = sum(parts)

class PlayerTest(unittest.TestCase):
    @staticmethod
    def test_login_success():
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        api_wrapper.get_api().login = Mock(return_value=True)

        assert (player_service.login()) is True

    @staticmethod
    def test_login_failure():
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        api_wrapper.get_api().login = Mock(return_value=False)

        assert (player_service.login()) is False

    def test_get_player(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        player = player_service.get_player()

        assert isinstance(player, PlayerData)
        assert player.username == 'test_account'
        assert pgo.call_stack_size() == 0

    def test_get_inventory(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        inventory = player_service.get_inventory()

        assert inventory['count'] == 36
        assert pgo.call_stack_size() == 0

    def test_get_pokemon(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        pokemon = player_service.get_pokemon()

        assert len(pokemon) == 2
        assert pgo.call_stack_size() == 0

    def test_get_candies(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        candies = player_service.get_candies()

        assert len(candies) == 1
        assert candies[1] == 100
        assert pgo.call_stack_size() == 0
        assert pgo.call_stack_size() == 0

    def test_get_candy(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        candies = player_service.get_candy(1)

        assert candies == 100
        assert pgo.call_stack_size() == 0

    def test_get_candy_key_error(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        candies = player_service.get_candy(100)

        assert candies == 0
        assert pgo.call_stack_size() == 0

    def test_add_candy(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        before_candies = player_service.get_candy(1)
        assert before_candies == 100

        player_service.add_candy(1, 3)
        after_candies = player_service.get_candy(1)

        assert after_candies == 103
        assert pgo.call_stack_size() == 0

    def test_get_pokeballs(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        pokeballs = player_service.get_pokeballs()

        assert Item.ITEM_POKE_BALL.value in pokeballs
        assert pokeballs[Item.ITEM_POKE_BALL.value] == 11

        assert Item.ITEM_GREAT_BALL.value in pokeballs
        assert pokeballs[Item.ITEM_GREAT_BALL.value] == 12

        assert Item.ITEM_ULTRA_BALL.value in pokeballs
        assert pokeballs[Item.ITEM_ULTRA_BALL.value] == 13

        assert Item.ITEM_MASTER_BALL.value in pokeballs

        assert pgo.call_stack_size() == 0

    @patch('pokemongo_bot.logger.log', return_value=None)
    def test_print_stats(self, log_fn):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        log_fn.return_value = None

        player_service.print_stats()

        assert log_fn.call_count == 15
        log_fn.assert_any_call('Username: test_account', prefix='#')
        log_fn.assert_any_call('Bag storage: 36/350', prefix='#')
        log_fn.assert_any_call('Pokemon storage: 2/250', prefix='#')
        log_fn.assert_any_call('Stardust: 20,000', prefix='#')
        log_fn.assert_any_call('Pokecoins: 10', prefix='#')
        log_fn.assert_any_call('Poke Balls: 11', prefix='#')
        log_fn.assert_any_call('Great Balls: 12', prefix='#')
        log_fn.assert_any_call('Ultra Balls: 13', prefix='#')
        log_fn.assert_any_call('-- Level: 14', prefix='#')
        log_fn.assert_any_call('-- Experience: 15', prefix='#')
        log_fn.assert_any_call('-- Experience until next level: 985', prefix='#')
        log_fn.assert_any_call('-- Pokemon captured: 17', prefix='#')
        log_fn.assert_any_call('-- Pokestops visited: 18', prefix='#')

        assert pgo.call_stack_size() == 0

    @staticmethod
    @patch('pokemongo_bot.logger.log', return_value=None)
    def test_print_stats_no_update(log_fn):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        api_wrapper.call = Mock(return_value=None)

        log_fn.return_value = None

        player_service.print_stats()

        log_fn.assert_called_once_with('Failed to retrieve player and inventory stats', color='red', prefix='#')

    def test_heartbeat(self):
        config = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config)
        player_service = Player(api_wrapper)

        pgo = api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        player_service.heartbeat()

        assert pgo.call_stack_size() == 0


    @staticmethod
    def _create_generic_player_response():
        return {
            'player_data': {
                'username': 'test_account',
                'max_pokemon_storage': 250,
                'max_item_storage': 350,
                'creation_timestamp_ms': 1470009600000,
                'currencies': [
                    {
                        'name': 'stardust',
                        'amount': 20000,
                    },
                    {
                        'name': 'pokecoin',
                        'amount': 10,
                    }
                ]
            }
        }

    @staticmethod
    def _create_generic_inventory_response():
        return {
            'inventory_delta': {
                'inventory_items': [
                    {
                        'inventory_item_data': {
                            'player_stats': {
                                'level': 14,
                                'experience': 15,
                                'next_level_xp': 1000,
                                'pokemons_captured': 17,
                                'poke_stop_visits': 18
                            }
                        }
                    },
                    {
                        'inventory_item_data': {
                            'candy': {
                                'candy': 100,
                                'family_id': 1
                            }
                        }
                    },
                    {
                        'inventory_item_data': {
                            'pokemon_data': {
                                'id': 123,
                                'pokemon_id': 1,
                                'individual_stamina': 15,
                                'individual_attack': 15,
                                'individual_defense': 10,
                                'cp_multiplier': 0,
                                'cp': 2000,
                            }
                        }
                    },
                    {
                        'inventory_item_data': {
                            'pokemon_data': {
                                'id': 1234,
                                'pokemon_id': 1,
                                'individual_stamina': 9,
                                'individual_attack': 9,
                                'individual_defense': 9,
                                'cp_multiplier': 0,
                                'cp': 10,
                            }
                        }
                    },
                    {
                        'inventory_item_data': {
                            'item': {
                                'item_id': 1,
                                'count': 11,
                            }
                        }
                    },
                    {
                        'inventory_item_data': {
                            'item': {
                                'item_id': 2,
                                'count': 12,
                            }
                        }
                    },
                    {
                        'inventory_item_data': {
                            'item': {
                                'item_id': 3,
                                'count': 13,
                            }
                        }
                    }
                ],
            }
        }
