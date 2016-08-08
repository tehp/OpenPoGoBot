# pylint: disable=redefined-builtin
from builtins import str
import time

from api.json_encodable import JSONEncodable


class Fort(JSONEncodable):
    def __init__(self, data):
        self.fort_id = data.get("id", "")
        self.fort_name = data.get("name", "Unknown").encode('ascii', 'replace')
                            # TODO: Make this proper unicode  ^^
        self.latitude = data.get("latitude", None)
        self.longitude = data.get("longitude", None)
        self.enabled = data.get("enabled", True)
        self.last_modified_timestamp_ms = data.get("last_modified_timestamp_ms", 0)
        self.fort_type = data.get("type", 0)


class PokeStop(Fort):
    def __init__(self, data):
        super(PokeStop, self).__init__(data)
        self.active_fort_modifier = data.get("active_fort_modifier", None)
        self.cooldown_timestamp_ms = data.get("cooldown_complete_timestamp_ms", None)

        lure_info = data.get("lure_info", {})
        self.lure_expires_timestamp_ms = lure_info.get("lure_expires_timestamp_ms", None)
        self.lure_encounter_id = lure_info.get("encounter_id", None)
        self.lure_pokemon_id = lure_info.get("active_pokemon_id", None)
        self.fort_type = 1

    def is_lure_active(self):
        if self.lure_expires_timestamp_ms is None:
            return False
        return self.lure_expires_timestamp_ms + 1000 > time.time() * 1000

    def is_in_cooldown(self):
        if self.cooldown_timestamp_ms is None:
            return False
        return self.cooldown_timestamp_ms + 1000 > time.time() * 1000


class Gym(Fort):
    def __init__(self, data):
        super(Gym, self).__init__(data)

        self.is_in_battle = True if data.get("is_in_battle", 0) == 1 else False

        self.guard_pokemon_id = data.get("guard_pokemon_id", None)
        self.owned_by_team = data.get("owned_by_team", 0)
        self.gym_points = data.get("gym_points", 0)


class Cell(JSONEncodable):
    def __init__(self, data):
        self.spawn_points = []
        self.gyms = []
        self.pokestops = []

        self.cell_id = data.get("s2_cell_id", 0)

        spawn_points = data.get("spawn_points", [])
        for spawn in spawn_points:
            self.spawn_points.append((spawn["latitude"], spawn["longitude"]))

        self.catchable_pokemon = data.get("catchable_pokemons", [])
        self.nearby_pokemon = data.get("nearby_pokemons", [])
        self.wild_pokemon = data.get("wild_pokemons", [])

        forts = data.get("forts", [])
        for fort in forts:
            if fort.get("type", 0) == 1:
                self.pokestops.append(PokeStop(fort))
            elif fort.get("type", 0) == 2:
                self.gyms.append(Gym(fort))
            else:
                # Some unknown kind of fort or invalid data
                pass


class WorldMap(JSONEncodable):
    def __init__(self):
        self.cells = []

    def update_map_objects(self, data):
        cells = data.get("map_cells", [])
        for cell_data in cells:
            cell = Cell(cell_data)
            self.cells.append(cell)
