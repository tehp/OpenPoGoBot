from __future__ import print_function
import inspect
import time

from colorama import Fore, Style


class Event(object):

    @staticmethod
    def log(text, color=None):
        # type: (str, Optional[str]) -> None

        # Added because this code needs to run without importing the logger module.
        color_hex = {
            'green': Fore.GREEN,
            'yellow': Fore.YELLOW,
            'red': Fore.RED
        }
        string = str(text)
        output = u"[" + time.strftime("%Y-%m-%d %H:%M:%S") + u"] [Events] {}".format(string)
        if color in color_hex:
            output = color_hex[color] + output + Style.RESET_ALL
        print(output)

    def __init__(self, name):
        self.name = name
        self.listeners = {}
        self.num_listeners = 0

    def add_listener(self, listener, priority=0):
        self.num_listeners += 1
        if priority not in self.listeners:
            self.listeners[priority] = list()
        self.listeners[priority].append(listener)

    def remove_listener(self, listener):
        for priority in self.listeners:
            print(self.listeners[priority])
            self.listeners[priority].remove(listener)
        self.num_listeners -= 1

    def fire(self, **kwargs):
        if self.num_listeners == 0:
            self.log("WARNING: No handler has registered to handle event \"{}\"".format(self.name), color="yellow")

        # Sort events by priorities from greatest to least
        priorities = sorted(self.listeners, key=lambda event_priority: event_priority)
        for priority in priorities:
            for listener in list(self.listeners[priority]):

                # Pass in the event name to the handler
                kwargs["event_name"] = self.name

                # Slice off any named arguments that the handler doesn't need
                # pylint: disable=deprecated-method
                argspec = inspect.getargspec(listener)

                if not argspec.args:
                    return_dict = listener()
                else:
                    listener_args = {}
                    for key in argspec.args:
                        listener_args[key] = kwargs.get(key)
                    return_dict = listener(**listener_args)

                # If a handler returns False, this means that the event should be cancelled.
                if return_dict is False:
                    return False

                # Update the list of arguments to be used for the next function
                # This enables "pipeline"-like functionality - if arguments to an event handler
                # need to be processed in some way, another handler with higher priority can be
                # installed beforehand to do this without touching the original handler.
                if return_dict is not None:
                    kwargs.update(return_dict)
        return kwargs

    def print_event_pipeline(self):
        if self.num_listeners == 0:
            self.log("Event pipeline for \"{}\" is empty.".format(self.name))
        output = []
        priorities = sorted(self.listeners, key=lambda event_priority: event_priority)
        for priority in priorities:
            if len(self.listeners[priority]) == 0:
                continue
            func_names = [f.__name__ for f in self.listeners[priority]]
            output.append("{} ({})".format(priority, " -> ".join(func_names)))
        if len(output) == 0:
            self.log("Event pipeline for \"{}\" is empty.".format(self.name))
        self.log("Event pipeline for \"{}\":".format(self.name), color="yellow")
        self.log(" -> ".join(output) + "\n", color="yellow")


class EventManager(object):
    def __init__(self):
        self.events = {}

    def add_listener(self, name, listener, **kwargs):
        if name not in self.events:
            self.events[name] = Event(name)
        priority = kwargs.get("priority", 0)
        self.events[name].add_listener(listener, priority)

    # Decorator for event handlers.
    # Higher priority events run before lower priority ones.
    # pylint: disable=invalid-name
    def on(self, *trigger_list, **kwargs):
        priority = kwargs.get("priority", 0)

        def register_handler(function):
            for trigger in trigger_list:
                self.add_listener(trigger, function, priority=priority)
            return function

        return register_handler

    # Fire an event and call all event handlers.
    def fire(self, event_name, *args, **kwargs):
        if event_name in self.events:
            return self.events[event_name].fire(*args, **kwargs)

    # Fire an event and call all event handlers, injecting the bot context as a named parameter.
    def fire_with_context(self, event_name, bot, *args, **kwargs):
        if event_name in self.events:
            kwargs['bot'] = bot
            return self.fire(event_name, *args, **kwargs)

    def remove_listener(self, name, listener):
        if name in self.events:
            self.events[name].remove_listener(listener)

    def get_registered_events(self):
        event_list = []
        for event_name in self.events:
            if self.events[event_name].num_listeners > 0:
                event_list.append(event_name)

        return sorted(event_list)

    def print_all_event_pipelines(self):
        for event_name in self.events:
            self.events[event_name].print_event_pipeline()


# This will only be loaded once
# To use, add the following code to plugins:
# from event_manager import manager
# pylint: disable=invalid-name
manager = EventManager()
