from __future__ import print_function
import time
import random
import os
import json
import jsonpickle

from six import integer_types  # type: ignore

from pgoapi.exceptions import ServerSideRequestThrottlingException, ServerSideAccessForbiddenException, \
    UnexpectedResponseException  # type: ignore
from POGOProtos.Enums import Platform_pb2

from app import kernel
from .state_manager import StateManager
from .exceptions import AccountBannedException

@kernel.container.register('stealth_api', ["@api_wrapper", "@event_manager"])
class StealthApi(object):
    def __init__(self, api_wrapper, event_manager):
        self.api_wrapper = api_wrapper
        self.event_manager = event_manager
        self.state = self.api_wrapper.state.get_state()

        self.download_settings_hash = None

        self.platform = Platform_pb2.ANDROID
        self.version = 3500

    def set_position(self, lat, lng, alt):
        self.api_wrapper.set_position(lat, lng, alt)

    def get_position(self):
        return self.api_wrapper.get_position()

    def login(self):
        return self.api_wrapper.login()

    def init(self):
        # mimic app
        self.api_wrapper.download_remote_config_version(platform=self.platform, app_version=self.version)
        self.api_wrapper.check_challenge()
        self.api_wrapper.get_hatched_eggs()
        self.api_wrapper.get_inventory()
        self.api_wrapper.check_awarded_badges()
        self.api_wrapper.download_settings()
        response_dict = self.api_wrapper.call()
        item_template_update = response_dict["DOWNLOAD_REMOTE_CONFIG_VERSION"]["item_templates_timestamp_ms"]

        self.download_settings_hash = response_dict["download_settings"]["hash"]

        self.api_wrapper.get_asset_digest(platform=self.platform, app_version=self.version)
        self.always()
        self.api_wrapper.call()

        self.get_item_templates(item_template_update)

    def always(self):
        last_inventory_timestamp = self.state.get("inventory_timestamp", 0)

        self.api_wrapper.check_challenge()
        self.api_wrapper.get_hatched_eggs()
        self.api_wrapper.check_awarded_badges()
        self.api_wrapper.get_inventory(last_timestamp_ms=last_inventory_timestamp)
        self.api_wrapper.download_settings(hash=self.download_settings_hash)

    def get_player(self):
        return self.state.get("player", None)

    def get_inventory(self):
        return self.state.get("inventory", None)

    def get_hatched_eggs(self):
        player = self.state.get("player", None)
        return player.hatched_eggs if player else None

    def get_item_templates(self, timestamp=None):
        item_templates = None
        if timestamp is not None:
            last = 0
            if os.path.isfile("data/item_templates.json"):
                with open('data/item_templates.json') as data_file:
                    item_templates = json.load(data_file)
                    last = item_templates["timestamp_ms"]

            if last < timestamp:
                self.api_wrapper.download_item_templates()
                self.always()
                response_dict = self.api_wrapper.call()
                item_templates = response_dict["DOWNLOAD_ITEM_TEMPLATES"]
                with open('data/item_templates.json', 'w') as outfile:
                    json.dump(item_templates, outfile)

        if item_templates is None and os.path.isfile("data/item_templates.json"):
            with open('data/item_templates.json') as data_file:
                item_templates = json.load(data_file)

        item_templates = item_templates["item_templates"] if item_templates is not None else None
        return item_templates

    def get_map_objects(self, latitude, longitude, since_timestamp_ms, cell_id):
        self.api_wrapper.get_map_objects(latitude=latitude, longitude=longitude, since_timestamp_ms=since_timestamp_ms, cell_id=cell_id)
        self.always()
        return self.api_wrapper.call()

    def encounter(self, encounter_id, spawn_point_id, player_latitude, player_longitude):
        self.api_wrapper.encounter(encounter_id=encounter_id,
                                   spawn_point_id=spawn_point_id,
                                   player_latitude=player_latitude,
                                   player_longitude=player_longitude)
        self.always()
        return self.api_wrapper.call()

    def disk_encounter(self, encounter_id, fort_id, player_latitude, player_longitude):
        self.api_wrapper.disk_encounter(encounter_id=encounter_id,
                                        fort_id=fort_id,
                                        player_latitude=player_latitude,
                                        player_longitude=player_longitude)
        self.always()
        return self.api_wrapper.call()

    def catch_pokemon(self, encounter_id, pokeball, normalized_reticle_size, spawn_point_id, hit_pokemon, spin_modifier, normalized_hit_position):
        self.api_wrapper.catch_pokemon(encounter_id=encounter_id,
                                       pokeball=pokeball,
                                       normalized_reticle_size=normalized_reticle_size,
                                       spawn_point_id=spawn_point_id,
                                       hit_pokemon=hit_pokemon,
                                       spin_modifier=spin_modifier,
                                       normalized_hit_position=normalized_hit_position)
        self.always()
        return self.api_wrapper.call()

    def evolve_pokemon(self, pokemon_id):
        self.api_wrapper.evolve_pokemon(pokemon_id=pokemon_id)
        self.always()
        return self.api_wrapper.call()

    def release_pokemon(self, pokemon_id):
        self.api_wrapper.release_pokemon(pokemon_id=pokemon_id)
        self.always()
        return self.api_wrapper.call()

    def set_favorite_pokemon(self, pokemon_id, is_favorite):
        self.api_wrapper.set_favorite_pokemon(pokemon_id=pokemon_id, is_favorite=is_favorite)
        self.always()
        return self.api_wrapper.call()

    def recycle_inventory_item(self, item_id, count):
        self.api_wrapper.recycle_inventory_item(item_id=item_id, count=count)
        self.always()
        return self.api_wrapper.call()

    def use_item_egg_incubator(self, item_id, pokemon_id):
        self.api_wrapper.use_item_egg_incubator(item_id=item_id, pokemon_id=pokemon_id)
        self.always()
        return self.api_wrapper.call()

    def level_up_rewards(self, level):
        self.api_wrapper.level_up_rewards(level=level)
        self.always()
        return self.api_wrapper.call()

    def fort_search(self, fort_id, fort_latitude, fort_longitude, player_latitude, player_longitude):
        self.api_wrapper.fort_search(fort_id=fort_id,
                                     fort_latitude=fort_latitude,
                                     fort_longitude=fort_longitude,
                                     player_latitude=player_latitude,
                                     player_longitude=player_longitude)
        self.always()
        return self.api_wrapper.call()

    def fort_details(self, fort_id, latitude, longitude):
        self.api_wrapper.fort_details(fort_id=fort_id,
                                      latitude=latitude,
                                      longitude=longitude)
        self.always()
        return self.api_wrapper.call()
