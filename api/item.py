class Incubator(object):

    def __init__(self, data):
        self.unique_id = data.get("id", 0)
        self.item_id = data.get("item_id")
        self.incubator_type = data.get("incubator_type")
        self.uses_remaining = data.get("uses_remaining")
        self.pokemon_id = data.get("pokemon_id", 0)
        self.start_km_walked = data.get("start_km_walked", 0.0)
        self.target_km_walked = data.get("target_km_walked", 0.0)

    def __repr__(self):
        return str(self.__dict__)
