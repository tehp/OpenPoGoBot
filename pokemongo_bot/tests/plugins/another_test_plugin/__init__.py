from pokemongo_bot.event_manager import manager


# pylint: disable=unused-argument
@manager.on('another_test')
def test_event(bot=None, value=0):
    return {
        'value': value + 2
    }
