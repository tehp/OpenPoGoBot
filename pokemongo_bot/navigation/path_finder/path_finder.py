class PathFinder(object):
    """
        Abstract class for a path finder
    """

    def __init__(self, config):
        # type: (Namespace, Stepper) -> None
        self.config = config

    def path(self, from_lat, form_lng, to_lat, to_lng):  # pragma: no cover
        # type: (float, float, float, float) -> List[(float, float)]
        raise NotImplementedError
