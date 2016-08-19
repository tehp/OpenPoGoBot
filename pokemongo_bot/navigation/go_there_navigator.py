from app import kernel
from pokemongo_bot.navigation.destination import Destination
from pokemongo_bot.navigation.navigator import Navigator


@kernel.container.register('go_there_navigator', ['@config.core', '@api_wrapper'])
class GoThereNavigator(Navigator):
    def __init__(self, config, api_wrapper):
        # type: (Namespace, PoGoApi) -> None
        super(GoThereNavigator, self).__init__(config, api_wrapper)

        self.position = None

    def set_destination(self, lat, lng):
        # TODO get altitude?
        self.position = (lat, lng, 0)

    def navigate(self, map_cells):
        # type: (List[Cell]) -> List[Destination]

        yield Destination(*self.position, name="Manual destination", exact_location=True)
