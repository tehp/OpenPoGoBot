class Navigator(object):
    """
        Abstract class for a navigator
    """

    def __init__(self, bot):
        # type: (PokemonGoBot) -> None
        self.bot = bot
        self.config = bot.config

        self.api_wrapper = bot.api_wrapper
        self.mapper = bot.mapper
        self.stepper = bot.stepper

    def navigate(self, map_cells):  # pragma: no cover
        # type: (List[Cell]) -> List[Direction]
        raise NotImplementedError
