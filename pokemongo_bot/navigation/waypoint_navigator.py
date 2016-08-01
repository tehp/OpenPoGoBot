from pokemongo_bot import logger
from pokemongo_bot.navigation.navigator import Navigator
from pokemongo_bot.utils import distance, format_dist
from pokemongo_bot.event_manager import manager


class WaypointNavigator(Navigator):

    def __init__(self, bot):
        # type: (PokemonGoBot) -> None
        super(WaypointNavigator, self).__init__(bot)

        self.waypoints = bot.config.navigator_waypoints
        self.pointer = 0

    def navigate(self, map_cells):
        # type: (List[Cell]) -> None
        while self.pointer < len(self.waypoints)-1:
            waypoint = self.waypoints[self.pointer]

            if waypoint is None:
                self.pointer += 1
                continue

            lat, lng = waypoint
            position = (lat, lng, 0.0)

            unit = self.config.distance_unit  # Unit to use when printing formatted distance

            dist = distance(self.stepper.current_lat, self.stepper.current_lng, lat, lng)

            logger.log("[#] Moving to waypoint at {},{} at distance {}".format(lat, lng, format_dist(dist, unit)))

            self.stepper.walk_to(*position)

            self.pointer += 1

        self.pointer = 0

    @manager.on("waypoint_add", priority=0)
    def waypoint_add(self, longitude, latitude):
        # type: (float, float) -> None
        self.waypoints.append((longitude, latitude))

    @manager.on("waypoint_remove", priority=0)
    def waypoint_remove(self, index):
        # type: (float, float) -> None
        try:
            self.waypoints[index] = None
        except KeyError:
            pass
