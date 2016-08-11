from pokemongo_bot import logger
from pokemongo_bot import sleep
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.navigator import Navigator
from pokemongo_bot.event_manager import manager


class CamperNavigator(Navigator):
    def __init__(self, config, api_wrapper):
        # type: (Namespace, PoGoApi) -> None
        super(CamperNavigator, self).__init__(config, api_wrapper)

        self.camping_sites = []

        if config.navigator_campsite is not None:
            lat, lng = config.navigator_campsite.split(',')
            self.camping_sites.append((float(lat), float(lng)))

        self.pointer = 0

    def navigate(self, map_cells):
        # type: (List[Cell]) -> List[Direction]
        if not len(self.camping_sites):
            current_lat, current_lng, _ = self.api_wrapper.get_position()
            self.camping_sites.append((current_lat, current_lng))

        try:
            print(self.camping_sites[self.pointer])
            lat, lng = self.camping_sites[self.pointer]
            position = (lat, lng, 0.0)

            yield Destination(*position, name="Camping position at {},{}".format(lat, lng), exact_location=True)

            sleep(5)
        except IndexError:
            logger.log("[#] No campsite location found", color="red")

    @manager.on("set_campsite", priority=0)
    def set_campsite(self, longitude, latitude):
        # type: (float, float) -> None
        self.camping_sites.append((longitude, latitude))
        self.pointer = len(self.camping_sites) - 1
