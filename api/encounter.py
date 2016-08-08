from api.json_encodable import JSONEncodable
from .pokemon import Pokemon


class Encounter(JSONEncodable):
    def __init__(self):
        self.status = 0
        self.latitude = 0.0
        self.longitude = 0.0
        self.spawn_point_id = ""
        self.encounter_id = 0
        self.last_modified_timestamp_ms = 0
        self.time_until_hidden_ms = 0
        self.wild_pokemon = None
        self.probability = [0.0, 0.0, 0.0]

        self.captured_pokemon_id = 0
        self.xp = 0
        self.candy = 0
        self.activity_type = [0, 0, 0]
        self.stardust = 0

    def update_encounter(self, data):
        self.status = data.get("status", 0)

        pokemon_data = data.get("wild_pokemon", {})
        self.latitude = pokemon_data.get("latitude", 0.0)
        self.longitude = pokemon_data.get("longitude", 0.0)
        self.spawn_point_id = pokemon_data.get("spawn_point_id", "")
        self.encounter_id = pokemon_data.get("encounter_id", 0)
        self.last_modified_timestamp_ms = pokemon_data.get("last_modified_timestamp_ms", 0)
        self.time_until_hidden_ms = pokemon_data.get("time_until_hidden_ms", 0)

        pokemon_data = pokemon_data.get("pokemon_data", None)
        self.wild_pokemon = Pokemon(pokemon_data) if pokemon_data is not None else None

        self.probability = data.get("capture_probability", {}).get("capture_probability", [0.0, 0.0, 0.0])

    def update_catch_pokemon(self, data):
        self.status = data.get("status", 0)
        self.captured_pokemon_id = data.get("catpured_pokemon_id", 0)

        capture_award = data.get("capture_award", {})
        self.xp = sum(capture_award.get("xp", [0]))
        self.candy = sum(capture_award.get("candy", [0]))
        self.activity_type = capture_award.get("activity_type", [0, 0, 0])
        self.stardust = sum(capture_award.get("stardust", [0]))

    def __repr__(self):
        return str(self.__dict__)
