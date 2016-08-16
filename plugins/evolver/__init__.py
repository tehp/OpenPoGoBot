from app import Plugin
from app import kernel
from pokemongo_bot.human_behaviour import sleep

# pylint: disable=unused-argument


@kernel.container.register('evolver', ['@config.evolve_pokemon', '@event_manager', '@logger'], tags=['plugin'])
class Evolver(Plugin):
    def __init__(self, config, event_manager, logger):
        self.config = config
        self.event_manager = event_manager
        self.set_logger(logger, 'Evolver')
        self.event_manager.add_listener('pokemon_caught', self._after_catch, priority=0)
        self.event_manager.add_listener('after_transfer_pokemon', self._after_transfer, priority=0)

    def _after_catch(self, event, bot, pokemon=None):
        self._do_evolve(bot, bot.pokemon_list[pokemon.pokemon_id - 1]['Name'])

    def _after_transfer(self, event, bot, pokemon=None):
        self._do_evolve(bot, bot.pokemon_list[pokemon.pokemon_id - 1]['Name'])

    def _do_evolve(self, bot, name):
        pokemon_list = bot.player_service.get_pokemon()
        base_pokemon = self._get_base_pokemon(bot, name)
        base_name = base_pokemon['name']
        pokemon_id = base_pokemon['id']
        num_evolve = base_pokemon['requirements']
        pokemon_candies = bot.player_service.get_candy(int(pokemon_id))
        evolve_list = self.config["evolve_filter"]
        if base_name in evolve_list and evolve_list[base_name]["evolve"] is True:
            if num_evolve is None:
                self.log('Can\'t evolve {}'.format(base_name), color='yellow')
                return

            pokemon_evolve = [pokemon for pokemon in pokemon_list if pokemon.pokemon_id is pokemon_id]
            if pokemon_evolve is None:
                return
            pokemon_evolve.sort(key=lambda p: p.combat_power, reverse=True)

            num_evolved = 0
            for pokemon in pokemon_evolve:
                if num_evolve > pokemon_candies:
                    break
                bot.api_wrapper.evolve_pokemon(pokemon_id=pokemon.unique_id)
                response = bot.api_wrapper.call()
                if response['evolution'].success:
                    pokemon_candies -= (num_evolve - 1)
                    num_evolved += 1
                    evolved_id = response['evolution'].get_pokemon().pokemon_id
                    self.log('Evolved {} into {}'.format(base_name, bot.pokemon_list[evolved_id - 1]['Name']))

                    self.event_manager.fire_with_context('pokemon_evolved', bot, pokemon=pokemon,
                                                         evolution=evolved_id)

                    sleep(2)
                else:
                    self.log('Evolving {} failed'.format(base_name), color='red')
                    break
            if num_evolve > pokemon_candies:
                self.log('Not enough candies for {} to evolve'.format(base_name), color='yellow')
            elif len(pokemon_evolve) > num_evolved:
                self.log('Stopped evolving due to error', color='red')
            else:
                self.log('Evolved {} {}(s)'.format(num_evolved, base_name))

    @staticmethod
    def _get_base_pokemon(bot, name):
        pokemon_id = None
        num_evolve = None
        pokemon_name = name
        for pokemon in bot.pokemon_list:
            if pokemon['Name'] is not name:
                continue
            else:
                previous_evolutions = pokemon.get("Previous evolution(s)", [])
                if previous_evolutions:
                    pokemon_id = previous_evolutions[0]['Number']
                    pokemon_name = previous_evolutions[0]['Name']
                    num_evolve = bot.pokemon_list[int(pokemon_id) - 1].get('Next Evolution Requirements', None)
                    if num_evolve is not None:
                        num_evolve = num_evolve.get('Amount', None)
                else:
                    pokemon_id = pokemon['Number']
                    num_evolve = pokemon.get('Next Evolution Requirements', None)
                    if num_evolve is not None:
                        num_evolve = num_evolve.get('Amount', None)
                break
        return {'id': int(pokemon_id), 'requirements': num_evolve, 'name': pokemon_name}
