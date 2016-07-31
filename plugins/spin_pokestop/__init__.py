# -*- coding: utf-8 -*-

from __future__ import print_function
import time

from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.event_manager import manager
from pokemongo_bot.utils import format_time
from pokemongo_bot import logger
from api.worldmap import PokeStop


@manager.on("pokestop_found", priority=-1000)
def filter_pokestops(pokestops=None):
    # type: (Optional[List[Fort]]) -> Dict[Str, List[PokeStop]]

    if pokestops is None:
        return {"pokestops": []}

    # Only grab PokeStops with coordinates
    pokestops = [pokestop for pokestop in pokestops if isinstance(pokestop, PokeStop) and pokestop.latitude is not None and pokestop.longitude is not None]
    return {"pokestops": pokestops}


@manager.on("pokestop_arrived", priority=1000)
def spin_pokestop(bot, pokestop=None):
    # type: (PokemonGoBot, Optional[List[Fort]]) -> None

    if pokestop is None:
        return

    def log(text, color="black"):
        logger.log(text, color=color, prefix="PokeStop")

    fort_id = pokestop.fort_id
    latitude = pokestop.latitude
    longitude = pokestop.longitude
    player_latitude = bot.position[0]
    player_longitude = bot.position[1]
    log("Spinning...", color="yellow")
    sleep(3)
    bot.api_wrapper.fort_search(fort_id=fort_id,
                                fort_latitude=latitude,
                                fort_longitude=longitude,
                                player_latitude=player_latitude,
                                player_longitude=player_longitude)

    response = bot.api_wrapper.call()
    if response is None:
        log("Got empty response from the API. Skipping.", color="red")
        return

    # TODO: Fix this to use a response object
    spin_details = response["FORT_SEARCH"]
    spin_result = spin_details.get("result")
    if spin_result == 1:
        log("Loot: ", "green")
        experience_awarded = spin_details.get("experience_awarded", False)
        if experience_awarded:
            log("+ {} XP".format(experience_awarded), "green")

        items_awarded = spin_details.get("items_awarded", [])
        if len(items_awarded) > 0:
            tmp_count_items = {}
            for item in items_awarded:
                item_id = item["item_id"]
                if item_id not in tmp_count_items:
                    tmp_count_items[item_id] = item["item_count"]
                else:
                    tmp_count_items[item_id] += item["item_count"]

            for item_id, item_count in tmp_count_items.items():
                item_id = str(item_id)
                item_name = bot.item_list[item_id]

                log("+ {} {}{}".format(item_count, item_name, "s" if item_count > 1 else ""), "green")
        else:
            log("Nothing found.", "yellow")

        pokestop_cooldown = spin_details.get("cooldown_complete_timestamp_ms")
        if pokestop_cooldown:
            seconds_since_epoch = time.time()
            cooldown_time = str(format_time((pokestop_cooldown / 1000) - seconds_since_epoch))
            log("PokeStop is on cooldown for {}.".format(cooldown_time))

        if not items_awarded and not experience_awarded and not pokestop_cooldown:
            log("Might be softbanned, try again later.", "red")
    elif spin_result == 2:
        log("PokeStop is out of range.", "red")
    elif spin_result == 3:
        log("PokeStop is already on cooldown.", "red")
        pokestop_cooldown = spin_details.get("cooldown_complete_timestamp_ms")
        if pokestop_cooldown:
            seconds_since_epoch = time.time()
            cooldown_time = str(format_time((pokestop_cooldown / 1000) - seconds_since_epoch))
            log("PokeStop is already on cooldown for {}.".format(cooldown_time), "red")
    elif spin_result == 4:
        log("Item bag is full.", "red")
        bot.fire("item_bag_full")
    else:
        log("I don't know what happened! Maybe servers are down?", "red")

    sleep(2)
