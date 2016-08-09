from flask import Flask, request

from pokemongo_bot import logger
from pokemongo_bot.event_manager import manager
from plugins.socket import myjson

# pylint: disable=unused-variable, unused-argument

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

    @socketio.on("evolve_pokemon", namespace="/event")
    def client_ask_for_evolve(evt):
        if "bot" in state:
            # print evt
            # print evt["id"]
            logger.log("Web UI action: Evolve", "yellow", fire_event=False)
            bot = state["bot"]
            # bot.pokemon_list
            # bot.api_wrapper.evolve_pokemon(pokemon_id=pokemon.unique_id).call()
