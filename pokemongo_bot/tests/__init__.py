from argparse import Namespace

from mock import Mock, MagicMock

import pokemongo_bot
from pokemongo_bot import Stepper
import pgoapi
import api


def create_mock_api_wrapper():
    pgoapi_instance = pgoapi.PGoApi()
    positions = []
    calls = []
    call_responses = []

    def _set_position(lat, lng, alt):
        positions.append((lat, lng, alt))
        return None

    def _get_position():
        return positions[len(positions) - 1]

    def _add_request(func):
        def function(*args, **kwargs):
            func_name = str(func).upper()
            calls.append((func_name, args, kwargs))
            return pgoapi_instance

        return function()

    def _set_request(call_type, response):
        call_responses.append((call_type, response))

    def _create_request():
        request = Mock()
        call_type, call_response = call_responses.pop(0)
        if call_response is None:
            request.call = MagicMock(return_value=None)
        else:
            request.call = MagicMock(return_value={
                "responses": {
                    call_type.upper(): call_response
                }
            })

        # print("creating request for {} ({})...".format(call_type, call_response))
        setattr(request, call_type, call_response)

        return request

    pgoapi_instance.activate_signature = MagicMock(return_value=None)
    pgoapi_instance.login = MagicMock(return_value=True)
    pgoapi_instance.set_position = _set_position
    pgoapi_instance.get_position = _get_position
    pgoapi_instance.list_curr_methods = MagicMock(return_value=[])
    pgoapi_instance.create_request = _create_request
    pgoapi_instance.__getattr__ = _add_request
    pgoapi_instance.set_response = _set_request

    api_wrapper = api.PoGoApi(api=pgoapi_instance)
    api_wrapper.get_expiration_time = MagicMock(return_value=1000000)

    return api_wrapper


def create_mock_bot(user_config=None):
    if user_config is None:
        user_config = {}

    config = {
        "debug": False,
        "path_finder": None,
        "walk": 4.16,
        "max_steps": 2,
    }
    config.update(user_config)

    config_namespace = Namespace(**config)

    bot = pokemongo_bot.PokemonGoBot(config_namespace)
    bot.api_wrapper = create_mock_api_wrapper()
    bot.stepper = Stepper(bot)

    return bot
