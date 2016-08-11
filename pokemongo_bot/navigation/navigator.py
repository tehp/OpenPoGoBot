class Navigator(object):
    """
        Abstract class for a navigator
    """

    def __init__(self, config, api_wrapper):
        # type: (Namespace, PoGoApi) -> None
        self.config = config
        self.api_wrapper = api_wrapper

    def navigate(self, map_cells):  # pragma: no cover
        # type: (List[Cell]) -> List[Direction]
        raise NotImplementedError
