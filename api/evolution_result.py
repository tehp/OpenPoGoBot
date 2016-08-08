from api.json_encodable import JSONEncodable
from api.pokemon import Pokemon


class EvolutionResult(JSONEncodable):
    def __init__(self, data):
        self.data = data
        self.success = data.get("result", 0) == 1

    def was_successful(self):
        return self.success

    def get_pokemon(self):
        return Pokemon(self.data.get("evolved_pokemon_data")) if self.success else None

    def get_experience(self):
        return self.data.get("experience_awarded", 0) if self.success else 0

    def get_candy(self):
        return self.data.get("candy_awarded", 0) if self.success else 0
