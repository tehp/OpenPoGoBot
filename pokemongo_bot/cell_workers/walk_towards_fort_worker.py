# -*- coding: utf-8 -*-

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.utils import distance, format_dist


# TODO: turn this into a plugin
class WalkTowardsFortWorker(object):
    def __init__(self, fort, bot):
        self.fort = fort
        self.api_wrapper = bot.api_wrapper
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list
        self.rest_time = 50
        self.stepper = bot.stepper

    def work(self):

        if self.config.fill_incubators:
            self.api_wrapper.get_inventory()
            response_dict = self.api_wrapper.call()

            eggs = [egg.unique_id for egg in response_dict["eggs"] if egg.egg_incubator_id == ""]
            incubators = [incu.unique_id for incu in response_dict["egg_incubators"] if incu.pokemon_id == 0 and (
                self.config.use_all_incubators or incu.item_id == 901)]

            for incubator_unique_id in incubators:
                if len(eggs) > 0:
                    self.api_wrapper.use_item_egg_incubator(item_id=incubator_unique_id, pokemon_id=eggs.pop())
                    self.api_wrapper.call()
                    logger.log("[+] Put an egg into an incubator", "green")
                else:
                    logger.log("[+] No more free incubators", "yellow")


        lat = self.fort.latitude
        lng = self.fort.longitude
        unit = self.config.distance_unit  # Unit to use when printing formatted distance

        fort_id = self.fort.fort_id
        dist = distance(self.position[0], self.position[1], lat, lng)

        self.api_wrapper.fort_details(fort_id=fort_id,
                                      latitude=lat,
                                      longitude=lng)
        response_dict = self.api_wrapper.call()
        if response_dict is None:
            return
        fort_details = response_dict["fort"]
        fort_name = fort_details.fort_name

        logger.log(u"[#] Found fort {} at distance {}".format(fort_name, format_dist(dist, unit)))

        if dist > 0:
            logger.log(u"[#] Moving closer to {}".format(fort_name))
            position = (lat, lng, 0.0)

            if self.config.walk > 0:
                self.stepper.walk_to(self.config.walk, *position)
            else:
                self.api_wrapper.set_position(*position)
            self.api_wrapper.player_update(latitude=lat, longitude=lng)
            sleep(2)

        logger.log(u"[#] Now at Pokestop: {}".format(fort_name))
