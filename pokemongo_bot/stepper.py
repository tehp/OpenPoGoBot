# -*- coding: utf-8 -*-

from math import ceil

from app import kernel
from pokemongo_bot.human_behaviour import sleep, random_lat_long_delta
from pokemongo_bot.utils import distance, format_time, format_dist


@kernel.container.register('stepper', ['@config.core', '@stealth_api', '%path_finder%', '@logger'])
class Stepper(object):
    AVERAGE_STRIDE_LENGTH_IN_METRES = 0.60

    def __init__(self, config, api_wrapper, path_finder, logger):
        # type: (Namespace, PoGpApi, PathFinder, Logger) -> None
        self.config = config
        self.api_wrapper = api_wrapper
        self.path_finder = path_finder
        self.logger = logger

        self.origin_lat = None
        self.origin_lng = None
        self.origin_alt = None

        self.current_lat = None
        self.current_lng = None
        self.current_alt = None

        self.speed = 4.16 if (self.config['movement']['walk_speed'] is None or self.config['movement']['walk_speed'] <= 0) else self.config['movement']['walk_speed']

    def start(self, origin_lat, origin_lng, origin_alt):
        # type: (float, float, float) -> None
        self.origin_lat = origin_lat
        self.origin_lng = origin_lng
        self.origin_alt = origin_alt
        self.current_lat = origin_lat
        self.current_lng = origin_lng
        self.current_alt = origin_alt

        position = (origin_lat, origin_lng, origin_alt)

        self.api_wrapper.set_position(*position)

    def step(self, destination):
        # type: (Destination) -> List[(float, float, float)]
        dist = distance(self.current_lat, self.current_lng, destination.target_lat, destination.target_lng)

        if destination.name:
            self.logger.log("Walking towards {} ({} away, eta {})".format(destination.name,
                                                                          format_dist(dist, self.config["mapping"]["distance_unit"]),
                                                                          format_time(destination.get_step_count())),
                            prefix="Navigation")

        for step in destination.step():
            if distance(self.current_lat, self.current_lng, destination.target_lat, destination.target_lng) < 30:
                break
            self._step_to(*step)
            yield step

        if destination.name:
            self.logger.log("Arrived at {} ({} away)".format(destination.name, format_dist(dist, self.config["mapping"]["distance_unit"])), prefix="Navigation")

    def get_route_between(self, from_lat, from_lng, to_lat, to_lng, alt):
        # type: (float, float, float) -> List[(float, float, float)]
        route_steps = list()

        # ask the path finder how to get there
        path_points = self.path_finder.path(from_lat, from_lng, to_lat, to_lng)
        for path_point in path_points:
            path_to_lat, path_to_lng = path_point
            path_steps = self._get_steps_between(from_lat, from_lng, path_to_lat, path_to_lng, alt)
            route_steps += path_steps

            # shift the path along
            from_lat = path_to_lat
            from_lng = path_to_lng

        return route_steps

    def _get_steps_between(self, from_lat, from_lng, to_lat, to_lng, alt):
        # type: (float, float, float) -> List[(float,float,float)]
        dist = distance(from_lat, from_lng, to_lat, to_lng)
        steps = (dist / (self.AVERAGE_STRIDE_LENGTH_IN_METRES * self.speed))

        step_locations = list()

        if steps != 0:
            d_lat = (to_lat - from_lat) / steps
            d_long = (to_lng - from_lng) / steps

            total_steps = int(ceil(steps))
            for _ in range(total_steps):
                from_lat += d_lat
                from_lng += d_long
                c_lat = from_lat + random_lat_long_delta(10)
                c_long = from_lng + random_lat_long_delta(10)
                step_locations.append((c_lat, c_long, alt))

        return step_locations

    def snap_to(self, to_lat, to_lng, to_alt):
        # type: (float, float, float) -> None
        """
            This method is to correct a position you are near to. If you try and snap a distance over 10 meters,
            it will fail.
        """
        # type: (float, float, float) -> None
        dist = distance(self.current_lat, self.current_lng, to_lat, to_lng)

        # Never snap big distances
        if dist > 15:
            return

        self._step_to(to_lat, to_lng, to_alt)

    def _step_to(self, lat, lng, alt):
        # type: (float, float, float) -> None
        self.api_wrapper.set_position(lat, lng, alt)

        self.current_lat = lat
        self.current_lng = lng
        self.current_alt = alt

        sleep(1)  # sleep one second plus a random delta
