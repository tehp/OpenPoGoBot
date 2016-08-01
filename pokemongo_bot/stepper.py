# -*- coding: utf-8 -*-

from math import ceil

from pokemongo_bot.event_manager import manager
from pokemongo_bot.human_behaviour import sleep, random_lat_long_delta
from pokemongo_bot.utils import distance, format_time
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

    def walk_to(self, lat, lng, alt):
        # type: (float, float, float) -> None
        position_lat, position_lng, position_alt = self.api_wrapper.get_position()
        self.current_lat = position_lat
        self.current_lng = position_lng
        self.current_alt = position_alt

        # ask the path finder how to get there
        steps = self.path_finder.path(position_lat, position_lng, lat, lng)
        for step in steps:
            to_lat, to_lng = step
            self._walk_to(to_lat, to_lng, alt)

        logger.log("[#] Walking Finished")

    def _walk_to(self, to_lat, to_lng, to_alt):
        # type: (float, float, float) -> None
        dist = distance(self.current_lat, self.current_lng, to_lat, to_lng)
        steps = (dist / (self.AVERAGE_STRIDE_LENGTH_IN_METRES * self.speed))

        if self.config.debug:
            logger.log("[#] Walking from " + str((self.current_lat, self.current_lng)) + " to " + str(
                str((to_lat, to_lng))) + " for approx. " + str(format_time(ceil(steps))))

        if steps != 0:
            d_lat = (to_lat - self.current_lat) / steps
            d_long = (to_lng - self.current_lng) / steps

            for _ in range(int(ceil(steps))):
                c_lat = self.current_lat + d_lat + random_lat_long_delta(10)
                c_long = self.current_lng + d_long + random_lat_long_delta(10)
                self._jump_to(c_lat, c_long, to_alt)

            self.bot.heartbeat()

    def snap_to(self, to_lat, to_lng, to_alt):
        # type: (float, float, float) -> None
        """
            This method is to correct a position you are near to. If you try and snap a distance over 10 meters,
            it will fail.
        """
        # type: (float, float, float) -> None
        dist = distance(self.current_lat, self.current_lng, to_lat, to_lng)

        # Never snap big distances
        if dist > 10:
            return

        self._jump_to(to_lat, to_lng, to_alt)

    def _jump_to(self, lat, lng, alt):
        # type: (float, float, float) -> None
        self.api_wrapper.set_position(lat, lng, alt)

        new_lat, new_lng, new_alt = self.api_wrapper.get_position()
        self.current_lat = new_lat
        self.current_lng = new_lng
        self.current_alt = new_alt

        self.bot.fire("position_updated", coords=(new_lat, new_lng, new_alt))

        self.bot.heartbeat()
        sleep(1)  # sleep one second plus a random delta

        map_cells = self.bot.mapper.get_cells(self.current_lat, self.current_lng)
        self.bot.work_on_cells(map_cells)
