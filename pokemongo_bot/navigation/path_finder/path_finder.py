class PathFinder(object):
    """
        Abstract class for a path finder
    """

    def __init__(self, stepper):
        # type: (Stepper) -> None
        self.stepper = stepper
        self.config = stepper.config

    def path(self, from_lat, form_lng, to_lat, to_lng):
        # type: (float, float, float, float) -> List[(float, float)]
        raise NotImplementedError
