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

def log(text, color='yellow'):
    logger.log(text, color=color, fire_event=False, prefix='UI')

def register_ui_events(socketio, state):

    @socketio.on("connect", namespace="/event")
    def connect():
        log("Web client connected")
        if "username" in state:
            emitted_object = state.copy()
            del emitted_object["bot"]
            socketio.emit("bot_initialized", emitted_object, namespace="/event")

    @socketio.on("disconnect", namespace="/event")
    def disconnect():
        log("Web client disconnected")

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
            log("Web UI action: Transfer")

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
                log("Transferring {0} (#{1}) with CP {2} and IV {3}".format(pokemon_name,
                                                                            pokemon_num,
                                                                            pokemon_cp,
                                                                            pokemon_potential), color="green")

    @socketio.on("evolve_pokemon", namespace="/event")
    def client_ask_for_evolve(evt):
        if "bot" in state:
            log("Web UI action: Evolve")

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
                    log('Evolved {} into {}'.format(bot.pokemon_list[pokemon.pokemon_id - 1]['Name'], bot.pokemon_list[evolved_id - 1]['Name']), color="green")

                    manager.fire_with_context('pokemon_evolved', bot, pokemon=pokemon, evolution=evolved_id)

    @socketio.on("drop_items", namespace="/event")
    def client_ask_for_item_drop(evt):
        if "bot" in state:
            bot = state["bot"]
            item_id = int(evt["id"])
            count = int(evt["count"])
            item_name = bot.item_list[item_id]
            log("Recycling {} {}{}".format(count, item_name, "s" if count > 1 else ""))
            bot.api_wrapper.recycle_inventory_item(item_id=item_id, count=count).call()
