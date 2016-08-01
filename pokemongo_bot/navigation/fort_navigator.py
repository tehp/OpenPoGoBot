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

                self.api_wrapper.fort_details(fort_id=fort_id,
                                              latitude=lat,
                                              longitude=lng)
                response_dict = self.api_wrapper.call()
                if response_dict is None:
                    fort_name = fort_id
                else:
                    fort_name = response_dict["fort"].fort_name

                logger.log("[#] Walking towards PokeStop \"{}\" ({} away)".format(fort_name, format_dist(dist, unit)))

                if dist > 0:
                    position = (lat, lng, 0.0)

                    self.stepper.walk_to(*position)
                    self.api_wrapper.player_update(latitude=lat, longitude=lng)
                    sleep(2)

                logger.log("[#] Now at PokeStop \"{}\"".format(fort_name))
