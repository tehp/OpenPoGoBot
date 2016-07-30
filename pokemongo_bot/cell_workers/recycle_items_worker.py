# -*- coding: utf-8 -*-

from pokemongo_bot import logger


class RecycleItemsWorker(object):
    def __init__(self, bot):
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list

    def work(self):
        response = self.bot.update_player_and_inventory()
        inventory = response["inventory"]
        for item in inventory:
            if item in self.config.item_filter:
                amount_to_keep = self.config.item_filter.get(item).get("keep")
                if amount_to_keep is None:
                    continue
                amount_to_drop = inventory[item] - amount_to_keep
                if amount_to_drop <= 0:
                    continue
                logger.log("[+] Recycling: {} x {}...".format(self.item_list[item], amount_to_drop), 'green')
                self.bot.drop_item(item, amount_to_drop)
