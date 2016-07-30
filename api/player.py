import datetime


class Player(object):

    def __init__(self):
        self.username = "Unknown"
        self.max_pokemon_storage = 250
        self.max_item_storage = 350
        self.creation_timestamp_ms = 0
        self.pokecoin = 0
        self.stardust = 0
        self.km_walked = 0.0
        self.pokeballs_thrown = 0
        self.unique_pokedex_entries = 0
        self.pokemon_caught_by_type = b""
        self.pokemons_captured = 0
        self.pokemons_encountered = 0
        self.poke_stop_visits = 0
        self.next_level_xp = 0
        self.prev_level_xp = 0
        self.experience = 0
        self.level = 1

    def update_get_player(self, data):
        data = data.get("player_data", {})
        self.username = data.get("username", "Unknown")
        self.max_pokemon_storage = data.get("max_pokemon_storage", 250)
        self.max_item_storage = data.get("max_item_storage", 350)
        self.creation_timestamp_ms = data.get("creation_timestamp_ms", 0)
        self.update_currency(data.get("currencies", {}))

    def update_get_inventory_stats(self, data):
        items = data.get("inventory_delta", {}).get("inventory_items", [])
        for item in items:
            item = item.get("inventory_item_data", {})
            if "player_stats" in item:
                item = item.get("player_stats", {})
                self.km_walked = item.get("km_walked", 0.0)
                self.pokeballs_thrown = item.get("pokeballs_thrown", 0)
                self.unique_pokedex_entries = item.get("unique_pokedex_entries", 0)
                self.pokemon_caught_by_type = item.get("pokemon_caught_by_type", b"")
                self.pokemons_captured = item.get("pokemons_captured", 0)
                self.pokemons_encountered = item.get("pokemons_encountered", 0)
                self.poke_stop_visits = item.get("poke_stop_visits", 0)
                self.next_level_xp = item.get("next_level_xp", 0)
                self.prev_level_xp = item.get("prev_level_xp", 0)
                self.experience = item.get("experience", 0)
                self.level = item.get("level", 1)

    def update_currency(self, currency_array):
        for currency in currency_array:
            name = currency.get("name", "Unknown").lower()
            amount = currency.get("amount", 0)
            setattr(self, name, amount)

    def get_creation_date(self):
        return datetime.datetime.fromtimestamp(self.creation_timestamp_ms / 1e3)

    def __repr__(self):
        return str(self.__dict__)
