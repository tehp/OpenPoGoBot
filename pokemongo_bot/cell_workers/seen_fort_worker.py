# -*- coding: utf-8 -*-

import time

from pokemongo_bot import logger
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.utils import format_time, f2i
from pokemongo_bot.cell_workers.recycle_items_worker import RecycleItemsWorker


class SeenFortWorker(object):
    def __init__(self, fort, bot):
        self.fort = fort
        self.api_wrapper = bot.api_wrapper
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list

    def work(self):
        lat = self.fort.latitude
        lng = self.fort.longitude
        logger.log("Spinning...", "yellow")
        sleep(3)
        self.api_wrapper.fort_search(fort_id=self.fort.fort_id,
                                     fort_latitude=lat, fort_longitude=lng,
                                     player_latitude=self.position[0], player_longitude=self.position[1])
        response_dict = self.api_wrapper.call()
        if response_dict is None:
            return
        # TODO: Fix the rest of this

        spin_details = response_dict["FORT_SEARCH"]
        spin_result = spin_details.get("result")
        if spin_result == 1:
            logger.log("[+] Loot: ", "green")
            experience_awarded = spin_details.get("experience_awarded", False)
            if experience_awarded:
                logger.log("[+] " + str(experience_awarded) + " xp", "green")

            items_awarded = spin_details.get("items_awarded", False)
            if items_awarded:
                tmp_count_items = {}
                for item in items_awarded:
                    item_id = item["item_id"]
                    if item_id not in tmp_count_items:
                        tmp_count_items[item_id] = item["item_count"]
                    else:
                        tmp_count_items[item_id] += item["item_count"]

                for item_id, item_count in tmp_count_items.items():
                    item_id = str(item_id)
                    item_name = self.item_list[item_id]

                    logger.log("[+] " + str(item_count) + "x " + item_name, "green")
                if self.config.recycle_items:
                    recycle_worker = RecycleItemsWorker(self.bot)
                    recycle_worker.work()

            else:
                logger.log("[#] Nothing found.", "yellow")

            pokestop_cooldown = spin_details.get("cooldown_complete_timestamp_ms")
            if pokestop_cooldown:
                seconds_since_epoch = time.time()
                cooldown_time = str(format_time((pokestop_cooldown / 1000) - seconds_since_epoch))
                logger.log("[#] PokeStop on cooldown. Time left: " + cooldown_time)

            if not items_awarded and not experience_awarded and not pokestop_cooldown:
                message = (
                    "Stopped at Pokestop and did not find experience, items "
                    "or information about the stop cooldown. You are "
                    "probably softbanned. Try to play on your phone, "
                    "if pokemons always ran away and you find nothing in "
                    "PokeStops you are indeed softbanned. Please try again "
                    "in a few hours.")
                raise RuntimeError(message)
        elif spin_result == 2:
            logger.log("[#] Pokestop out of range")
        elif spin_result == 3:
            pokestop_cooldown = spin_details.get("cooldown_complete_timestamp_ms")
            if pokestop_cooldown:
                seconds_since_epoch = time.time()
                cooldown_time = str(format_time((pokestop_cooldown / 1000) - seconds_since_epoch))
                logger.log("[#] PokeStop on cooldown. Time left: " + cooldown_time)
        elif spin_result == 4:
            logger.log("[#] Inventory is full, switching to catch mode...", "red")
            self.config.mode = "poke"

        sleep(2)
