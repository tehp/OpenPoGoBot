from pokemongo_bot.event_manager import manager


@manager.on('test')
def test_event(bot=None, value=0):
    return {
        'value': value+1
    }
