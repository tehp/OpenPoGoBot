# -*- coding: utf-8 -*-

import json

from googlemaps.exceptions import ApiError
from s2sphere import CellId, LatLng  # type: ignore

from app import kernel
from pokemongo_bot.utils import distance


@kernel.container.register('mapper', ['@config', '@api_wrapper', '@google_maps', '@logger'])
class Mapper(object):
    def __init__(self, config, api_wrapper, google_maps, logger):
        # type: (Namespace, PoGoApi, Client) -> None
        self.config = config
        self.api_wrapper = api_wrapper
        self.google_maps = google_maps
        self.logger = logger

    def get_cells(self, lat, lng):
        # type: (float, float) -> List[Cell]
        cell_id = self._get_cell_id_from_latlong()
        timestamp = [0, ] * len(cell_id)
        self.api_wrapper.get_map_objects(latitude=lat,
                                         longitude=lng,
                                         since_timestamp_ms=timestamp,
                                         cell_id=cell_id)

        response_dict = self.api_wrapper.call()
        if response_dict is None:
            return []

        # Passing data through last-location and location
        map_objects = response_dict["worldmap"]

        with open("data/last-location-{}.json".format(self.config["login"]["username"]), "w") as outfile:
            outfile.truncate()
            json.dump({"lat": lat, "lng": lng}, outfile)

        map_cells = map_objects.cells
        # Sort all by distance from current pos - eventually this should build graph and A* it
        map_cells.sort(key=lambda x: distance(lat, lng, x.pokestops[0].latitude, x.pokestops[0].longitude) if len(
            x.pokestops) > 0 else 1e6)

        return map_cells

    def find_location(self, location):
        # type: (str) -> Tuple[float, float, float]

        # If we have been given a string of coordinates
        if location.count(',') == 1:
            try:
                parts = location.split(',')

                pos_lat = float(parts[0])
                pos_lng = float(parts[1])

                # we need to ask google for the altitude
                response = self.google_maps.elevation((pos_lat, pos_lng))

                if response is not None and len(response) and "elevation" in response[0]:
                    return pos_lat, pos_lng, response[0]["elevation"]
                else:
                    raise ValueError
            except ApiError:
                self.logger.log("Could not fetch altitude from google. Trying geolocator.", prefix='Logger', color='yellow')
            except ValueError:
                self.logger.log("Location was not Lat/Lng. Trying geolocator.", prefix='Logger', color='yellow')

        # Fallback to geolocation if no Lat/Lng can be found
        loc = self.google_maps.geocode(location)

        return loc.latitude, loc.longitude, loc.altitude

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
