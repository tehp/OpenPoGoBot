# pylint: disable=unused-argument
from __future__ import print_function

from api.evolution_result import EvolutionResult
from .player import Player
from .inventory_parser import InventoryParser
from .worldmap import WorldMap, Gym, PokeStop
from .encounter import Encounter
from .item import Incubator
from .exceptions import AccountBannedException

class StateManager(object):
    def __init__(self):

        # Transforms response data from the server to objects.
        # Use self._noop if there is no response data.
        self.response_map = {
            "CHECK_CHALLENGE": self._verify_challenge,
            "GET_PLAYER": self._parse_player,
            "GET_INVENTORY": self._parse_inventory,
            "GET_MAP_OBJECTS": self._parse_map,
            "ENCOUNTER": self._parse_encounter,
            "DISK_ENCOUNTER": self._parse_disk_encounter,
            "RELEASE_POKEMON": self._noop,
            "CATCH_POKEMON": self._parse_catch_pokemon,
            "PLAYER_UPDATE": self._noop,
            "CHECK_AWARDED_BADGES": self._identity,
            "FORT_DETAILS": self._parse_fort,
            "FORT_SEARCH": self._identity,
            "RECYCLE_INVENTORY_ITEM": self._noop,
            "USE_ITEM_EGG_INCUBATOR": self._parse_use_incubator,
            "GET_HATCHED_EGGS": self._parse_get_hatched_eggs,
            "EVOLVE_POKEMON": self._parse_evolution,
            "DOWNLOAD_SETTINGS": self._dl_settings,
            "DOWNLOAD_ITEM_TEMPLATES": self._identity,
            "DOWNLOAD_REMOTE_CONFIG_VERSION": self._identity,
            "GET_ASSET_DIGEST": self._identity,
            "SET_FAVORITE_POKEMON": self._identity,
            "LEVEL_UP_REWARDS": self._identity
        }

        # Maps methods to the state objects that they refresh.
        # Used for caching.
        self.method_returns_states = {
            "GET_PLAYER": ["player"],
            "GET_INVENTORY": ["player", "inventory", "pokemon", "pokedex", "candy", "eggs"],
            "USE_ITEM_EGG_INCUBATOR": ["egg_incubators"],
            "GET_HATCHED_EGGS": [],
            "CHECK_AWARDED_BADGES": ["CHECK_AWARDED_BADGES"],
            "CHECK_CHALLENGE": ["CHECK_CHALLENGE"],
            "DOWNLOAD_SETTINGS": ["DOWNLOAD_SETTINGS"],
            "DOWNLOAD_REMOTE_CONFIG_VERSION": ["DOWNLOAD_REMOTE_CONFIG_VERSION"],
            "GET_ASSET_DIGEST": ["GET_ASSET_DIGEST"],
            "GET_MAP_OBJECTS": ["worldmap"],
            "ENCOUNTER": ["encounter"],
            "DISK_ENCOUNTER": [],
            "RELEASE_POKEMON": [],
            "PLAYER_UPDATE": [],
            "FORT_DETAILS": ["fort"],
            "FORT_SEARCH": ["FORT_SEARCH"],
            "RECYCLE_INVENTORY_ITEM": [],
            "EVOLVE_POKEMON": ["evolution"],
            "DOWNLOAD_ITEM_TEMPLATES": ["DOWNLOAD_ITEM_TEMPLATES"],
            "SET_FAVORITE_POKEMON": ["SET_FAVORITE_POKEMON"],
            "LEVEL_UP_REWARDS": []
        }

        # Maps methods to the state objects that they invalidate.
        # (ie. require another API call to get the correct data)
        # If a method needs to always be called, ensure that it
        # mutates at least one state.
        # Used for caching.
        self.method_mutates_states = {
            "GET_PLAYER": ["GET_PLAYER"],
            "GET_INVENTORY": [],
            "USE_ITEM_EGG_INCUBATOR": ["egg_incubators"],
            "GET_HATCHED_EGGS": ["GET_HATCHED_EGGS"],
            "CHECK_AWARDED_BADGES": ["CHECK_AWARDED_BADGES"],
            "CHECK_CHALLENGE": ["CHECK_CHALLENGE"],
            "DOWNLOAD_SETTINGS": ["DOWNLOAD_SETTINGS"],
            "DOWNLOAD_REMOTE_CONFIG_VERSION": ["DOWNLOAD_REMOTE_CONFIG_VERSION"],
            "GET_ASSET_DIGEST": ["GET_ASSET_DIGEST"],
            "GET_MAP_OBJECTS": ["worldmap"],
            "ENCOUNTER": ["encounter", "player", "pokedex"],
            "DISK_ENCOUNTER": ["encounter"],
            "RELEASE_POKEMON": ["pokemon", "candy"],
            "CATCH_POKEMON": ["encounter", "player", "pokemon", "pokedex", "candy", "inventory"],
            "PLAYER_UPDATE": ["player", "inventory"],
            "FORT_DETAILS": ["fort"],
            "FORT_SEARCH": ["player", "inventory", "eggs"],
            "RECYCLE_INVENTORY_ITEM": ["inventory"],
            "EVOLVE_POKEMON": ["player", "inventory", "pokemon", "pokedex", "candy"],
            "DOWNLOAD_ITEM_TEMPLATES": [],
            "SET_FAVORITE_POKEMON": ["pokemon"],
            "LEVEL_UP_REWARDS": ["inventory"]
        }

        self.current_state = {}

        self.staleness = {}

    def _noop(self, *args, **kwargs):
        pass

    def is_stale(self, key):
        return self.staleness.get(key, True)

    # Check whether a method is cached or if it needs to be updated.
    def is_method_cached(self, method):
        return False

    # Filter the list of methods so that only uncached methods (or methods that will become
    # uncached) and state-invalidating methods will be called. Note that the order is
    # important - calling GET_INVENTORY before FORT_SEARCH, for example, will return the cached
    # and now invalidated inventory object. To fix, call FORT_SEARCH and then GET_INVENTORY.
    def filter_cached_methods(self, method_keys):
        return method_keys

    # Update a state object and mark it as valid.
    def _update_state(self, data):
        for key in data:
            value = data.get(key, None)
            if value is None:
                continue
            self.current_state[key] = data[key]
            self.staleness[key] = False

    def get_state(self):
        return self.current_state

    # Get only the following state objects from the current state.
    def get_state_filtered(self, keys):
        return_object = {}
        for key in keys:
            return_object[key] = self.current_state.get(key, None)
        return self.current_state

    # Mark the states affected by the given methods as invalid/stale.
    def mark_stale(self, methods):
        for method in methods:
            for state in self.method_mutates_states[method]:
                self.staleness[state] = True

    # Mark the states returned by the given methods as invalid/stale.
    def mark_returned_stale(self, methods):
        for method in methods:
            for state in self.method_returns_states[method]:
                self.staleness[state] = True

    # Transform the returned data from the server into data objects and
    # then update the current state.
    def update_with_response(self, key, response):
        if key not in self.response_map:
            print(response)
            print("Unimplemented response " + key)
        self.response_map[key](key, response)

    def _verify_challenge(self, key, response):
        if response["challenge_url"] != " ":
            print(response["challenge_url"])
            raise AccountBannedException()

    def _parse_player(self, key, response):
        current_player = self.current_state.get("player", None)
        if current_player is None:
            current_player = Player()
        current_player.update_get_player(response)
        self._update_state({"player": current_player})

    def _parse_inventory(self, key, response):
        new_inventory = InventoryParser(response)

        new_state = {
            "inventory": new_inventory.items,
            "pokedex": new_inventory.pokedex_entries,
            "candy": new_inventory.candy,
            "pokemon": new_inventory.pokemon,
            "eggs": new_inventory.eggs,
            "egg_incubators": new_inventory.egg_incubators
        }

        new_state["inventory_timestamp"] = new_inventory.last_updated

        current_player = self.current_state.get("player", None)
        if current_player is None:
            current_player = Player()
        current_player.update_get_inventory_stats(response)
        new_state["player"] = current_player

        self._update_state(new_state)

    def _parse_map(self, key, response):
        # TODO: Figure out how I want to do WorldMap. Lazy loading might be a better idea
        """
        current_map = self.current_state.get("worldmap", None)
        if current_map is None:
            current_map = WorldMap()
        current_map.update_map_objects(response)
        """
        current_map = WorldMap()
        current_map.update_map_objects(response)

        self._update_state({"worldmap": current_map})

    def _parse_encounter(self, key, response):
        current_encounter = Encounter()
        current_encounter.update_encounter(response)
        self._update_state({"encounter": current_encounter})

    def _parse_disk_encounter(self, key, response):
        current_encounter = Encounter()
        current_encounter.update_disk_encounter(response)
        self._update_state({"disk_encounter": current_encounter})

    def _parse_catch_pokemon(self, key, response):
        current_encounter = self.current_state.get("encounter", None)
        if current_encounter is None:
            current_encounter = Encounter()
        current_encounter.update_catch_pokemon(response)
        self._update_state({"encounter": current_encounter})

    def _parse_fort(self, key, response):
        fort_type = response.get("type", 2)
        if fort_type == 2:
            self._update_state({"fort": Gym(response)})
        else:
            self._update_state({"fort": PokeStop(response)})

    def _parse_get_hatched_eggs(self, key, response):
        if response.get("success", False):
            current_player = self.current_state.get("player", None)
            if current_player is None:
                current_player = Player()

            current_player.update_hatched_eggs(response)
            self._update_state({"player": current_player})

            if len(response.get("pokemon_id", [])) > 0:
                self.mark_returned_stale("GET_INVENTORY")

    def _parse_use_incubator(self, key, response):
        if response.get("result", 0) == 1:

            current_egg_incubators = self.current_state.get("egg_incubators", [])
            new_egg_incubators = []

            for curr_incu in current_egg_incubators:
                if curr_incu.unique_id == response["egg_incubator"].get("id"):
                    new_egg_incubators.append(Incubator(response["egg_incubator"]))
                else:
                    new_egg_incubators.append(curr_incu)

            self._update_state({"egg_incubators": new_egg_incubators})

    def _parse_evolution(self, key, response):
        self._update_state({"evolution": EvolutionResult(response)})

    def _identity(self, key, response):
        self._update_state({key: response})

    def _dl_settings(self, key, response):
        self._update_state({"download_settings": response})
