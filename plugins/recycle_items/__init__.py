# -*- coding: utf-8 -*-
from app import Plugin
from app import kernel
from pokemongo_bot.human_behaviour import sleep


@kernel.container.register('recycle_items', ['@config.recycle_items', '@event_manager', '@logger'], tags=['plugin'])
class RecycleItems(Plugin):
    def __init__(self, config, event_manager, logger):
        self.config = config
        self.event_manager = event_manager
        self.set_logger(logger, 'Recycler')

        if self.config["recycle_on_start"]:
            self.event_manager.add_listener('bot_initialized', self.recycle_on_bot_start)

        self.event_manager.add_listener('item_bag_full', self.filter_recyclable_items, priority=-10)
        self.event_manager.add_listener('item_bag_full', self.recycle_items, priority=1000)

    @staticmethod
    def recycle_on_bot_start(bot):
        bot.fire("item_bag_full")

    def filter_recyclable_items(self, bot, recyclable_items=None):

        if recyclable_items is None:
            recyclable_items = bot.player_service.get_inventory()

        copy_of_recyclable_items = dict(recyclable_items)

        filtered_recyclable_items = {}

        item_filter_list = self.config["item_filter"]
        sorted_categories = sorted(item_filter_list.keys(), key=lambda x: item_filter_list[x]["priority"])
        for category_name in sorted_categories:
            category = item_filter_list[category_name]
            # If priority for category is 0, don't throw away items in category
            if category["priority"] <= 0:
                for item_type in category["items"]:
                    if item_type["item_id"] in copy_of_recyclable_items:
                        del copy_of_recyclable_items[item_type["item_id"]]
            else:
                # Max quantity to keep for category
                total_keep = category["total_keep"]

                # Keep better items first
                sorted_item_types = sorted(category["items"], key=lambda x: -1 * x["priority"])

                total_kept_quantity = 0
                for item_type in sorted_item_types:
                    if total_keep == total_kept_quantity:
                        break

                    item_id = item_type["item_id"]
                    if item_id not in recyclable_items:
                        continue

                    # Keep up to the lesser of item keep maximum or number of keep slots have remaining
                    max_keep_quantity = min(item_type.get("keep", total_keep), total_keep - total_kept_quantity)
                    current_quantity = recyclable_items[item_id]
                    discard_quantity = current_quantity - max_keep_quantity
                    if discard_quantity > 0:
                        filtered_recyclable_items[item_id] = discard_quantity
                        total_kept_quantity += discard_quantity

        return {"recyclable_items": filtered_recyclable_items}

    def recycle_items(self, bot, recyclable_items=None):

        if recyclable_items is None:
            return

        recycled_items = 0

        for item_type in recyclable_items:
            quantity = recyclable_items[item_type]
            item_name = bot.item_list[item_type]
            self.log("Recycling {} {}{}".format(quantity, item_name, "s" if quantity > 1 else ""), color="green")
            bot.api_wrapper.recycle_inventory_item(item_id=item_type, count=quantity).call()
            recycled_items += quantity

            sleep(2)

        if recycled_items > 0:
            self.log("Recycled {} items.".format(recycled_items), color="green")
