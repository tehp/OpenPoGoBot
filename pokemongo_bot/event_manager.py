from __future__ import print_function


class Event(object):
    def __init__(self, name):
        self.name = name
        self.listeners = set()
        print("Initialized new event: " + name)

    def add_listener(self, listener):
        self.listeners.add(listener)

    def remove_listener(self, listener):
        self.listeners.discard(listener)

    def fire(self, *args, **kwargs):
        for listener in self.listeners:
            listener(self.name, *args, **kwargs)


class EventManager(object):
    def __init__(self):
        self.events = {}

    def add_listener(self, name, listener):
        if name not in self.events:
            self.events[name] = Event(name)
        self.events[name].add_listener(listener)

    # decorator for event handlers
    # pylint: disable=invalid-name
    def on(self, *trigger_list):
        def register_handler(function):
            for trigger in trigger_list:
                self.add_listener(trigger, function)
            return function

        return register_handler

    # fire an event and call all event handlers
    def fire(self, event_name, *args, **kwargs):
        if event_name in self.events:
            self.events[event_name].fire(*args, **kwargs)

    # fire an event and call all event handlers, injecting the context as 2nd parameter
    def fire_with_context(self, event_name, bot, *args, **kwargs):
        if event_name in self.events:
            kwargs['bot'] = bot
            self.fire(event_name, *args, **kwargs)

    def remove_listener(self, name, listener):
        if name in self.events:
            self.events[name].remove_listener(listener)


# This will only be loaded once
# To use, add the following code to plugins:
# from event_manager import manager
# pylint: disable=invalid-name
manager = EventManager()
