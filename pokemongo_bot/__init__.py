import googlemaps

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
    service_container.set_parameter('pogoapi.provider', service_container.config["login"]["auth_service"])
    service_container.set_parameter('pogoapi.username', service_container.config["login"]["username"])
    service_container.set_parameter('pogoapi.password', service_container.config["login"]["password"])
    service_container.set_parameter('pogoapi.shared_lib', service_container.config["load_library"])

    service_container.register_singleton('pgoapi', PGoApi())
    service_container.register_singleton('google_maps', googlemaps.Client(key=service_container.config["mapping"]["gmapkey"]))

    if service_container.config["movement"]["path_finder"] in ['google', 'direct']:
        service_container.set_parameter('path_finder', service_container.config["movement"]["path_finder"] + '_path_finder')
    else:
        raise Exception('You must provide a valid path finder')

    if service_container.config["movement"]["navigator"] in ['fort', 'waypoint', 'camper']:
        service_container.set_parameter('navigator', service_container.config["movement"]["navigator"] + '_navigator')
    else:
        raise Exception('You must provide a valid navigator')
