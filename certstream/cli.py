import argparse
import datetime
import json
import logging
import sys
import termcolor

from signal import signal, SIGPIPE, SIG_DFL

import certstream

parser = argparse.ArgumentParser(description='Connect to the CertStream and process CTL list updates.')

parser.add_argument('--json', action='store_true', help='Output raw JSON to the console.')
parser.add_argument('--full', action='store_true', help='Output all SAN addresses as well')
parser.add_argument('--disable-colors', action='store_true', help='Disable colors when writing a human readable ')
parser.add_argument('--verbose', action='store_true', default=False, dest='verbose', help='Display debug logging.')
parser.add_argument('--url', default="wss://certstream.calidog.io", dest='url', help='Connect to a certstream server.')

def main():
    args = parser.parse_args()

    # Ignore broken pipes
    signal(SIGPIPE, SIG_DFL)

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    logging.basicConfig(format='[%(levelname)s:%(name)s] %(asctime)s - %(message)s', level=log_level)

    def _handle_messages(message, context):
        if args.json:
            sys.stdout.flush()
            sys.stdout.write(json.dumps(message) + "\n")
            sys.stdout.flush()
        else:
            if args.disable_colors:
                logging.debug("Starting normal output.")
                payload = "{} {} - {} {}\n".format(
                    "[{}]".format(datetime.datetime.fromtimestamp(message['data']['seen']).isoformat()),
                    message['data']['source']['url'],
                    message['data']['leaf_cert']['subject']['CN'],
                    "[{}]".format(", ".join(message['data']['leaf_cert']['all_domains'])) if args.full else ""
                )

                sys.stdout.write(payload)
            else:
                logging.debug("Starting colored output.")
                payload = "{} {} - {} {}\n".format(
                    termcolor.colored("[{}]".format(datetime.datetime.fromtimestamp(message['data']['seen']).isoformat()), 'cyan', attrs=["bold", ]),
                    termcolor.colored(message['data']['source']['url'], 'blue', attrs=["bold",]),
                    termcolor.colored(message['data']['leaf_cert']['subject']['CN'], 'green', attrs=["bold",]),
                    termcolor.colored("[", 'blue') + "{}".format(
                        termcolor.colored(", ", 'blue').join(
                            [termcolor.colored(x, 'white', attrs=["bold",]) for x in message['data']['leaf_cert']['all_domains']]
                        )
                    ) + termcolor.colored("]", 'blue') if args.full else "",
                )
                sys.stdout.write(payload)

            sys.stdout.flush()

    certstream.listen_for_events(_handle_messages, args.url, skip_heartbeats=True)

if __name__ == "__main__":
    main()
