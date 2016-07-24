# -*- coding: utf-8 -*-

import json

from math import ceil
from s2sphere import CellId, LatLng

from human_behaviour import sleep, random_lat_long_delta
from cell_workers.utils import distance, i2f, format_time

from pgoapi.utilities import f2i, h2f
import logger


def get_cell_id_from_latlong(lat, long, radius=10):
    origin = CellId.from_lat_lng(LatLng.from_degrees(lat, long)).parent(15)
    walk = [origin.id()]

    # 10 before and 10 after
    next = origin.next()
    prev = origin.prev()
    for i in range(radius):
        walk.append(prev.id())
        walk.append(next.id())
        next = next.next()
        prev = prev.prev()
    return sorted(walk)


class Stepper(object):

    def __init__(self, bot):
        self.bot = bot
        self.api = bot.api
        self.config = bot.config

        self.pos = 1
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = -1
        self.step_limit = self.config.max_steps
        self.step_limit_squared = self.step_limit ** 2
        self.origin_lat = self.bot.position[0]
        self.origin_lon = self.bot.position[1]

    def take_step(self):
        position = (self.origin_lat, self.origin_lon, 0.0)

        self.api.set_position(*position)

        for step in range(self.step_limit_squared):
            # starting at 0 index
            logger.log("[#] Scanning area for objects ({} / {})".format((step + 1), self.step_limit ** 2))
            if self.config.debug:
                logger.log("steplimit: {} x: {} y: {} pos: {} dx: {} dy {}".format(self.step_limit_squared, self.x, self.y, self.pos, self.dx, self.dy))
            # Scan location math
            if -self.step_limit_squared / 2 < self.x <= self.step_limit_squared / 2 and -self.step_limit_squared / 2 < self.y <= self.step_limit_squared / 2:
                position = (self.x * 0.0025 + self.origin_lat,
                            self.y * 0.0025 + self.origin_lon, 0)
                if self.config.walk > 0:
                    self.walk_to(self.config.walk, *position)
                else:
                    self.api.set_position(*position)
                print("[#] {}".format(position))
            if self.x == self.y or self.x < 0 and self.x == -self.y or self.x > 0 and self.x == 1 - self.y:
                self.dx, self.dy = -self.dy, self.dx

            self.x, self.y = self.x + self.dx, self.y + self.dy

            self._work_at_position(position[0], position[1], position[2], True)
            sleep(10)

    def walk_to(self, speed, lat, long, alt):
        dist = distance(i2f(self.api._position_lat), i2f(self.api._position_lng), lat, long)
        steps = (dist + 0.0) / (speed + 0.0)  # may be rational number
        intSteps = int(steps)
        residuum = steps - intSteps
        logger.log("[#] Walking from " + str((i2f(self.api._position_lat), i2f(self.api._position_lng))) + " to " + str(str((lat, long))) + " for approx. " + str(format_time(ceil(steps))))
        if steps != 0:
            d_lat = (lat - i2f(self.api._position_lat)) / steps
            d_long = (long - i2f(self.api._position_lng)) / steps

            for i in range(intSteps):
                c_lat = i2f(self.api._position_lat) + d_lat + random_lat_long_delta()
                c_long = i2f(self.api._position_lng) + d_long + random_lat_long_delta()
                self.api.set_position(c_lat, c_long, alt)
                self.bot.heartbeat()
                sleep(1)  # sleep one second plus a random delta
                self._work_at_position(i2f(self.api._position_lat), i2f(self.api._position_lng), alt, False)

            self.api.set_position(lat, long, alt)
            self.bot.heartbeat()
            logger.log("[#] Finished walking")

    def _work_at_position(self, lat, long, alt, pokemon_only=False):
        cell_id = get_cell_id_from_latlong(lat, long)
        timestamp = [0, ] * len(cell_id)
        self.api.get_map_objects(latitude=f2i(lat),
                                 longitude=f2i(long),
                                 since_timestamp_ms=timestamp,
                                 cell_id=cell_id)

        response_dict = self.api.call()
        # Passing data through last-location and location
        map_objects = response_dict.get("responses", {}).get("GET_MAP_OBJECTS")
        if map_objects is not None:
            with open("web/location-{}.json".format(self.config.username), "w") as outfile:
                json.dump({"lat": lat, "lng": long, "cells": map_objects.get("map_cells")}, outfile)
            with open("data/last-location-{}.json".format(self.config.username), "w") as outfile:
                outfile.truncate()
                json.dump({"lat": lat, "lng": long}, outfile)
            if "status" in map_objects:
                if map_objects.get("status") is 1:
                    map_cells = map_objects.get("map_cells")
                    position = lat, long, alt
                # Sort all by distance from current pos - eventually this should build graph and A* it
                map_cells.sort(key=lambda x: distance(lat, long, x["forts"][0]["latitude"], x["forts"][0]["longitude"]) if "forts" in x and x["forts"] != [] else 1e6)
                for cell in map_cells:
                    self.bot.work_on_cell(cell, position, pokemon_only)
