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
    CERTSTREAM_URL = 'wss://certstream.calidog.io'
    _context = Context()

    def __init__(self, message_callback, skip_heartbeats=True):
        self.message_callback = message_callback
        self.skip_heartbeats = skip_heartbeats
        super(CertStreamClient, self).__init__(
            url=self.CERTSTREAM_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
        )

    def _on_open(self, _):
        logging.info("Connection established to CertStream! Listening for events...")

    def _on_message(self, _, message):
        frame = json.loads(message)

        if frame.get('message_type', None) == "heartbeat" and self.skip_heartbeats:
            return

        self.message_callback(frame, self._context)

    def _on_error(self, _, ex):
        if type(ex) == KeyboardInterrupt:
            raise
        logging.error("Error connecting to CertStream - {} - Sleeping for a few seconds and trying again...".format(ex))

def listen_for_events(message_callback, skip_heartbeats=True):
    logging.basicConfig(format='[%(levelname)s:%(name)s] %(asctime)s - %(message)s', level=logging.INFO)
    try:
        while True:
            c = CertStreamClient(message_callback, skip_heartbeats=skip_heartbeats)
            c.run_forever()
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Kill command received, exiting!!")

