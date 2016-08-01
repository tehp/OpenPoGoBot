# -*- coding: utf-8 -*-

from pokemongo_bot.event_manager import manager
from pokemongo_bot import logger


@manager.on("item_bag_full", priority=-1000)
def filter_recyclable_items(bot, recyclable_items=None):

    if bot.config.item_filter is None:
        return

    if recyclable_items is None:
        response = bot.update_player_and_inventory()
        recyclable_items = response["inventory"]

    filtered_recyclable_items = {}

    for item_type in recyclable_items:
        if item_type not in bot.config.item_filter:
            continue
        max_keep_quantity = bot.config.item_filter[item_type].get("keep", None)
        if max_keep_quantity is None:
            continue
        current_quantity = recyclable_items[item_type]
        discard_quantity = current_quantity - max_keep_quantity
        if discard_quantity > 0:
            filtered_recyclable_items[item_type] = discard_quantity

    return {"recyclable_items": filtered_recyclable_items}


@manager.on("item_bag_full", priority=1000)
def recycle_items(bot, recyclable_items=None):

    if recyclable_items is None:
        return

    def log(text, color=None):
        logger.log(text, color=color, prefix="Recycler")

    recycled_items = 0

    for item_type in recyclable_items:
        quantity = recyclable_items[item_type]
        item_name = bot.item_list[item_type]
        log("Recycling {} {}{}".format(quantity, item_name, "s" if quantity > 1 else ""), color="green")
        bot.api_wrapper.recycle_inventory_item(item_id=item_type, count=quantity).call()
        recycled_items += quantity

    if recycled_items > 0:
        log("Recycled {} items.".format(recycled_items), color="green")
