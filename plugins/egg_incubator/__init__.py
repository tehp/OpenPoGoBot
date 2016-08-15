# -*- coding: utf-8 -*-
from pokemongo_bot import sleep
from pokemongo_bot.event_manager import manager
from pokemongo_bot import logger

# TODO: Fix this entire plugin

# TODO: Use DI for config loading (requires PR #270)
import ruamel.yaml
import os # pylint: disable=wrong-import-order
with open(os.path.join(os.getcwd(), 'config/plugins/egg_incubator.yml'), 'r') as config_file:
    incubate_config = ruamel.yaml.load(config_file.read(), ruamel.yaml.RoundTripLoader)


def log(text, color="black"):
    logger.log(text, color=color, prefix="Incubator")


@manager.on("walking_started", priority=1000)
def incubate_eggs(bot, coords=None):

    if coords is None:
        return

    inventory = bot.update_player_and_inventory()

    eggs = [egg for egg in inventory["eggs"] if egg.egg_incubator_id == ""]
    incubators = [incu for incu in inventory["egg_incubators"] if incu.pokemon_id == 0 and (
        incubate_config["incubation_use_all"] is True or incu.item_id == 901)]

    in_use_count = len(inventory["egg_incubators"]) - len(incubators)

    # order eggs by distance longest -> shortest
    eggs_by_distance = sorted(eggs, key=lambda x: x.total_distance, reverse=True)

    for egg_distance in incubate_config["incubation_priority"]:
        try:
            egg_restriction = int(incubate_config["incubation_restrict"][egg_distance])
        except KeyError:
            egg_restriction = None

        for egg in eggs_by_distance:
            if len(incubators) == 0:
                log("No more free incubators ({}/{} in use)".format(in_use_count, len(inventory["egg_incubators"])), "yellow")
                return

            if egg_restriction is None:
                incubator = incubators.pop()
                bot.fire("incubate_egg", incubator=incubator, egg=egg)
                in_use_count += 1
            else:
                for incubator in incubators:
                    if incubator.item_id == egg_restriction:
                        bot.fire("incubate_egg", incubator=incubator, egg=egg)
                        in_use_count += 1
                        incubators.remove(incubator)
                        break


@manager.on("incubate_egg")
def incubate_egg(bot, incubator=None, egg=None):
    if incubator is None or egg is None:
        return

    bot.api_wrapper.use_item_egg_incubator(item_id=incubator.unique_id, pokemon_id=egg.unique_id).call()
    log("Put a {}km egg into an incubator".format(int(egg.total_distance)), "green")
