from pokemongo_bot import logger
from pokemongo_bot.event_manager import manager


# pylint: disable=unused-argument

@manager.on("before_catch_pokemon")
def action_before_catch_pokemon(name=None, combat_power=None, pokemon_potential=None, **kwargs):
    logger.log(u"[] A Wild {} appeared! [CP {}] [Potential {}]".format(name, combat_power, pokemon_potential), "yellow")


@manager.on("catch_pokemon")
def action_catch_pokemon(*args, **kwargs):
    pass


@manager.on("after_catch_pokemon")
def action_after_catch_pokemon(name=None, combat_power=None, **kwargs):
    logger.log(u"[x] Captured {} [CP {}]".format(name, combat_power), "green")


@manager.on("use_pokeball")
def action_use_pokeball(pokeball_name=None, number_left=None, **kwargs):
    logger.log(u"[x] Using {}... ({} left!)".format(pokeball_name, number_left))


@manager.on("fort_found")
def action_fort_found(fort_name="Unknown", fort_distance=0.0, **kwargs):
    logger.log(u"[#] Found fort {} at distance {}".format(fort_name, fort_distance))


@manager.on("fort_moving")
def action_fort_moving(fort_name="Unknown"):
    logger.log(u"[#] Moving closer to {}".format(fort_name))


@manager.on("fort_arrived")
def action_fort_arrived(fort_name="Unknown"):
    logger.log(u"[#] Now at Pokestop: {}".format(fort_name))
