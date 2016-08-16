from app import kernel
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.navigator import Navigator
from pokemongo_bot.utils import distance


@kernel.container.register('fort_navigator', ['@config.core', '@api_wrapper'])
class FortNavigator(Navigator):
    def navigate(self, map_cells):
        # type: (List[Cell]) -> List([Destination])

        for cell in map_cells:
            pokestops = [pokestop for pokestop in cell.pokestops if
                         pokestop.latitude is not None and pokestop.longitude is not None]
            # gyms = [gym for gym in cell['forts'] if 'gym_points' in gym]

            # Sort all by distance from current pos- eventually this should
            # build graph & A* it
            current_lat, current_lng, _ = self.api_wrapper.get_position()
            pokestops.sort(key=lambda x, lat=current_lat, lng=current_lng: distance(lat, lng, x.latitude, x.longitude))

            for fort in pokestops:

                response_dict = self.api_wrapper.fort_details(
                    fort_id=fort.fort_id,
                    latitude=fort.latitude,
                    longitude=fort.longitude
                ).call()

                if response_dict is None:
                    fort_name = fort.fort_id
                else:
                    fort_name = response_dict["fort"].fort_name

                if isinstance(fort_name, bytes):
                    fort_name = fort_name.decode()

                yield Destination(fort.latitude, fort.longitude, 0.0, name="PokeStop \"{}\"".format(fort_name))
