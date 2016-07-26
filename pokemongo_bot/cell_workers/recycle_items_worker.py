# -*- coding: utf-8 -*-

from pokemongo_bot import logger


class RecycleItemsWorker(object):

    def __init__(self, bot):
        self.api = bot.api
        self.bot = bot
        self.position = bot.position
        self.config = bot.config
        self.item_list = bot.item_list

    def work(self):
        self.bot.update_inventory()
        for item in self.bot.inventory:
            if str(item["item_id"]) in self.config.item_filter:
                amount_to_keep = self.config.item_filter.get(str(item["item_id"])).get("keep")
                if amount_to_keep is None:
                    continue
                amount_to_drop = item["count"] - amount_to_keep
                if amount_to_drop <= 0:
                    continue
                logger.log("[+] Recycling: {} x {}...".format(self.item_list[str(item["item_id"])], amount_to_drop), 'green')
                self.bot.drop_item(item["item_id"], amount_to_drop)
