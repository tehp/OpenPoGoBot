from pokemongo_bot import logger
def action_before_catch_pokemon(hook_params):
    logger.log("[#] A Wild {} appeared! [CP {}] [Potential {}]".format(hook_params["name"], hook_params["cp"],
                                                                       hook_params["pokemon_potential"]), "yellow")

def action_catch_pokemon(hook_params):
    pass

def action_after_catch_pokemon(hook_params):
    logger.log("[x] Captured {} [CP {}]".format(hook_params["name"], hook_params["cp"]), "green")

def action_use_pokeball(hook_params):
    logger.log("[x] Using {}... ({} left!)".format(hook_params["pokeball_name"], hook_params["number_left"]))