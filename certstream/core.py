from __future__ import print_function

import json
import logging

import time
from websocket import WebSocketApp

class Context(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class CertStreamClient(WebSocketApp):
    _context = Context()

    def __init__(self, message_callback, url, skip_heartbeats=True, on_open=None, on_error=None, enable_logging=True):
        self.message_callback = message_callback
        self.skip_heartbeats = skip_heartbeats
        self.on_open_handler = on_open
        self.on_error_handler = on_error
        self.enable_logging = enable_logging
        super(CertStreamClient, self).__init__(
            url=url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
        )

    def _on_open(self, instance):
        if self.enable_logging:
            logging.info("Connection established to CertStream! Listening for events...")
        if self.on_open_handler:
            self.on_open_handler(instance)

    def _on_message(self, _, message):
        frame = json.loads(message)

        if frame.get('message_type', None) == "heartbeat" and self.skip_heartbeats:
            return

        self.message_callback(frame, self._context)

    def _on_error(self, instance, ex):
        if type(ex) == KeyboardInterrupt:
            raise
        if self.on_error_handler:
            self.on_error_handler(instance, ex)
        if self.enable_logging:
            logging.error("Error connecting to CertStream - {} - Sleeping for a few seconds and trying again...".format(ex))

def listen_for_events(message_callback, url, skip_heartbeats=True, setup_logger=True, on_open=None, on_error=None, enable_logging=True, **kwargs):
    if setup_logger:
        logging.basicConfig(format='[%(levelname)s:%(name)s] %(asctime)s - %(message)s', level=logging.INFO)

    try:
        while True:
            c = CertStreamClient(message_callback, url, skip_heartbeats=skip_heartbeats, on_open=on_open, on_error=on_error, enable_logging=enable_logging)
            c.run_forever(**kwargs)
            time.sleep(5)
    except KeyboardInterrupt:
        if enable_logging:
            logging.info("Kill command received, exiting!!")

