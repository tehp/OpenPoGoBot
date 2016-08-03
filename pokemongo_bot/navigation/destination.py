class Destination(object):
    def __init__(self, lat, lng, alt, name=None, exact_location=False):
        self.target_lat = lat
        self.target_lng = lng
        self.target_alt = alt
        self.name = name
        self.exact_location = exact_location
        self.steps = []
        self.pointer = 0

    def set_steps(self, step_list):
        self.steps = step_list

    def walk(self):
        try:
            # If the pointer has reached the end, check if we need to move to the exact location
            if self.pointer == len(self.steps):
                yield self.exact_location
                self.pointer += 1

            yield self.steps[self.pointer]
            self.pointer += 1
        except KeyError:
            pass
