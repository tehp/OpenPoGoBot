import json
import logging
import os
import unittest

import pytest
from mock import Mock, patch, call

from api.pokemon import Pokemon
from api.worldmap import Cell, PokeStop
from pokemongo_bot import PokemonGoBot
from pokemongo_bot.event_manager import EventManager
from pokemongo_bot.mapper import Mapper
from pokemongo_bot.navigation import FortNavigator
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.service.player import Player
from pokemongo_bot.service.pokemon import Pokemon as PokemonService
from pokemongo_bot.stepper import Stepper
from pokemongo_bot.tests import create_mock_api_wrapper, create_core_test_config


class BotTest(unittest.TestCase):
    @staticmethod
    def test_init():
        logger = Mock()
        logger.log = Mock(return_value=None)

        config_namespace = create_core_test_config()
        api_wrapper = create_mock_api_wrapper(config_namespace)
        event_manager = EventManager()
        player_service = Player(api_wrapper, event_manager, logger)
        pokemon_service = PokemonService(api_wrapper)
        mapper = Mapper(config_namespace, api_wrapper, Mock(), logger)
        path_finder = DirectPathFinder(config_namespace)
        stepper = Stepper(config_namespace, api_wrapper, path_finder, logger)
        navigator = FortNavigator(config_namespace, api_wrapper)

        bot = PokemonGoBot(config_namespace, api_wrapper, player_service, pokemon_service, event_manager, mapper, stepper, navigator, logger)

        assert len(bot.pokemon_list) == 151
        assert len(bot.item_list) == 30
        assert bot.position == (0, 0, 0)

        assert bot.config is config_namespace
        assert bot.api_wrapper is api_wrapper
        assert bot.player_service is player_service
        assert bot.pokemon_service is pokemon_service
        assert bot.event_manager is event_manager
        assert bot.mapper is mapper
        assert bot.stepper is stepper
        assert bot.navigator is navigator
        assert bot.logger is logger

    def test_start_login_success_no_debug(self):
        bot = self._create_generic_bot({
            'plugins': {
                'exclude': ['another_test_plugin'],
            },
            'mapping': {
                'location': '51.5037053,-0.2047603',
                'location_cache': False,
            }
        })

        bot.mapper.google_maps.elevation = Mock(return_value=[{'elevation': 10.1}])

        bot.event_manager.fire_with_context = Mock()

        pgo = bot.api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())
        pgo.set_response('DOWNLOAD_REMOTE_CONFIG_VERSION', self._create_generic_remote_config)

        bot.player_service.print_stats = Mock(return_value=None)

        bot.start()

        # Assert print stats is called
        bot.player_service.print_stats.assert_called_once()

        bot.event_manager.fire_with_context.assert_has_calls([
            call('bot_initialized', bot),
        ])

        # Check logging
        assert logging.getLogger('requests').level == logging.ERROR
        assert logging.getLogger('pgoapi').level == logging.ERROR
        assert logging.getLogger('rpc_api').level == logging.ERROR

        # Check events
        assert bot.event_manager.fire_with_context.call_count == 1

    def test_start_login_success_with_debug(self):
        bot = self._create_generic_bot({
            'debug': True,
            'plugins': {
                'exclude': ['another_test_plugin'],
            },
            'mapping': {
                'location': 'Tower Bridge, London',
                'location_cache': False,
            }
        })

        bot.mapper.google_maps.elevation = Mock(return_value=[{'elevation': 10.1}])

        bot.event_manager.fire_with_context = Mock()

        pgo = bot.api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())
        pgo.set_response('DOWNLOAD_REMOTE_CONFIG_VERSION', self._create_generic_remote_config)

        bot.start()

        # TODO: assert print stats called

        bot.event_manager.fire_with_context.assert_has_calls([
            call('bot_initialized', bot),
        ])

        # Check logging
        assert logging.getLogger('requests').level == logging.DEBUG
        assert logging.getLogger('pgoapi').level == logging.DEBUG
        assert logging.getLogger('rpc_api').level == logging.DEBUG

        # Check events
        assert bot.event_manager.fire_with_context.call_count == 1

    def test_start_login_success_location_cache_not_exists(self):
        account = 'test_account-test_start_login_success_location_cache_not_exists'
        bot = self._create_generic_bot({
            'login': {
                'username': account
            },
            'plugins': {
                'exclude': ['another_test_plugin'],
            },
            'mapping': {
                'location': None,
                'location_cache': True,
            }
        })

        pgo.set_response('DOWNLOAD_REMOTE_CONFIG_VERSION', self._create_generic_remote_config)

        if os.path.isfile('data/last-location-'+account+'.json'):
            os.unlink('data/last-location-'+account+'.json')

        bot.logger.log.return_value = None

        bot.event_manager.fire_with_context = Mock()

        with pytest.raises(SystemExit):
            bot.start()

    def test_start_login_success_location_cache(self):
        account = 'test_account-test_start_login_success_location_cache'
        bot = self._create_generic_bot({
            'login': {
                'username': account
            },
            'plugins': {
                'exclude': ['another_test_plugin'],
            },
            'mapping': {
                'location': '0,0',
                'location_cache': True,
            }
        })

        if os.path.isfile('data/last-location-'+account+'.json'):
            os.unlink('data/last-location-'+account+'.json')

        with open('data/last-location-'+account+'.json', 'w') as location_file:
            location_file.write(json.dumps({'lat': 51.5037053, 'lng': -0.2047603}))

        bot.logger.log.return_value = None

        bot.mapper.google_maps.elevation = Mock(return_value=[{'elevation': 10.1}])

        bot.event_manager.fire_with_context = Mock()

        pgo = bot.api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())
        pgo.set_response('DOWNLOAD_REMOTE_CONFIG_VERSION', self._create_generic_remote_config)

        bot.start()

        bot.event_manager.fire_with_context.assert_has_calls([
            call('bot_initialized', bot),
        ])

        # Check events
        assert bot.event_manager.fire_with_context.call_count == 1

        os.unlink('data/last-location-'+account+'.json')

    def test_start_login_failed(self):
        bot = self._create_generic_bot({
            'plugins': {
                'exclude': ['another_test_plugin'],
            },
            'mapping': {
                'location': '0,0',
                'location_cache': True,
            }
        })

        bot.mapper.google_maps.elevation = Mock(return_value=[{'elevation': 10.1}])

        bot.event_manager.fire_with_context = Mock()

        pgo = bot.api_wrapper.get_api()
        pgo.should_login = [False, False, True]
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())
        pgo.set_response('DOWNLOAD_REMOTE_CONFIG_VERSION', self._create_generic_remote_config)

        with patch('time.sleep', return_value=None) as sleep:
            bot.start()

            sleep.assert_any_call(15)

        bot.logger.log.assert_any_call('Login Error, server busy', color='red')
        bot.logger.log.assert_any_call('Waiting 15 seconds before trying again...')

    def test_run(self):
        bot = self._create_generic_bot({})
        bot.api_wrapper.set_location(51.504154, -0.076304, 10)
        bot.stepper.current_lat = 51.504154
        bot.stepper.current_lng = -0.076304
        bot.stepper.current_alt = 10

        pgo = bot.api_wrapper.get_api()
        pgo.should_login = [False, False, True]
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())
        pgo.set_response('DOWNLOAD_REMOTE_CONFIG_VERSION', self._create_generic_remote_config)

        bot.mapper.get_cells = Mock(return_value=[
            Cell({}),
            Cell({})
        ])

        def navigator(cells):  # pylint: disable=unused-argument
            destinations = [
                Destination(51.504601, -0.075964, 10),
                Destination(51.505356, -0.075481, 11)
            ]
            for destination in destinations:
                yield destination

        bot.navigator.navigate = navigator

        def stepper_get_route_between(position_lat, position_lng, target_lat, target_lng, target_alt):
            return [
                (position_lat, position_lng, 0),
                (position_lat + (target_lat - position_lat) / 2, position_lng + (target_lng - position_lng) / 2, 0),
                (target_lat, target_lng, target_alt)
            ]

        bot.stepper.get_route_between = stepper_get_route_between

        def stepper_step(destination):
            for step in destination.step():
                yield step
                bot.stepper.current_lat = step[0]
                bot.stepper.current_lng = step[1]
                bot.stepper.current_alt = step[2]

        bot.stepper.step = stepper_step

        bot.player_service.heartbeat = Mock(return_value=None)

        bot.run()

    def test_work_on_cells(self):
        bot = self._create_generic_bot({})
        bot.fire = Mock()

        poke1 = Pokemon({'id': 1})
        poke2 = Pokemon({'id': 2})
        poke3 = Pokemon({'id': 3})
        poke4 = Pokemon({'id': 4})
        poke5 = Pokemon({'id': 5})
        poke6 = Pokemon({'id': 6})
        pokestop1 = PokeStop({'id': 1})
        pokestop2 = PokeStop({'id': 2})
        pokestop3 = PokeStop({'id': 3})

        cell1 = Cell({})
        cell1.catchable_pokemon = [poke1, poke2]
        cell1.wild_pokemon = [poke3, poke4]
        cell1.pokestops = [pokestop1, pokestop2]

        cell2 = Cell({})
        cell2.catchable_pokemon = [poke5]
        cell2.wild_pokemon = [poke6]
        cell2.pokestops = [pokestop3]

        bot.work_on_cells([cell1, cell2])

        assert bot.fire.call_count == 2

        bot.fire.has_calls([
            call('pokemon_found', encounters=[poke1, poke2, poke3, poke4, poke5, poke6]),
            call('pokestops_found', encounters=[pokestop1, pokestop2, pokestop3])
        ])

    def test_get_username(self):
        bot = self._create_generic_bot({
            'plugins': {
                'exclude': ['another_test_plugin'],
            },
            'mapping': {
                'location': '51.5037053,-0.2047603',
                'location_cache': False,
            }
        })
        bot.mapper.google_maps.elevation = Mock(return_value=[{'elevation': 10.1}])
        bot.player_service.print_stats = Mock(return_value=None)

        pgo = bot.api_wrapper.get_api()
        pgo.set_response('get_player', self._create_generic_player_response())
        pgo.set_response('get_inventory', self._create_generic_inventory_response())
        pgo.set_response('DOWNLOAD_REMOTE_CONFIG_VERSION', self._create_generic_remote_config)

        bot.api_wrapper.get_player()

        assert (bot.get_username()) == 'test_account'

    def test_get_username_unknown(self):
        bot = self._create_generic_bot({})
        bot.player_service.get_player = Mock(return_value=None)

        assert (bot.get_username()) == 'Unknown'

    @staticmethod
    def _create_generic_bot(config):
        logger = Mock()
        logger.log = Mock()
        config_namespace = create_core_test_config(config)
        api_wrapper = create_mock_api_wrapper(config_namespace)
        event_manager = Mock()
        player_service = Player(api_wrapper, event_manager, logger)
        pokemon_service = PokemonService(api_wrapper)
        mapper = Mapper(config_namespace, api_wrapper, Mock(), logger)
        path_finder = DirectPathFinder(config_namespace)
        stepper = Stepper(config_namespace, api_wrapper, path_finder, logger)
        navigator = FortNavigator(config_namespace, api_wrapper)

        return PokemonGoBot(
            config_namespace,
            api_wrapper,
            player_service,
            pokemon_service,
            event_manager,
            mapper,
            stepper,
            navigator,
            logger
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
    def _create_generic_remote_config():
        return {
            'DOWNLOAD_REMOTE_CONFIG_VERSION': {
                'item_templates_timestamp_ms': -1
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
