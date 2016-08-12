from flask import Flask, request

from pokemongo_bot import logger
from pokemongo_bot.event_manager import manager
from plugins.socket import myjson

# pylint: disable=unused-variable, unused-argument

def find(f, seq):
    for item in seq:
        if f(item):
            return item
    return None

def register_ui_events(socketio, state):

    @socketio.on("connect", namespace="/event")
    def connect():
        logger.log("Web client connected", "yellow", fire_event=False)
        if "username" in state:
            emitted_object = state.copy()
            del emitted_object["bot"]
            socketio.emit("bot_initialized", emitted_object, namespace="/event")

    @socketio.on("disconnect", namespace="/event")
    def disconnect():
        logger.log("Web client disconnected", "yellow", fire_event=False)

    @socketio.on("pokemon_settings", namespace="/event")
    def client_ask_for_pokemon_settings():
        if "bot" in state:
            bot = state["bot"]
            templates = bot.api_wrapper.download_item_templates().call()
            templates = templates["DOWNLOAD_ITEM_TEMPLATES"]["item_templates"]
            pokemon_settings = [t["pokemon_settings"] for t in templates if "pokemon_settings" in t]
            pokemon_settings = sorted(pokemon_settings, key=lambda p: p["pokemon_id"])
            socketio.emit("pokemon_settings", pokemon_settings, namespace="/event", room=request.sid)

    @socketio.on("pokemon_list", namespace="/event")
    def client_ask_for_pokemon_list():
        if "bot" in state:
            logger.log("Web UI action: Pokemon List", "yellow", fire_event=False)
            bot = state["bot"]
            bot.api_wrapper.get_player().get_inventory()
            inventory = bot.api_wrapper.call()

            emit_object = {
                "pokemon": inventory["pokemon"],
                "candy": inventory["candy"],
                "eggs_count": len(inventory["eggs"])
            }
            socketio.emit("pokemon_list", emit_object, namespace="/event", room=request.sid)

    @socketio.on("inventory_list", namespace="/event")
    def client_ask_for_inventory_list():
        if "bot" in state:
            logger.log("Web UI action: Inventory List", "yellow", fire_event=False)
            bot = state["bot"]
            bot.api_wrapper.get_player().get_inventory()
            inventory = bot.api_wrapper.call()

            emit_object = {
                "inventory": inventory["inventory"]
            }
            socketio.emit("inventory_list", emit_object, namespace="/event", room=request.sid)

    @socketio.on("player_stats", namespace="/event")
    def client_ask_for_player_stats():
        if "bot" in state:
            logger.log("Web UI action: Player Stats", "yellow", fire_event=False)
            bot = state["bot"]
            bot.api_wrapper.get_player().get_inventory()
            inventory = bot.api_wrapper.call()

            player = inventory["player"]
            emit_object = {
                "player": {
                    "level": player.level,
                    "unique_pokedex_entries": player.unique_pokedex_entries,
                    "pokemons_captured": player.pokemons_captured,
                    "next_level_xp": player.next_level_xp,
                    "prev_level_xp": player.prev_level_xp,
                    "experience": player.experience
                }
            }
            state["player"] = emit_object["player"]
            socketio.emit("player_stats", emit_object, namespace="/event", room=request.sid)

    @socketio.on("eggs_list", namespace="/event")
    def client_ask_for_eggs_list():
        if "bot" in state:
            logger.log("Web UI action: Eggs List", "yellow", fire_event=False)
            bot = state["bot"]
            bot.api_wrapper.get_player().get_inventory()
            inventory = bot.api_wrapper.call()

            emit_object = {
                "km_walked": inventory["player"].km_walked,
                "eggs": inventory["eggs"],
                "egg_incubators": inventory["egg_incubators"]
            }
            socketio.emit("eggs_list", emit_object, namespace="/event", room=request.sid)

    @socketio.on("transfer_pokemon", namespace="/event")
    def client_ask_for_transfer(evt):
        if "bot" in state:
            logger.log("Web UI action: Transfer", "yellow", fire_event=False)

            bot = state["bot"]
            pkm_id = int(evt["id"])

            bot.api_wrapper.get_player().get_inventory()
            all_pokemons = bot.api_wrapper.call()["pokemon"]

            pokemon = find(lambda p: p.unique_id == pkm_id, all_pokemons)

            if pokemon is not None:
                bot.api_wrapper.release_pokemon(pokemon_id=int(evt["id"])).call()
                bot.fire('after_transfer_pokemon', pokemon=pokemon)

                pokemon_num = pokemon.pokemon_id
                pokemon_name = bot.pokemon_list[pokemon_num - 1]["Name"]
                pokemon_cp = pokemon.combat_power
                pokemon_potential = pokemon.potential
                logger.log("Transferring {0} (#{1}) with CP {2} and IV {3}".format(pokemon_name,
                                                                                   pokemon_num,
                                                                                   pokemon_cp,
                                                                                   pokemon_potential))

    @socketio.on("evolve_pokemon", namespace="/event")
    def client_ask_for_evolve(evt):
        if "bot" in state:
            logger.log("Web UI action: Evolve", "yellow", fire_event=False)

            bot = state["bot"]
            pkm_id = int(evt["id"])

            bot.api_wrapper.get_player().get_inventory()
            all_pokemons = bot.api_wrapper.call()["pokemon"]

            pokemon = find(lambda p: p.unique_id == pkm_id, all_pokemons)

            if pokemon is not None:
                bot.api_wrapper.evolve_pokemon(pokemon_id=int(evt["id"]))
                response = bot.api_wrapper.call()
                if response['evolution'].success:
                    evolved_id = response['evolution'].get_pokemon().pokemon_id
                    logger.log('Evolved {} into {}'.format(bot.pokemon_list[pokemon.pokemon_id - 1]['Name'], bot.pokemon_list[evolved_id - 1]['Name']))

                    manager.fire_with_context('pokemon_evolved', bot, pokemon=pokemon, evolution=evolved_id)
