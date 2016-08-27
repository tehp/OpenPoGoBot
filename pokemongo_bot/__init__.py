import os
import sys
import uuid

import googlemaps
import jsonpickle
from pgoapi import PGoApi

from app import kernel
from pokemongo_bot.bot import PokemonGoBot
from pokemongo_bot.event_manager import EventManager
from pokemongo_bot.logger import Logger
from pokemongo_bot.mapper import Mapper
from pokemongo_bot.stepper import Stepper
from pokemongo_bot.navigation import CamperNavigator, FortNavigator, WaypointNavigator
from pokemongo_bot.navigation.path_finder import DirectPathFinder, GooglePathFinder
from pokemongo_bot.service import Player, Pokemon


@kernel.container.register_compiler_pass()
def boot(service_container):
    # PoGoApi parameters
    config = service_container.get('config.core')

    if os.path.isfile(os.path.join(os.getcwd(), config['load_library'])):
        config['load_library'] = os.path.join(os.getcwd(), config['load_library'])

    service_container.set_parameter('pogoapi.provider', config['login']['auth_service'])
    service_container.set_parameter('pogoapi.username', config['login']['username'])
    service_container.set_parameter('pogoapi.password', config['login']['password'])
    service_container.set_parameter('pogoapi.shared_lib', config['load_library'])

    if config['device_info'] is not None:
        device_info = dict(config['device_info'])
        if device_info["device_id"] is None:
            device_info["device_id"] = uuid.uuid4().hex
        service_container.set_parameter('pogoapi.device_info', jsonpickle.encode(device_info))

    service_container.register_singleton('pgoapi', PGoApi())
    service_container.register_singleton('google_maps', googlemaps.Client(key=config["mapping"]["gmapkey"]))

    if config['movement']['path_finder'] in ['google', 'direct']:
        service_container.set_parameter('path_finder', config['movement']['path_finder'] + '_path_finder')
    else:
        raise Exception('You must provide a valid path finder')

    if config['movement']['navigator'] in ['fort', 'waypoint', 'camper']:
        service_container.set_parameter('navigator', config['movement']['navigator'] + '_navigator')
    else:
        raise Exception('You must provide a valid navigator')
