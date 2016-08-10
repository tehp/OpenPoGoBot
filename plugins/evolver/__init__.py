from pokemongo_bot import logger
from pokemongo_bot import manager
from pokemongo_bot import sleep

# pylint: disable=unused-argument

@manager.on('caught_pokemon', priority=0)
def _after_catch(event, bot, pokemon=None):
    _do_evolve(bot, bot.pokemon_list[pokemon.pokemon_id - 1]['Name'])

@manager.on('after_transfer_pokemon', priority=0)
def _after_transfer(event, bot, pokemon=None):
    _do_evolve(bot, bot.pokemon_list[pokemon.pokemon_id - 1]['Name'])

def _do_evolve(bot, name):
    if bot.config.evolve_pokemon:
        bot.api_wrapper.get_player().get_inventory()
        response_dict = bot.api_wrapper.call()
        pokemon_list = response_dict['pokemon']
        base_pokemon = _get_base_pokemon(bot, name)
        base_name = base_pokemon['name']
        pokemon_id = base_pokemon['id']
        num_evolve = base_pokemon['requirements']
        pokemon_candies = bot.candies.get(int(pokemon_id), 0)
        evolve_list = [str.lower(str(x)) for x in bot.config.evolve_filter]
        if base_name.lower() in evolve_list or 'all' in evolve_list:
            if num_evolve is None:
                _log('Can\'t evolve {}'.format(base_name), color='yellow')
                return

            pokemon_evolve = [pokemon for pokemon in pokemon_list if pokemon.pokemon_id is pokemon_id]
            if pokemon_evolve is None:
                return
            pokemon_evolve.sort(key=lambda p: p.combat_power, reverse=True)

            num_evolved = 0
            for pokemon in pokemon_evolve:
                if num_evolve < pokemon_candies:
                    break
                bot.api_wrapper.evolve_pokemon(pokemon_id=pokemon.unique_id)
                response = bot.api_wrapper.call()
                if response['evolution'].success:
                    pokemon_candies -= (num_evolve - 1)
                    num_evolved += 1
                    evolved_id = response['evolution'].get_pokemon().pokemon_id
                    _log('Evolved {} into {}'.format(base_name, bot.pokemon_list[evolved_id - 1]['Name']))

                    manager.fire_with_context('pokemon_evolved', bot, pokemon=pokemon, evolution=evolved_id)

                    sleep(2)
                else:
                    _log('Evolving {} failed'.format(base_name), color='red')
                    break

            if num_evolve > pokemon_candies and num_evolved is 0:
                _log('Not enough candies for {} to evolve'.format(base_name), color='yellow')
            elif len(pokemon_evolve) > num_evolved:
                _log('Stopped evolving due to error', color='red')
            else:
                _log('Evolved {} {}(s)'.format(num_evolved, base_name))

        # bot.update_inventory()
        # bot.get_pokemon()

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

def _log(text, color='green'):
    logger.log(text, color=color, prefix='Evolver')
