# -*- coding: utf-8 -*-

from math import ceil
import json

from s2sphere import CellId, LatLng  # type: ignore
from pokemongo_bot.human_behaviour import sleep, random_lat_long_delta
from pokemongo_bot.utils import distance, format_time, f2i, convert_to_utf8
from pokemongo_bot.navigation import FortNavigator
import pokemongo_bot.logger as logger


# Uncomment to enable type annotations for Python 3
# from typing import Optional, List


class Mapper(object):
    def __init__(self, bot):
        # type: (PokemonGoBot) -> None
        self.bot = bot
        self.stepper = bot.stepper
        self.api_wrapper = bot.api_wrapper
        self.config = bot.config

    def get_cells(self, lat, lng):
        # type: (float, float) -> List[Cell]
        cell_id = self._get_cell_id_from_latlong()
        timestamp = [0, ] * len(cell_id)
        self.api_wrapper.get_map_objects(latitude=f2i(lat),
                                         longitude=f2i(lng),
                                         since_timestamp_ms=timestamp,
                                         cell_id=cell_id)

        response_dict = self.api_wrapper.call()
        if response_dict is None:
            return []

        # Passing data through last-location and location
        map_objects = response_dict["worldmap"]

        with open("data/last-location-{}.json".format(self.config.username), "w") as outfile:
            outfile.truncate()
            json.dump({"lat": lat, "lng": lng}, outfile)

        map_cells = map_objects.cells
        # Sort all by distance from current pos - eventually this should build graph and A* it
        map_cells.sort(key=lambda x: distance(lat, lng, x.pokestops[0].latitude, x.pokestops[0].longitude) if len(
            x.pokestops) > 0 else 1e6)

        return map_cells

    def get_cells_at_current_position(self):
        # type: () -> List[Cell]
        return self.get_cells(
            self.stepper.current_lat,
            self.stepper.current_lng
        )

    def _get_cell_id_from_latlong(self, radius=10):
        # type: (Optional[int]) -> List[str]
        position_lat, position_lng, _ = self.api_wrapper.get_position()
        origin = CellId.from_lat_lng(LatLng.from_degrees(position_lat, position_lng)).parent(15)
        walk = [origin.id()]

        # 10 before and 10 after
        next_cell = origin.next()
        prev_cell = origin.prev()
        for _ in range(radius):
            walk.append(prev_cell.id())
            walk.append(next_cell.id())
            next_cell = next_cell.next()
            prev_cell = prev_cell.prev()
        return sorted(walk)
