class Destination(object):
    def __init__(self, lat, lng, alt, name=None, exact_location=False):
        self.target_lat = lat
        self.target_lng = lng
        self.target_alt = alt
        self.name = name
        self.exact_location = exact_location
        self._steps = []

    def set_steps(self, step_list):
        self._steps = step_list

    def get_step_count(self):
        return len(self._steps)

    def step(self):
        for step in self._steps:
            # If the pointer has reached the end, check if we need to move to the exact location
            yield step

        if self.exact_location:
            yield (self.target_lat, self.target_lng, self.target_alt)
