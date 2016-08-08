# -*- coding: utf-8 -*-

from math import ceil

from pokemongo_bot.event_manager import manager
from pokemongo_bot.human_behaviour import sleep, random_lat_long_delta
from pokemongo_bot.utils import distance, format_time, format_dist
from pokemongo_bot.navigation.path_finder import GooglePathFinder, DirectPathFinder
import pokemongo_bot.logger as logger

# Uncomment to enable type annotations for Python 3
# from typing import Optional, List


class Stepper(object):
    AVERAGE_STRIDE_LENGTH_IN_METRES = 0.60

    def __init__(self, bot):
        # type: (PokemonGoBot) -> None
        self.bot = bot
        self.api_wrapper = bot.api_wrapper
        self.config = bot.config

        self.speed = self.config.walk if self.config.walk > 0 else 4.16
        self.path_finder = None
        self.pos = 1
        self.step_limit = self.config.max_steps
        self.step_limit_squared = self.step_limit ** 2

        self.origin_lat = self.bot.position[0]
        self.origin_lng = self.bot.position[1]
        self.origin_alt = self.bot.position[2]

        self.current_lat = self.origin_lat
        self.current_lng = self.origin_lng
        self.current_alt = self.origin_alt

        if self.config.path_finder == 'google':
            self.path_finder = GooglePathFinder(self)  # pylint: disable=redefined-variable-type
        elif self.config.path_finder == 'direct':
            self.path_finder = DirectPathFinder(self)  # pylint: disable=redefined-variable-type

    def start(self):
        # type: () -> None
        position = (self.origin_lat, self.origin_lng, self.origin_alt)

        self.api_wrapper.set_position(*position)

    def step(self, destination):
        # type: (Destination) -> None
        self.bot.fire("walking_started", coords=(destination.target_lat, destination.target_lng, destination.target_alt))

        dist = distance(self.current_lat, self.current_lng, destination.target_lat, destination.target_lng)

        if destination.name:
            logger.log("Walking towards {} ({} away, eta {})".format(destination.name,
                                                                     format_dist(dist, self.config.distance_unit),
                                                                     format_time(destination.get_step_count())),
                       prefix="Navigation")

        for step in destination.step():
            self._step_to(*step)
            yield step

        if destination.name:
            logger.log("Arrived at {} ({} away)".format(destination.name, format_dist(dist, self.config.distance_unit)), prefix="Navigation")

        self.bot.fire("walking_finished", coords=(destination.target_lat, destination.target_lng, destination.target_alt))

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

        new_lat, new_lng, new_alt = self.api_wrapper.get_position()
        self.current_lat = new_lat
        self.current_lng = new_lng
        self.current_alt = new_alt

        self.bot.fire("position_updated", coordinates=(new_lat, new_lng, new_alt))

        self.bot.heartbeat()
        sleep(1)  # sleep one second plus a random delta
