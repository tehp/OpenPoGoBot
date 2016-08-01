# -*- coding: utf-8 -*-
from pokemongo_bot import sleep
from pokemongo_bot.event_manager import manager
from pokemongo_bot import logger


def log(text, color="black"):
    logger.log(text, color=color, prefix="Incubator")


@manager.on("walking_started", priority=1000)
def incubate_eggs(bot, coords=None):

    if coords is None:
        return

    if bot.config.incubation_fill:

        inventory = bot.update_player_and_inventory()

        # Hatch any eggs that need to be hatched
        bot.api_wrapper.get_hatched_eggs().call()
        sleep(3)

        eggs = [egg for egg in inventory["eggs"] if egg.egg_incubator_id == ""]
        incubators = [incu for incu in inventory["egg_incubators"] if incu.pokemon_id == 0 and (
            bot.config.incubation_use_all or incu.item_id == 901)]

        in_use_count = len(inventory["egg_incubators"]) - len(incubators)

        # order eggs by distance longest -> shortest
        eggs_by_distance = sorted(eggs, key=lambda x: x.total_distance, reverse=True)

        for egg_distance in bot.config.incubation_priority:
            try:
                egg_restrictions = bot.config.incubation_restrict[egg_distance]
            except KeyError:
                egg_restrictions = None

            for egg in eggs_by_distance:
                if len(incubators) == 0:
                    log("No more free incubators ({}/{} in use)".format(in_use_count, len(inventory["egg_incubators"])), "yellow")
                    return

                if egg_restrictions is None:
                    incubator = incubators.pop()
                    bot.fire("incubate_egg", incubatior=incubator, egg=egg)
                    in_use_count += 1
                else:
                    for incubator in incubators:
                        if incubator.item_id in egg_restrictions:
                            bot.fire("incubate_egg", incubatior=incubator, egg=egg)
                            in_use_count += 1


@manager.on("incubate_egg")
def incubate_egg(bot, incubator=None, egg=None):
    if incubator is None or egg is None:
        return

    bot.api_wrapper.use_item_egg_incubator(item_id=incubator.unique_id, pokemon_id=egg.unique_id).call()
    log("Put a {}km egg into an incubator".format(int(egg.total_distance)), "green")
