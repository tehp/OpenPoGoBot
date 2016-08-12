from pokemongo_bot import logger
from pokemongo_bot.event_manager import manager

# pylint: disable=unused-variable, unused-argument

def register_bot_events(socketio, state):

    @manager.on("bot_initialized")
    def bot_initialized(bot):
        player = bot.player_service.get_player()
        emitted_object = {
            "username": player.username,
            "level": player.level,
            "player": {
                "level": player.level,
                "unique_pokedex_entries": player.unique_pokedex_entries,
                "pokemons_captured": player.pokemons_captured,
                "next_level_xp": player.next_level_xp,
                "prev_level_xp": player.prev_level_xp,
                "experience": player.experience
            },
            "coordinates": bot.get_position(),
            "storage": {
                "max_item_storage": player.max_item_storage,
                "max_pokemon_storage": player.max_pokemon_storage
            }
        }

        # reinit state
        state.update(emitted_object)
        state["bot"] = bot

        socketio.emit("bot_initialized", emitted_object, namespace="/event")

    @manager.on("position_updated")
    def position_update(bot, coordinates=None):
        if coordinates is None:
            return
        emitted_object = {
            "coordinates": coordinates
        }
        state["coordinates"] = coordinates
        socketio.emit("position", emitted_object, namespace="/event")

    @manager.on("gyms_found", priority=-2000)
    def gyms_found_event(bot=None, gyms=None):
        if gyms is None or len(gyms) == 0:
            return
        emitted_object = {
            "gyms": gyms
        }
        socketio.emit("gyms", emitted_object, namespace="/event")

    @manager.on("pokestops_found", priority=-2000)
    def pokestops_found_event(bot=None, pokestops=None):
        if pokestops is None or len(pokestops) == 0:
            return
        emitted_object = {
            "pokestops": pokestops
        }
        socketio.emit("pokestops", emitted_object, namespace="/event")

    @manager.on("pokestop_visited", priority=-2000)
    def pokestop_visited_event(bot=None, pokestop=None):
        if pokestop is None:
            return
        emitted_object = {
            "pokestop": pokestop
        }
        socketio.emit("pokestop_visited", emitted_object, namespace="/event")

    @manager.on("pokemon_caught")
    def pokemon_caught(bot=None, pokemon=None, position=None):
        if pokemon is None:
            return
        emitted_object = {
            "pokemon": pokemon,
            "position": position
        }
        socketio.emit("pokemon_caught", emitted_object, namespace="/event")

    @manager.on("pokemon_evolved")
    def pokemon_evolved(bot=None, pokemon=None, evolution=None):
        if pokemon is None:
            return
        emitted_object = {
            "pokemon": pokemon,
            "evolution": evolution
        }
        socketio.emit("pokemon_evolved", emitted_object, namespace="/event")

    @manager.on("after_transfer_pokemon")
    def transfer_pokemon(bot=None, pokemon=None):
        if pokemon is None:
            return
        emitted_object = {
            "pokemon": pokemon
        }
        socketio.emit("transfered_pokemon", emitted_object, namespace="/event")

    @manager.on("route")
    def on_route_event(bot=None, route=None):
        if route is not None:
            socketio.emit("route", route, namespace="/event")
