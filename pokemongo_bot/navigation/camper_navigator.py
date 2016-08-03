from pokemongo_bot import logger
from pokemongo_bot import sleep
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.navigator import Navigator
from pokemongo_bot.event_manager import manager


class CamperNavigator(Navigator):
    def __init__(self, bot):
        # type: (PokemonGoBot) -> None
        super(CamperNavigator, self).__init__(bot)

        if bot.config.navigator_campsite is None:
            self.camping_sites = [(bot.position[0], bot.position[1])]
        else:
            lat, lng = bot.config.navigator_campsite.split(',')
            self.camping_sites = [(float(lat), float(lng))]

        self.pointer = 0

    def navigate(self, map_cells):
        # type: (List[Cell]) -> None
        try:
            camp_site = self.camping_sites[self.pointer]

            lat, lng = camp_site
            position = (lat, lng, 0.0)

            yield Destination(*position, name="camping position at {},{}".format(lat, lng), exact_location=True)

            sleep(5)

        except KeyError:
            logger.log("[#] No campsite location found", color="red")

    @manager.on("set_campsite", priority=0)
    def set_campsite(self, longitude, latitude):
        # type: (float, float) -> None
        self.camping_sites.append((longitude, latitude))
        self.pointer = len(self.camping_sites) - 1
