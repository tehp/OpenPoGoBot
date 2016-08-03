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

    def navigate(self, map_cells):
        # type: (List[Cell]) -> None
        raise NotImplementedError
