from threading import Thread

import logging
from flask import Flask, redirect
from flask_socketio import SocketIO

from app import Plugin, kernel

from plugins.socket import myjson
from plugins.socket.botevents import BotEvents
from plugins.socket.uievents import UiEvents


# pylint: disable=unused-variable, unused-argument

@kernel.container.register('socket', ['@config.socket', '@event_manager', '@logger'], tags=['plugin'])
class Socket(Plugin):
    def __init__(self, config, event_manager, logger):
        self.config = config
        self.event_manager = event_manager
        self.set_logger(logger, 'Socket')

        logging.getLogger('socketio').disabled = True
        logging.getLogger('engineio').disabled = True
        logging.getLogger('werkzeug').disabled = True

        SOCKET_THREAD = Thread(target=self.run_socket_server)
        SOCKET_THREAD.daemon = True
        SOCKET_THREAD.start()

    def run_socket_server(self):
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "OpenPoGoBotSocket"
        socketio = SocketIO(app, logging=False, engineio_logger=False, json=myjson)

        @app.route("/")
        def redirect_online():
            return redirect("http://openpogoui.nicontoso.eu")

        state = {}

        BotEvents(socketio, state, self.event_manager)
        UiEvents(socketio, state, self.event_manager, self.logger)

        self.log("Starting socket server...")

        socketio.run(
            app,
            host=self.config['socket_server']['host'] or '0.0.0.0',
            port=self.config['socket_server']['port'] or 8080,
            debug=False,
            use_reloader=False,
            log_output=False
        )
