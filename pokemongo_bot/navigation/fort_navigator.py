from datetime import datetime

from pokemongo_bot import logger
from pokemongo_bot.navigation.navigator import Navigator
from pokemongo_bot.utils import distance, format_dist
from pokemongo_bot.human_behaviour import sleep


class FortNavigator(Navigator):

    def navigate(self, map_cells):
        # type: (List[Cell]) -> None

        for cell in map_cells:
            pokestops = [pokestop for pokestop in cell.pokestops if
                         pokestop.latitude is not None and pokestop.longitude is not None]
            # gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]

            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            pokestops.sort(key=lambda x: distance(self.stepper.current_lat, self.stepper.current_lng, x.latitude, x.longitude))

            for fort in pokestops:
                lat = fort.latitude
                lng = fort.longitude
                unit = self.config.distance_unit  # Unit to use when printing formatted distance

                fort_id = fort.fort_id
                dist = distance(self.stepper.current_lat, self.stepper.current_lng, lat, lng)

                logger.log("[#] Found fort {} at distance {}".format(fort_id, format_dist(dist, unit)))

                if dist > 0:
                    logger.log("[#] Need to move closer to Pokestop")
                    position = (lat, lng, 0.0)

                    self.stepper.walk_to(*position)
                    self.api_wrapper.player_update(latitude=lat, longitude=lng)
                    sleep(2)

                self.api_wrapper.fort_details(fort_id=fort_id,
                                              latitude=lat,
                                              longitude=lng)
                response_dict = self.api_wrapper.call()
                if response_dict is None:
                    return
                fort_details = response_dict["fort"]
                fort_name = fort_details.fort_name
                logger.log("[#] Now at Pokestop: " + fort_name)
