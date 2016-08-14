# -*- coding: utf-8 -*-
from app import kernel

# TODO: Fix this entire plugin

# TODO: Use DI for config loading (requires PR #270)
import ruamel.yaml
import os # pylint: disable=wrong-import-order
with open(os.path.join(os.getcwd(), 'config/plugins/egg_incubator.yml'), 'r') as config_file:
    incubate_config = ruamel.yaml.load(config_file.read(), ruamel.yaml.RoundTripLoader)


@kernel.container.register('egg_incubator', ['@event_manager', '@logger'], tags=['plugin'])
class EggIncubator(object):
    def __init__(self, event_manager, logger):
        self.event_manager = event_manager
        self.logger = logger

        self.event_manager.add_listener('walking_started', self.incubate_eggs, priority=1000)
        self.event_manager.add_listener('incubate_egg', self.incubate_egg)

    def log(self, text, color="black"):
        self.logger.log(text, color=color, prefix="Incubator")

    def incubate_eggs(self, bot, coords=None):
        if coords is None:
            return
        eggs = bot.player_service.get_eggs()
        all_incubators = bot.player_service.get_egg_incubators()

        eggs = [egg for egg in eggs if egg.egg_incubator_id == ""]
        incubators = [incu for incu in all_incubators if incu.pokemon_id == 0 and (
            incubate_config["incubation_use_all"] or incu.item_id == 901)]

        in_use_count = len(all_incubators) - len(incubators)

        # order eggs by distance longest -> shortest
        eggs_by_distance = sorted(eggs, key=lambda x: x.total_distance, reverse=True)

        for egg_distance in incubate_config["incubation_priority"]:
            try:
                egg_restriction = int(incubate_config["incubation_restrict"][egg_distance])
            except KeyError:
                egg_restriction = None

            for egg in eggs_by_distance:
                if len(incubators) == 0:
                    log("No more free incubators ({}/{} in use)".format(in_use_count, len(all_incubators)), "yellow")
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

    def incubate_egg(self, bot, incubator=None, egg=None):
        if incubator is None or egg is None:
            return

        bot.api_wrapper.use_item_egg_incubator(item_id=incubator.unique_id, pokemon_id=egg.unique_id).call()
        self.log("Put a {}km egg into an incubator".format(int(egg.total_distance)), "green")
