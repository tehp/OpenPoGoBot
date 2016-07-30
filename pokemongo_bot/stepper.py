# -*- coding: utf-8 -*-

from datetime import datetime
from math import ceil
import json
import googlemaps

from s2sphere import CellId, LatLng  # type: ignore
from pokemongo_bot.human_behaviour import sleep, random_lat_long_delta
from pokemongo_bot.utils import distance, format_time, f2i
import pokemongo_bot.logger as logger

# Uncomment to enable type annotations for Python 3
# from typing import Optional, List


class Stepper(object):
    AVERAGE_STRIDE_LENGTH_IN_METRES = 0.60

    def __init__(self, bot):
        self.bot = bot
        self.api_wrapper = bot.api_wrapper
        self.config = bot.config

        self.pos = 1
        self.first_step = True
        self.step_limit = self.config.max_steps
        self.step_limit_squared = self.step_limit ** 2
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]

    def take_step(self):
        if self.first_step:
            self.first_step = False
            position = (self.origin_lat, self.origin_lon, 0.0)
        else:
            position_lat, position_lng, _ = self.api_wrapper.get_position()
            position = (position_lat, position_lng, 0.0)

        self.api_wrapper.set_position(*position)
        self._work_at_position(position[0], position[1], True)
        sleep(5)

    def walk_to(self, speed, lat, lng, alt):
        position_lat, position_lng, _ = self.api_wrapper.get_position()

        # ask google for directions
        if self.config.google_directions and self.config.gmapkey:

            logger.log("[#] Asking google for directions")
            gmaps = googlemaps.Client(key=self.config.gmapkey)

            now = datetime.now()
            start = "{},{}".format(position_lat, position_lng)
            end = "{},{}".format(lat, lng)
            directions_result = gmaps.directions(start, end, mode="walking", departure_time=now)

            if len(directions_result) and len(directions_result[0]["legs"]):
                for leg in directions_result[0]["legs"]:
                    for step in leg["steps"]:
                        self._do_walk_to(speed, step["start_location"]["lat"], step["start_location"]["lng"],
                                         step["end_location"]["lat"], step["end_location"]["lng"], alt, 10)
            else:
                # If google doesn't know the way, then we just have to go as the crow flies
                self._do_walk_to(speed, position_lat, position_lng, lat, lng, alt, 25)

        else:
            self._do_walk_to(speed, position_lat, position_lng, lat, lng, alt, 25)

        logger.log("[#] Walking Finished")

    def _do_walk_to(self, speed, from_lat, from_lng, to_lat, to_lng, alt, delta_factor):
        # type: (float, float, float, float, float, float, float) -> None

        dist = distance(from_lat, from_lng, to_lat, to_lng)
        steps = (dist / (self.AVERAGE_STRIDE_LENGTH_IN_METRES * speed))

        logger.log("[#] Walking from " + str((from_lat, from_lng)) + " to " + str(
            str((to_lat, to_lng))) + " for approx. " + str(format_time(ceil(steps))))
        if steps != 0:
            d_lat = (to_lat - from_lat) / steps
            d_long = (to_lng - from_lng) / steps

            for _ in range(int(steps)):
                position_lat, position_lng, _ = self.api_wrapper.get_position()
                c_lat = position_lat + d_lat + random_lat_long_delta(delta_factor)
                c_long = position_lng + d_long + random_lat_long_delta(delta_factor)
                self.api_wrapper.set_position(c_lat, c_long, alt)

                self.bot.heartbeat()
                sleep(1)  # sleep one second plus a random delta

                position_lat, position_lng, _ = self.api_wrapper.get_position()
                self._work_at_position(position_lat, position_lng, False)

            self.bot.heartbeat()

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

    def _work_at_position(self, lat, lng, pokemon_only=False):
        # type: (float, float, Optional[bool]) -> None
        cell_id = self._get_cell_id_from_latlong()
        timestamp = [0, ] * len(cell_id)
        self.api_wrapper.get_map_objects(latitude=f2i(lat),
                                         longitude=f2i(lng),
                                         since_timestamp_ms=timestamp,
                                         cell_id=cell_id)

        response_dict = self.api_wrapper.call()
        if response_dict is None:
            return
        # Passing data through last-location and location
        map_objects = response_dict["worldmap"]
        with open("data/last-location-{}.json".format(self.config.username), "w") as outfile:
            outfile.truncate()
            json.dump({"lat": lat, "lng": lng}, outfile)

        map_cells = map_objects.cells
        # Sort all by distance from current pos - eventually this should build graph and A* it
        map_cells.sort(key=lambda x: distance(lat, lng, x.pokestops[0].latitude, x.pokestops[0].longitude) if len(
            x.pokestops) > 0 else 1e6)
        for cell in map_cells:
            self.bot.work_on_cell(cell, pokemon_only)
