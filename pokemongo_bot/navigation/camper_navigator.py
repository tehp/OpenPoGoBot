from app import kernel
from pokemongo_bot.human_behaviour import sleep
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.navigator import Navigator


@kernel.container.register('camper_navigator', ['@config.core', '@api_wrapper', '@logger'])
class CamperNavigator(Navigator):
    def __init__(self, config, api_wrapper, logger):
        # type: (Namespace, PoGoApi, Logger) -> None
        super(CamperNavigator, self).__init__(config, api_wrapper)

        self.camping_sites = []
        self.logger = logger

        if config['movement']['navigator_campsite'] is not None:
            lat, lng = config['movement']['navigator_campsite']
            self.camping_sites.append((float(lat), float(lng)))

        self.pointer = 0

    def navigate(self, map_cells):
        # type: (List[Cell]) -> List[Direction]
        if not len(self.camping_sites):
            current_lat, current_lng, _ = self.api_wrapper.get_position()
            self.camping_sites.append((current_lat, current_lng))

        try:
            lat, lng = self.camping_sites[self.pointer]
            position = (lat, lng, 0.0)

            yield Destination(*position, name="Camping position at {},{}".format(lat, lng), exact_location=True)

            sleep(5)
        except IndexError:
            self.logger.log("No campsite location found", color="red", prefix="Camper")

    def set_campsite(self, longitude, latitude):
        # type: (float, float) -> None
        self.camping_sites.append((longitude, latitude))
        self.pointer = len(self.camping_sites) - 1
