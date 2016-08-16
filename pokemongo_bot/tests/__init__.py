import collections
import os
import uuid
from argparse import Namespace
from future.utils import viewitems

from mock import Mock, MagicMock
import pgoapi

from app import Kernel
from app.plugin_manager import PluginManager
from pokemongo_bot import FortNavigator, PokemonGoBot
from pokemongo_bot.event_manager import EventManager
from pokemongo_bot.logger import Logger
from pokemongo_bot.mapper import Mapper
from pokemongo_bot.navigation.path_finder import DirectPathFinder
from pokemongo_bot.service.player import Player
from pokemongo_bot.service.pokemon import Pokemon
from pokemongo_bot.stepper import Stepper
import api


# pylint: disable=super-init-not-called
class PGoApiMock(pgoapi.PGoApi):
    def __init__(self):
        self.positions = list()
        self.call_responses = list()
        self.should_login = []

    # pylint: disable=unused-argument,no-self-use
    def activate_signature(self, shared_lib):
        return None

    # pylint: disable=unused-argument,no-self-use
    def login(self, provider, username, password, lat=None, lng=None, alt=None, app_simulation=True):
        if len(self.should_login):
            return self.should_login.pop(0)
        else:
            return True

    def set_position(self, lat, lng, alt):
        self.positions.append((lat, lng, alt))
        return None

    def get_position(self):
        return self.positions[len(self.positions) - 1]

    # pylint: disable=no-self-use
    def list_curr_methods(self):
        return list()

    def set_response(self, call_type, response):
        self.call_responses.append((call_type, response))

    def create_request(self):
        return PGoApiRequestMock(self)

    def call_stack_size(self):
        return len(self.call_responses)


# pylint: disable=super-init-not-called
class PGoApiRequestMock(pgoapi.pgoapi.PGoApiRequest):
    def __init__(self, pgo):
        self.pgoapi = pgo
        self.calls = []

    def call(self):
        return_values = {}

        for call in self.calls:
            call_name, _, _ = call
            if len(self.pgoapi.call_responses) == 0:
                raise RuntimeError("Response for \"{}\" expected, but none was set".format(call_name))

            call_response_name, call_response_data = self.pgoapi.call_responses.pop(0)

            if call_name.upper() != call_response_name.upper():
                raise RuntimeError(
                    "Response expected for \"{}\", but the next response was for \"{}\"".format(call_name,
                                                                                                call_response_name))

            if call_response_data is not None:
                return_values[call_response_name.upper()] = call_response_data

        if len(return_values) > 0:
            return {
                'status_code': 1,
                'responses': return_values
            }
        else:
            return None

    def __getattr__(self, func):

        def function(*args, **kwargs):
            func_name = str(func).upper()
            self.calls.append((func_name, args, kwargs))
            return self

        return function


def create_mock_api_wrapper(config):
    # type: (Dict) -> PoGoApi
    pgoapi_instance = PGoApiMock()
    api_wrapper = api.PoGoApi(pgoapi_instance, config)
    api_wrapper.get_expiration_time = MagicMock(return_value=1000000)
    api_wrapper.set_position(0, 0, 0)
    return api_wrapper


def create_test_kernel(user_config=None):
    # type: (Dict) -> ServiceContainer

    kernel = Kernel()

    config = create_core_test_config(user_config)

    kernel.container.register_singleton('config', config)
    kernel.container.register_singleton('pgoapi', PGoApiMock())
    kernel.container.register_singleton(
        'plugin_manager',
        PluginManager(os.path.dirname(os.path.realpath(__file__)) + '/plugins')
    )
    kernel.container.register_singleton('event_manager', EventManager())

    kernel.container.set_parameter('path_finder', config['movement']['path_finder'])
    kernel.container.set_parameter('navigator', config['movement']['path_finder'])

    return kernel


def create_core_test_config(user_config=None):
    # type: (Dict) -> Namespace
    if user_config is None:
        user_config = {}

    config = {
        "load_library": "libencrypt.so",
        "debug": False,
        "login": {
            "auth_service": "ptc",
            "username": "testaccount",
            "password": "test123",
        },
        "mapping": {
            "gmapskey": "test_key",
            "location": None,
            "location_cache": False,
            "distance_unit": "km",
        },
        "movement": {
            "path_finder": "direct",
            "navigator": "fort",
            "navigator_waypoints": [],
            "navigator_campsite": None,
            "walk_speed": 4.16,
        },
        "plugins": {
            "exclude": [],
            "include": ['./tests/plugins'],
            "config": "config/plugins"
        }
    }

    config = _merge_config(config, user_config)

    return config


def create_mock_bot(user_config=None):
    config_namespace = create_core_test_config(user_config)

    event_manager = EventManager()
    logger = Logger(event_manager)
    api_wrapper = create_mock_api_wrapper(config_namespace)
    player_service = Player(api_wrapper, logger)
    pokemon_service = Pokemon(api_wrapper)
    mapper = Mapper(config_namespace, api_wrapper, Mock(), logger)
    path_finder = DirectPathFinder(config_namespace)
    stepper = Stepper(config_namespace, api_wrapper, path_finder, logger)
    navigator = FortNavigator(config_namespace, api_wrapper)

    bot = PokemonGoBot(
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

    return bot


def test_account_name():
    return 'test_account-' + str(uuid.uuid1())


def _merge_config(d, u):
    for k, v in viewitems(u):
        if isinstance(v, collections.Mapping):
            r = _merge_config(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
