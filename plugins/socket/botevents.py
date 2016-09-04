
# pylint: disable=unused-variable, unused-argument

class BotEvents(object):
    def __init__(self, bot, socketio, state, event_manager):
        self.socketio = socketio
        self.state = state
        self.bot = bot

        event_manager.add_listener('bot_initialized', self.bot_initialized, priority=-1000)
        event_manager.add_listener('position_updated', self.position_update)

        event_manager.add_listener('gyms_found', self.gyms_found_event, priority=-2000)
        event_manager.add_listener('pokestops_found', self.pokestops_found_event, priority=-2000)
        event_manager.add_listener('pokestop_visited', self.pokestop_visited_event, priority=-2000)

        event_manager.add_listener('pokemon_caught', self.pokemon_caught_event, priority=-1000)
        event_manager.add_listener('pokemon_evolved', self.pokemon_evolved_event)
        event_manager.add_listener('after_transfer_pokemon', self.transfer_pokemon_event)

        event_manager.add_listener('player_level_up', self.player_level_up_event)

        event_manager.add_listener('route', self.on_route_event)
        event_manager.add_listener('manual_destination_reached', self.manual_destination_reached_event)

    def bot_initialized(self, bot):
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
            "coordinates": bot.api_wrapper.get_position(),
            "storage": {
                "max_item_storage": player.max_item_storage,
                "max_pokemon_storage": player.max_pokemon_storage
            }
        }

        # reinit state
        self.state.update(emitted_object)

        self.socketio.emit("bot_initialized", emitted_object, namespace="/event")

    def position_update(self, bot, coordinates=None):
        if coordinates is None:
            return
        emitted_object = {
            "coordinates": coordinates
        }
        self.state["coordinates"] = coordinates
        self.socketio.emit("position", emitted_object, namespace="/event")

    def gyms_found_event(self, bot=None, gyms=None):
        if gyms is None or len(gyms) == 0:
            return
        emitted_object = {
            "gyms": gyms
        }
        self.socketio.emit("gyms", emitted_object, namespace="/event")

    def pokestops_found_event(self, bot=None, pokestops=None):
        if pokestops is None or len(pokestops) == 0:
            return
        emitted_object = {
            "pokestops": pokestops
        }
        self.socketio.emit("pokestops", emitted_object, namespace="/event")

    def pokestop_visited_event(self, bot=None, pokestop=None):
        if pokestop is None:
            return
        emitted_object = {
            "pokestop": pokestop
        }
        self.socketio.emit("pokestop_visited", emitted_object, namespace="/event")

    def pokemon_caught_event(self, bot=None, pokemon=None, position=None):
        if pokemon is None:
            return
        emitted_object = {
            "pokemon": pokemon,
            "position": position
        }
        self.socketio.emit("pokemon_caught", emitted_object, namespace="/event")

    def pokemon_evolved_event(self, bot=None, pokemon=None, evolution=None):
        if pokemon is None:
            return
        emitted_object = {
            "pokemon": pokemon,
            "evolution": evolution
        }
        self.socketio.emit("pokemon_evolved", emitted_object, namespace="/event")

    def transfer_pokemon_event(self, bot=None, pokemon=None):
        if pokemon is None:
            return
        emitted_object = {
            "pokemon": pokemon
        }
        self.socketio.emit("transfered_pokemon", emitted_object, namespace="/event")

    def player_level_up_event(self, level=None):
        player = self.bot.player_service.get_player()
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
        self.socketio.emit("player_stats", emit_object, namespace="/event")

    def on_route_event(self, bot=None, route=None):
        if route is not None:
            self.socketio.emit("route", route, namespace="/event")

    def manual_destination_reached_event(self, bot=None):
        self.socketio.emit("manual_destination_reached")
