# pylint: disable=redefined-builtin
from builtins import str
import time


class Fort(object):
    def __init__(self, data):
        self.fort_id = data.get("id", "")
        self.fort_name = str(data.get("name", "Unknown"))
        self.latitude = data.get("latitude", None)
        self.longitude = data.get("longitude", None)
        self.enabled = data.get("enabled", 1)
        self.last_modified_timestamp_ms = data.get("last_modified_timestamp_ms", 0)
        self.cooldown_timestamp_ms = data.get("cooldown_complete_timestamp_ms", 0)
        self.fort_type = data.get("type", 0)

    def is_in_cooldown(self):
        return self.cooldown_timestamp_ms + 1000 > time.time() * 1000


class PokeStop(Fort):
    def __init__(self, data):
        super(PokeStop, self).__init__(data)
        self.active_fort_modifier = data.get("active_fort_modifier", "")

        lure_info = data.get("lure_info", {})
        self.lure_expires_timestamp_ms = lure_info.get("lure_expires_timestamp_ms", 0)
        self.lure_encounter_id = lure_info.get("encounter_id", 0)
        self.lure_encounter_id = lure_info.get("active_pokemon_id", 0)
        self.fort_type = 1


class Gym(Fort):
    def __init__(self, data):
        super(Gym, self).__init__(data)

        self.is_in_battle = data.get("is_in_battle", 0)
        self.is_in_battle = True if self.is_in_battle == 1 else False

        self.guard_pokemon_id = data.get("guard_pokemon_id", 0)
        self.owned_by_team = data.get("owned_by_team", 0)
        self.gym_points = data.get("gym_points", 0)


class Cell(object):
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
            if fort.get("type", 2) == 1:
                self.pokestops.append(PokeStop(fort))
            else:
                self.gyms.append(Gym(fort))


class WorldMap(object):
    def __init__(self):
        self.cells = []

    def update_map_objects(self, data):
        cells = data.get("map_cells", [])
        for cell_data in cells:
            cell = Cell(cell_data)
            self.cells.append(cell)
