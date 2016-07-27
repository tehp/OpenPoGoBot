from pokemongo_bot import logger, event_manager
from pokemongo_bot.event_manager import manager

# pylint: disable=unused-argument

@manager.on("before_catch_pokemon")
def action_before_catch_pokemon(event, name=None, combat_power=None, pokemon_potential=None, **kwargs):
    logger.log("[#] A Wild {} appeared! [CP {}] [Potential {}]".format(name, combat_power, pokemon_potential), "yellow")

@manager.on("catch_pokemon")
def action_catch_pokemon(hook_params):
    pass

@manager.on("after_catch_pokemon")
def action_after_catch_pokemon(event, name=None, combat_power=None, **kwargs):
    logger.log("[x] Captured {} [CP {}]".format(name, combat_power), "green")

@manager.on("use_pokeball")
def action_use_pokeball(event, pokeball_name=None, number_left=None, **kwargs):
    logger.log("[x] Using {}... ({} left!)".format(pokeball_name, number_left))
