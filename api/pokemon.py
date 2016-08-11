from api.json_encodable import JSONEncodable


class Egg(JSONEncodable):

    def __init__(self, data):
        self.unique_id = data.get("id", 0)
        self.walked_distance = data.get("egg_km_walked_start", 0.0)
        self.total_distance = data.get("egg_km_walked_target", 0.0)
        self.creation_time_ms = data.get("creation_time_ms", 0)
        self.captured_cell_id = data.get("captured_cell_id", 0)
        self.egg_incubator_id = data.get("egg_incubator_id", "")


class Pokemon(JSONEncodable):

    def __init__(self, data):
        self.data = data
        self.unique_id = data.get("id", 0)
        self.pokemon_id = data.get("pokemon_id", 0)
        self.hp = data.get("individual_stamina", 0)
        self.max_hp = data.get("stamina_max", 0)
        self.combat_power = data.get("cp", 0)
        self.combat_power_multiplier = data.get("cp_multiplier", 0.0)
        self.additional_cp_multiplier = data.get("additional_cp_multiplier", 0.0)
        self.attack = data.get("individual_attack", 0)
        self.defense = data.get("individual_defense", 0)
        self.stamina = data.get("individual_stamina", 0)
        self.potential = round(float(self.attack + self.defense + self.stamina) / 45.0, 2)

        self.pokeball = data.get("pokeball", 1)
        self.move_1 = data.get("move_1", 0)
        self.move_2 = data.get("move_2", 0)
        self.creation_time_ms = data.get("creation_time_ms", 0)
        self.captured_cell_id = data.get("captured_cell_id", 0)
        self.height = data.get("height_m", 0.0)
        self.weight = data.get("weight_kg", 0.0)

        self.deployed_fort_id = data.get("deployed_fort_id", None)
