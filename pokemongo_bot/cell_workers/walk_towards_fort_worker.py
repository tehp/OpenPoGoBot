# -*- coding: utf-8 -*-

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.cell_workers.utils import distance, format_dist

class WalkTowardsFortWorker(object):

    def __init__(self, fort, bot):
        self.fort = fort
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list
        self.rest_time = 50
        self.stepper = bot.stepper

    def work(self):
        lat = self.fort["latitude"]
        lng = self.fort["longitude"]
        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        fort_id = self.fort["id"]
        dist = distance(self.position[0], self.position[1], lat, lng)

        logger.log("[#] Found fort {} at distance {}".format(fort_id, format_dist(dist, unit)))

        if dist > 0:
            logger.log("[#] Need to move closer to Pokestop")
            position = (lat, lng, 0.0)

            if self.config.walk > 0:
                self.stepper.walk_to(self.config.walk, *position)
            else:
                self.api.set_position(*position)
            self.api.player_update(latitude=lat, longitude=lng)
            logger.log("[#] Arrived at Pokestop")
            sleep(2)

        self.api.fort_details(fort_id=self.fort["id"],
                              latitude=lat,
                              longitude=lng)
        response_dict = self.api.call()
        if response_dict is None:
            return
        fort_details = response_dict.get("responses", {}).get("FORT_DETAILS", {})
        fort_name = fort_details.get("name") if fort_details.get("name") else "Unknown"
        logger.log("[#] Now at Pokestop: " + fort_name)
