from math import floor

from pokemongo_bot import logger
from pokemongo_bot import sleep
from pokemongo_bot.navigation.navigator import Navigator
from pokemongo_bot.utils import distance, format_dist
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

            unit = self.config.distance_unit  # Unit to use when printing formatted distance
            dist = floor(distance(self.stepper.current_lat, self.stepper.current_lng, lat, lng))

            # Given the random delta we add to the
            if dist > 0:
                logger.log(
                    "[#] Moving to camping position at {},{} at distance {}".format(lat, lng, format_dist(dist, unit)))
                self.stepper.walk_to(*position)
                self.stepper.snap_to(*position)
            else:
                # fire any events on these cells
                logger.log("[#] Camping on {},{}".format(lat, lng))
                position_map_cells = self.bot.mapper.get_cells(lat, lng)
                self.bot.work_on_cells(position_map_cells)

            sleep(5)

        except KeyError:
            logger.log("[#] No campsite location found", color="red")

    @manager.on("set_campsite", priority=0)
    def set_campsite(self, longitude, latitude):
        # type: (float, float) -> None
        self.camping_sites.append((longitude, latitude))
        self.pointer = len(self.camping_sites) - 1
