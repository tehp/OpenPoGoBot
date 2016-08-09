import unittest
import os
import pytest
from mock import Mock

from pokemongo_bot.event_manager import EventManager, Event
from pokemongo_bot.plugins import PluginManager


class EventManagerTest(unittest.TestCase):
    @staticmethod
    def test_add_listener():
        event_manager = EventManager()

        test_listener = Mock()
        event_manager.add_listener('test', test_listener)

        assert isinstance(event_manager.events['test'], Event)

        assert len(event_manager.events['test'].listeners[0]) == 1

    @staticmethod
    def test_add_listener_priorities():
        event_manager = EventManager()

        test_listener = Mock()
        event_manager.add_listener('test', test_listener, priority=-100)
        event_manager.add_listener('test', test_listener, priority=100)

        assert isinstance(event_manager.events['test'], Event)

        assert len(event_manager.events['test'].listeners[-100]) == 1
        assert len(event_manager.events['test'].listeners[100]) == 1

    @staticmethod
    def test_remove_listener():
        event_manager = EventManager()

        test_listener = Mock()
        event_manager.add_listener('test', test_listener, priority=10)

        assert isinstance(event_manager.events['test'], Event)
        assert len(event_manager.events['test'].listeners) == 1

        event_manager.remove_listener('test', test_listener)

        assert isinstance(event_manager.events['test'], Event)
        assert len(event_manager.events['test'].listeners[10]) == 0

    @staticmethod
    def test_get_registered_events():
        event_manager = EventManager()

        test_listener = Mock()
        event_manager.add_listener('test', test_listener)

        events = event_manager.get_registered_events()

        assert len(events) == 1
        assert 'test' in events

    @staticmethod
    def test_fire():
        event_manager = EventManager()

        # pylint: disable=unused-argument
        def test_listener(value=None):
            return {
                'value': 'first'
            }

        # pylint: disable=unused-argument
        def test_listener_late(value=None):
            return {
                'value': 'second'
            }

        event_manager.add_listener('test', test_listener_late, priority=100)
        event_manager.add_listener('test', test_listener, priority=-100)

        return_data = event_manager.fire('test', value=None)

        assert return_data['value'] == 'second'

    @staticmethod
    def test_fire_cancelled():
        event_manager = EventManager()

        def test_listener():
            return {
                'value': 'first'
            }

        def test_listener_late():
            return False

        event_manager.add_listener('test', test_listener_late, priority=100)
        event_manager.add_listener('test', test_listener, priority=-100)

        return_data = event_manager.fire('test', value=None)

        assert return_data is False

    @staticmethod
    def test_fire_no_listeners():

        import sys
        from io import StringIO

        out = StringIO()
        sys.stdout = out

        event_manager = EventManager()

        event_manager.events['test'] = Event('test')
        event_manager.fire('test', value=None)

        assert 'WARNING: No handler has registered to handle event "test"' in out.getvalue().strip()


    @staticmethod
    def test_fire_with_context():
        event_manager = EventManager()

        def test_listener(bot=None):
            bot()

        event_manager.add_listener('test', test_listener, priority=-100)

        bot = Mock()
        event_manager.fire_with_context('test', bot)

        bot.assert_called_once()
