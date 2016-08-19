from threading import Thread

import logging
from flask import Flask, redirect
from flask_socketio import SocketIO

from app import Plugin, kernel

from plugins.socket import myjson
from plugins.socket.botevents import BotEvents
from plugins.socket.uievents import UiEvents
from pokemongo_bot.navigation.camper_navigator import CamperNavigator

# pylint: disable=unused-variable, unused-argument

@kernel.container.register('socket', ['@config.socket', "@pokemongo_bot", '@event_manager', '@logger', '@go_there_navigator'], tags=['plugin'])
class Socket(Plugin):
    def __init__(self, config, bot, event_manager, logger, go_there_navigator):
        self.config = config
        self.event_manager = event_manager
        self.set_logger(logger, 'Socket')
        self.bot = bot
        self.go_there_navigator = go_there_navigator
        self.oldnavigator = None

        logging.getLogger('socketio').disabled = True
        logging.getLogger('engineio').disabled = True
        logging.getLogger('werkzeug').disabled = True

        event_manager.add_listener('set_destination', self.set_destination_event)

        SOCKET_THREAD = Thread(target=self.run_socket_server)
        SOCKET_THREAD.daemon = True
        SOCKET_THREAD.start()

    def set_destination_event(self, lat, lng):
        self.oldnavigator = self.bot.navigator
        self.go_there_navigator.set_destination(lat, lng)

        self.bot.navigator = self.go_there_navigator

        if isinstance(self.oldnavigator, CamperNavigator):
            self.oldnavigator.set_campsite(lat, lng)

        self.event_manager.add_listener('walking_finished', self.walking_finished_event)
        self.bot.fire("reset_navigation")

    def walking_finished_event(self):
        if self.oldnavigator is not None:
            # I would have just remove the listener but this result of loads of logs
            #self.event_manager.remove_listener('walking_finished', self.walking_finished_event)
            self.bot.navigator = self.oldnavigator
            self.oldnavigator = None
            self.bot.fire("reset_navigation")
            self.bot.fire("manual_destination_reached")

    def run_socket_server(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "OpenPoGoBotSocket"
        socketio = SocketIO(app, logging=False, engineio_logger=False, json=myjson)

        @app.route("/")
        def redirect_online():
            return redirect("http://openpogoui.nicontoso.eu")

        state = {}

        BotEvents(self.bot, socketio, state, self.event_manager)
        UiEvents(self.bot, socketio, state, self.event_manager, self.logger)

        self.log("Starting socket server...")

        socketio.run(
            app,
            host=self.config['socket_server']['host'] or '0.0.0.0',
            port=self.config['socket_server']['port'] or 8080,
            debug=False,
            use_reloader=False,
            log_output=False
        )
