import logging
import os
import unittest
import sys
from argparse import Namespace
from io import StringIO

import geopy
from mock import Mock, patch, call

import api
import pokemongo_bot
from pokemongo_bot.event_manager import EventManager
from pokemongo_bot.mapper import Mapper
from pokemongo_bot.navigation import FortNavigator
from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.plugins import PluginManager
from pokemongo_bot.service.player import Player
from pokemongo_bot.service.pokemon import Pokemon
from pokemongo_bot.stepper import Stepper
from pokemongo_bot.tests import create_mock_api_wrapper, create_test_config


class BotTest(unittest.TestCase):
    @staticmethod
    def test_init():
        config_namespace = create_test_config({})
        api_wrapper = create_mock_api_wrapper(config_namespace)
        plugin_manager = PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')
        player_service = Player(api_wrapper)
        pokemon_service = Pokemon(api_wrapper)
        mapper = Mapper(config_namespace, api_wrapper)
        path_finder = DirectPathFinder(config_namespace)
        stepper = Stepper(config_namespace, api_wrapper, path_finder)
        navigator = FortNavigator(config_namespace, api_wrapper)
        event_manager = EventManager()

        bot = pokemongo_bot.PokemonGoBot(config_namespace, api_wrapper, player_service, pokemon_service, plugin_manager,
                                         event_manager, mapper, stepper, navigator)

        assert len(bot.pokemon_list) == 151
        assert len(bot.item_list) == 30
        assert bot.position == (0, 0, 0)
        assert bot.last_session_check > 0

        assert bot.config is config_namespace
        assert bot.api_wrapper is api_wrapper
        assert bot.player_service is player_service
        assert bot.pokemon_service is pokemon_service
        assert bot.plugin_manager is plugin_manager
        assert bot.event_manager is event_manager
        assert bot.mapper is mapper
        assert bot.stepper is stepper
        assert bot.navigator is navigator

    @patch('pokemongo_bot.event_manager.manager', new_callable=EventManager)
    @patch('googlemaps.Client')
    @patch('geopy.geocoders.GoogleV3')
    @patch('pokemongo_bot.logger.log', return_value=None)
    def test_start_login_success_no_debug(self, log_fn, google_v3, google_client, event_manager):
        bot = self._create_generic_bot({
            'debug': False,
            'test': False,
            'exclude_plugins': ['another_test_plugin'],
            'load_library': 'libencrypt.so',
            'auth_service': 'ptc',
            'username': 'test_bot_account',
            'password': 'pa55w0rd',
            'location': '51.5037053,-0.2047603',
            'location_cache': False,
            'gmapkey': 'test_gmaps_key',
            'initial_transfer': True,
            'recycle_items': True
        })

        geocoder = Mock()
        location = Mock()
        location.latitude = 51.5037053
        location.longitude = -0.2047603
        location.altitude = 10

        geocoder.geocode = Mock(return_value=location)
        google_v3.return_value = geocoder

        event_manager.fire_with_context = Mock()
        bot.event_manager = event_manager

        google_client.elevation = Mock(return_value=[
            {
                'elevation': {

                }
            }
        ])

        pgo = bot.api_wrapper._api
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        bot.start()

        assert log_fn.call_count == 26
        log_fn.assert_any_call('Plugins loaded: [\'test_plugin\']', color='green', prefix='Plugins')
        log_fn.assert_any_call('Events available: [\'test\']', color='green', prefix='Events')

        log_fn.assert_any_call('[x] Fetching altitude from google')
        log_fn.assert_any_call('[x] Location was not Lat/Lng.')

        log_fn.assert_any_call('[#] Username: test_account')
        log_fn.assert_any_call('[#] Account creation: 2016-08-01 01:00:00')
        log_fn.assert_any_call('[#] Bag storage: 36/350')
        log_fn.assert_any_call('[#] Pokemon storage: 2/250')
        log_fn.assert_any_call('[#] Stardust: 20,000')
        log_fn.assert_any_call('[#] Pokecoins: 10')
        log_fn.assert_any_call('[#] Poke Balls: 11')
        log_fn.assert_any_call('[#] Great Balls: 12')
        log_fn.assert_any_call('[#] Ultra Balls: 13')
        log_fn.assert_any_call('[#] -- Level: 14')
        log_fn.assert_any_call('[#] -- Experience: 15')
        log_fn.assert_any_call('[#] -- Experience until next level: 985')
        log_fn.assert_any_call('[#] -- Pokemon captured: 17')
        log_fn.assert_any_call('[#] -- Pokestops visited: 18')

        bot.event_manager.fire_with_context.assert_has_calls([
            call('bot_initialized', bot),
            call('pokemon_bag_full', bot),
            call('item_bag_full', bot)
        ])

        # Check logging
        assert logging.getLogger('requests').level == logging.ERROR
        assert logging.getLogger('pgoapi').level == logging.ERROR
        assert logging.getLogger('rpc_api').level == logging.ERROR

        # Check Plugins
        assert len(bot.plugin_manager.get_loaded_plugins()) == 1
        assert 'test_plugin' in bot.plugin_manager.get_loaded_plugins()

        # Check events
        assert bot.event_manager.fire_with_context.call_count == 3

    @patch('pokemongo_bot.event_manager.manager', new_callable=EventManager)
    @patch('geopy.geocoders.GoogleV3')
    @patch('pokemongo_bot.logger.log', return_value=None)
    def test_start_login_success_with_debug(self, log_fn, google_v3, event_manager):
        bot = self._create_generic_bot({
            'debug': True,
            'test': False,
            'exclude_plugins': ['another_test_plugin'],
            'load_library': 'libencrypt.so',
            'auth_service': 'ptc',
            'username': 'test_bot_account',
            'password': 'pa55w0rd',
            'location': '51.5037053,-0.2047603',
            'location_cache': False,
            'gmapkey': 'test_gmaps_key',
            'initial_transfer': True,
            'recycle_items': True
        })

        geocoder = Mock()
        location = Mock()
        location.latitude = 51.5037053
        location.longitude = -0.2047603
        location.altitude = 10

        geocoder.geocode = Mock(return_value=location)
        google_v3.return_value = geocoder

        event_manager.fire_with_context = Mock()
        bot.event_manager = event_manager

        pgo = bot.api_wrapper._api
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())

        bot.start()

        assert log_fn.call_count == 26
        log_fn.assert_any_call('Plugins loaded: [\'test_plugin\']', color='green', prefix='Plugins')
        log_fn.assert_any_call('Events available: [\'test\']', color='green', prefix='Events')

        log_fn.assert_any_call('[x] Fetching altitude from google')
        log_fn.assert_any_call('[x] Location was not Lat/Lng.')

        log_fn.assert_any_call('[#] Username: test_account')
        log_fn.assert_any_call('[#] Account creation: 2016-08-01 01:00:00')
        log_fn.assert_any_call('[#] Bag storage: 36/350')
        log_fn.assert_any_call('[#] Pokemon storage: 2/250')
        log_fn.assert_any_call('[#] Stardust: 20,000')
        log_fn.assert_any_call('[#] Pokecoins: 10')
        log_fn.assert_any_call('[#] Poke Balls: 11')
        log_fn.assert_any_call('[#] Great Balls: 12')
        log_fn.assert_any_call('[#] Ultra Balls: 13')
        log_fn.assert_any_call('[#] -- Level: 14')
        log_fn.assert_any_call('[#] -- Experience: 15')
        log_fn.assert_any_call('[#] -- Experience until next level: 985')
        log_fn.assert_any_call('[#] -- Pokemon captured: 17')
        log_fn.assert_any_call('[#] -- Pokestops visited: 18')

        bot.event_manager.fire_with_context.assert_has_calls([
            call('bot_initialized', bot),
            call('pokemon_bag_full', bot),
            call('item_bag_full', bot)
        ])

        # Check logging
        assert logging.getLogger('requests').level == logging.DEBUG
        assert logging.getLogger('pgoapi').level == logging.DEBUG
        assert logging.getLogger('rpc_api').level == logging.DEBUG

        # Check Plugins
        self._assert_plugins_loaded(bot.plugin_manager, ['test_plugin'])

        # Check events
        assert bot.event_manager.fire_with_context.call_count == 3

    @staticmethod
    def _assert_plugins_loaded(plugin_manager, plugins):
        # type: (PluginManager, List[String]) -> None
        assert len(plugin_manager.get_loaded_plugins()) == len(plugins)
        for plugin in plugins:
            assert plugin in plugin_manager.get_loaded_plugins()

    @staticmethod
    def _create_generic_bot(config):
        config_namespace = create_test_config(config)
        api_wrapper = create_mock_api_wrapper(config_namespace)
        plugin_manager = PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')
        player_service = Player(api_wrapper)
        pokemon_service = Pokemon(api_wrapper)
        mapper = Mapper(config_namespace, api_wrapper)
        path_finder = DirectPathFinder(config_namespace)
        stepper = Stepper(config_namespace, api_wrapper, path_finder)
        navigator = FortNavigator(config_namespace, api_wrapper)
        event_manager = Mock()

        return pokemongo_bot.PokemonGoBot(
            config_namespace,
            api_wrapper,
            player_service,
            pokemon_service,
            plugin_manager,
            event_manager,
            mapper,
            stepper,
            navigator
        )

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
