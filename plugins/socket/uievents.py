from flask import request


# pylint: disable=unused-variable, unused-argument
class UiEvents(object):
    def __init__(self, bot, socketio, state, event_manager, logger):
        self.logger = logger
        self.bot = bot

        @socketio.on("connect", namespace="/event")
        def connect():
            self.log("Web client connected")
            if "username" in state:
                emitted_object = state.copy()
                socketio.emit("bot_initialized", emitted_object, namespace="/event")

        # @socketio.on("disconnect", namespace="/event")
        # def disconnect():
        #     self.log("Web client disconnected")

        @socketio.on("pokemon_settings", namespace="/event")
        def client_ask_for_pokemon_settings():
            templates = self.bot.api_wrapper.get_item_templates()
            pokemon_settings = [t["pokemon_settings"] for t in templates if "pokemon_settings" in t]
            pokemon_settings = sorted(pokemon_settings, key=lambda p: p["pokemon_id"])
            socketio.emit("pokemon_settings", pokemon_settings, namespace="/event", room=request.sid)

        @socketio.on("pokemon_list", namespace="/event")
        def client_ask_for_pokemon_list():
            pokemon = self.bot.player_service.get_pokemon()
            candies = self.bot.player_service.get_candies()
            eggs = self.bot.player_service.get_eggs()

            emit_object = {
                "pokemon": pokemon,
                "candy": candies,
                "eggs_count": len(eggs)
            }
            socketio.emit("pokemon_list", emit_object, namespace="/event", room=request.sid)

        @socketio.on("inventory_list", namespace="/event")
        def client_ask_for_inventory_list():
            inventory = self.bot.player_service.get_inventory()

            emit_object = {
                "inventory": inventory
            }
            socketio.emit("inventory_list", emit_object, namespace="/event", room=request.sid)

        @socketio.on("player_stats", namespace="/event")
        def client_ask_for_player_stats():
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
            state["player"] = emit_object["player"]
            socketio.emit("player_stats", emit_object, namespace="/event", room=request.sid)

        @socketio.on("eggs_list", namespace="/event")
        def client_ask_for_eggs_list():
            player = self.bot.player_service.get_player()
            eggs = self.bot.player_service.get_eggs()
            egg_incubators = self.bot.player_service.get_egg_incubators()

            emit_object = {
                "km_walked": player.km_walked,
                "eggs": eggs,
                "egg_incubators": egg_incubators
            }
            socketio.emit("eggs_list", emit_object, namespace="/event", room=request.sid)

        @socketio.on("transfer_pokemon", namespace="/event")
        def client_ask_for_transfer(evt):
            self.log("Web UI action: Transfer")

            pkm_id = int(evt["id"])

            all_pokemons = self.bot.player_service.get_pokemon()

            pokemon = self._find(lambda p: p.unique_id == pkm_id, all_pokemons)

            if pokemon is not None:
                self.bot.api_wrapper.release_pokemon(pokemon_id=int(evt["id"]))
                self.bot.fire('after_transfer_pokemon', pokemon=pokemon)

                pokemon_num = pokemon.pokemon_id
                pokemon_name = self.bot.pokemon_list[pokemon_num - 1]["Name"]
                pokemon_cp = pokemon.combat_power
                pokemon_potential = pokemon.potential
                self.log("Transferred {0} (#{1}) with CP {2} and IV {3}".format(pokemon_name,
                                                                                pokemon_num,
                                                                                pokemon_cp,
                                                                                pokemon_potential), color="green")

        @socketio.on("evolve_pokemon", namespace="/event")
        def client_ask_for_evolve(evt):
            self.log("Web UI action: Evolve")

            pkm_id = int(evt["id"])

            all_pokemons = self.bot.player_service.get_pokemon()

            pokemon = self._find(lambda p: p.unique_id == pkm_id, all_pokemons)

            if pokemon is not None:
                response = self.bot.api_wrapper.evolve_pokemon(pokemon_id=int(evt["id"]))
                if response['evolution'].success:
                    evolved_id = response['evolution'].get_pokemon().pokemon_id
                    self.log('Evolved {} into {}'.format(self.bot.pokemon_list[pokemon.pokemon_id - 1]['Name'],
                                                         self.bot.pokemon_list[evolved_id - 1]['Name']), color="green")

                    event_manager.fire_with_context('pokemon_evolved', self.bot, pokemon=pokemon, evolution=evolved_id)

        @socketio.on("drop_items", namespace="/event")
        def client_ask_for_item_drop(evt):
            item_id = int(evt["id"])
            count = int(evt["count"])
            item_name = self.bot.item_list[item_id]
            self.log("Recycling {} {}{}".format(count, item_name, "s" if count > 1 else ""))
            self.bot.api_wrapper.recycle_inventory_item(item_id=item_id, count=count)

        @socketio.on("favorite_pokemon", namespace="/event")
        def client_ask_for_favorite_pokemon(evt):
            self.log("Web UI action: Favorite")

            pkm_id = int(evt["id"])
            favorite = evt["favorite"]

            self.bot.api_wrapper.set_favorite_pokemon(pokemon_id=pkm_id, is_favorite=favorite)

        @socketio.on("set_destination", namespace="/event")
        def client_set_destination(evt):
            self.log("Web UI action: Set Destination")
            self.bot.fire("set_destination", lat=evt["lat"], lng=evt["lng"])

    def log(self, text, color='yellow'):
        self.logger.log(text, color=color, fire_event=False, prefix='UI')

    @staticmethod
    def _find(f, seq):
        for item in seq:
            if f(item):
                return item
        return None
