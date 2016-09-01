from app import kernel


@kernel.container.register('pokemon_service', ['@stealth_api'])
class Pokemon(object):
    def __init__(self, api_wrapper):
        self.api_wrapper = api_wrapper
