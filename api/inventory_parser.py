import logging

from .json_encodable import JSONEncodable
from .pokemon import Egg, Pokemon
from .item import Incubator


class InventoryParser(JSONEncodable):
    def __init__(self):
        self.last_updated = 0
        self.items = {"count": 0}
        self.candy = {}
        self.pokedex_entries = {}

        self.pokemon = []
        self.eggs = []
        self.egg_incubators = []

    def update(self, data):
        data = data.get("inventory_delta", {})
        self.last_updated = data.get("new_timestamp_ms", 0)

        items = data.get("inventory_items", [])

        for item in items:
            if "inventory_item_data" in item:
                item = item.get("inventory_item_data", {})

                if "candy" in item:
                    num_candy = item["candy"].get("candy", 0)
                    family_id = item["candy"].get("family_id", 0)
                    if num_candy == 0 or family_id == 0:
                        del self.candy[family_id] 
                    else:
                        self.candy[family_id] = num_candy

                elif "egg_incubators" in item:
                    incubators = item['egg_incubators'].get('egg_incubator', [])
                    if isinstance(incubators, dict):
                        incubators = [incubators]
                    for incu in incubators:
                        self.egg_incubators.append(Incubator(incu))

                elif "item" in item:
                    item_id = item["item"].get("item_id", 0)
                    num_item = item["item"].get("count", 0)
                    if num_item == 0 or item_id == 0:
                        del self.items[item_id]
                    else:
                        self.items[item_id] = num_item

                elif "pokemon_data" in item:
                    current_data = item["pokemon_data"]
                    if current_data.get("is_egg", False):
                        self.eggs.append(Egg(current_data))
                    else:
                        self.pokemon.append(Pokemon(current_data))

            elif "deleted_item" in item:
                item = item.get("deleted_item", {})
                for type in item:
                    if type == "pokemon_id":
                        self.pokemon = [p for p in self.pokemon if p.unique_id != item["pokemon_id"]]
                    else:
                        logging.error("deleted_item not handled: %s", type)
                        logging.info("item: %s", item)
                        print("ERROR: unhandled deletion of " + type)
                        print(item)

        del self.items["count"]
        self.items["count"] = sum(self.items.values())
