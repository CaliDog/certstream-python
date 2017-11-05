# coding=utf-8
import Queue
import json

import os

import itertools
import urwid
import urwid.curses_display
import threading
import certstream

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

"""
This is the very hacky result of a weekend fighting with Urwid to create a more gui-driven experience for CertStream (and an 
attempt to replicate the feed watcher on certstream.calidog.io). I spent more time than I care to admit to messing with this 
and hit my breaking point :-/ 

If anyone else feels like taking this up let me know, and I'll be happy to help! Otherwise this will inevitably be garbage 
collected at some point in the future. 
"""

urwid.set_encoding("UTF-8")

PALETTE = [
    ('headings', 'white,underline', 'black', 'bold,underline'), # bold text in monochrome mode
    ('body_text', 'light green', 'black'),
    ('heartbeat_active', 'light red', 'black'),
    ('heartbeat_inactive', 'light green', 'black'),
    ('buttons', 'yellow', 'dark green', 'standout'),
    ('section_text', 'body_text'), # alias to body_text
]

class CertStreamGui(object):
    INTRO_MESSAGE = u"""
   _____          _    _____ _                            
  / ____|        | |  / ____| |                           
 | |     ___ _ __| |_| (___ | |_ _ __ ___  __ _ _ __ ___  
 | |    / _ \ '__| __|\___ \| __| '__/ _ \/ _` | '_ ` _ \ 
 | |___|  __/ |  | |_ ____) | |_| | |  __/ (_| | | | | | |
  \_____\___|_|   \__|_____/ \__|_|  \___|\__,_|_| |_| |_|

Welcome to CertStream CLI 1.0!

We're waiting on certificates to come in, so hold tight!

Protip: Looking for the old CertStream CLI behavior? Use the --grep flag!

{}
    """

    COUNTER_FORMAT = u"┤ {}/{} ├"

    FOOTER_START = "Certstream 1.0 | "

    HEARTBEAT_ICON = u'\u2764'

    def __init__(self):
        self.message_queue = Queue.Queue()
        self.message_list = []
        self.counter_text = urwid.Text(self.COUNTER_FORMAT.format('0', '0'))
        self.seen_message = False
        self._heartbeat_is_animating = False
        self.setup_widgets()
        self.setup_certstream_listener()
        self._animate_waiter()


    def setup_widgets(self):
        self.intro_frame = urwid.LineBox(
            urwid.Filler(
                urwid.Text(('body_text', self.INTRO_MESSAGE.format("")), align=urwid.CENTER),
                valign=urwid.MIDDLE,
            )
        )

        self.frame = urwid.Frame(
            body=self.intro_frame,
            footer=urwid.Text(
                [self.FOOTER_START, ('heartbeat_inactive', self.HEARTBEAT_ICON)],
                align=urwid.CENTER
            )
        )

        self.loop = urwid.MainLoop(
            urwid.AttrMap(self.frame, 'body_text'),
            unhandled_input=show_or_exit,
            palette=PALETTE,
        )

        self.list_walker = urwid.SimpleListWalker(self.message_list)
        self.list_box = urwid.ListBox(self.list_walker)
        urwid.connect_signal(self.list_walker, "modified", self.item_focused)

    def setup_certstream_listener(self):
        self.draw_trigger = self.loop.watch_pipe(self.process_trigger)

        self.certstream_thread = threading.Thread(
            target=certstream.listen_for_events,
            kwargs={
                "message_callback": self.cert_processor,
                "skip_heartbeats": False,
                # "on_connect": on_connect
            },
        )
        self.certstream_thread.setDaemon(True)
        self.certstream_thread.start()

    def cert_processor(self, message, context):
        self.message_queue.put(message)
        os.write(self.draw_trigger, "TRIGGER")

    def process_trigger(self, _):
        while True:
            try:
                message = self.message_queue.get_nowait()
                self.process_message(message)
            except Queue.Empty:
                break

        self.loop.draw_screen()

    def _animate_waiter(self):
        if self.seen_message:
            return

        skel = u"|{}==={}|"

        WIDTH = 28

        cycle = itertools.cycle(range(1, WIDTH) + list(reversed(range(0, WIDTH-1))))

        def _anim(loop, args):
            INTRO_MESSAGE, gui = args
            if gui.seen_message:
                return

            step = next(cycle)

            text = INTRO_MESSAGE.format(
                skel.format(
                    " " * step,
                    " " * ((WIDTH - step) - 1)
                )
            )

            gui.intro_frame.original_widget.original_widget.set_text(text)

            loop.set_alarm_in(0.1, _anim, (INTRO_MESSAGE, gui))

        self.loop.set_alarm_in(0.1, _anim, (self.INTRO_MESSAGE, self))

    def _animate_heartbeat(self, _=None, stage=0):
        if stage == 0:
            self.frame.set_footer(
                urwid.Text(
                    [self.FOOTER_START, ('heartbeat_active', self.HEARTBEAT_ICON)],
                    align=urwid.CENTER
                )
            )
            self.loop.set_alarm_in(0.5, self._animate_heartbeat, 1)
        elif stage == 1:
            self.frame.set_footer(
                urwid.Text(
                    [self.FOOTER_START, ('heartbeat_inactive', self.HEARTBEAT_ICON)],
                    align=urwid.CENTER
                )
            )
            self._heartbeat_is_animating = False

    def focus_right_panel(self, button, user_data):
        pass

    def item_focused(self):
        total = len(self.list_box.body)

        logging.info("item_focused called...")

        logging.info("Len {} | {}".format(
                len(self.list_walker),
                self.list_box.get_focus()[1]
            )
        )

        self.counter_text.set_text(
            self.COUNTER_FORMAT.format(
                total - self.list_box.get_focus()[1],
                total
            )
        )

        self.right_text.set_text(
            json.dumps(
                self.list_walker[self.list_box.get_focus()[1]].original_widget.user_data['data']['leaf_cert'],
                indent=4
            )
        )

    def process_message(self, message):
        if message['message_type'] == 'heartbeat' and not self._heartbeat_is_animating:
            self._heartbeat_is_animating = True
            self._animate_heartbeat()

        if not self.seen_message and message['message_type'] == 'certificate_update':
            self.right_text = urwid.Text('')
            self.frame.set_body(
                urwid.Columns(
                    widget_list=[
                        urwid.Pile(
                            [
                                SidelessLineBox(
                                    self.list_box,
                                    title="CertStream Messages",
                                    bline="",
                                ),
                                (
                                    'flow',
                                    urwid.Columns([
                                        ('fixed', 6, urwid.Text(u'└─────')),
                                        ('flow', self.counter_text),
                                        Divider('─'),
                                        ('fixed', 1, urwid.Text(u'┘')),
                                    ])
                                 )
                            ]
                        ),
                        SidelessLineBox(
                            urwid.Filler(
                                self.right_text,
                                valign=urwid.TOP
                            ),
                            title="Parsed JSON"
                        )
                    ],
                )
            )
            self.seen_message = True

        if message['message_type'] == 'certificate_update':
            _, original_offset = self.list_box.get_focus()
            self.list_walker.insert(0,
                urwid.AttrMap(
                    FauxButton(
                        "[{}] {} - {}".format(
                            message['data']['cert_index'],
                            message['data']['source']['url'],
                            message['data']['leaf_cert']['subject']['CN'],
                        ),
                        user_data=message,
                        on_press=self.focus_right_panel
                    ),
                    '',
                    focus_map='buttons'
                )
            )

            self.counter_text.set_text(
                self.COUNTER_FORMAT.format(
                    original_offset,
                    len(self.list_box.body) - 1
                )
            )

            offset = (len(self.list_box.body) - 1)

            logging.info("Disconnecting")
            urwid.disconnect_signal(self.list_walker, "modified", self.item_focused)
            logging.info("Setting focus")
            self.list_walker.set_focus(offset)
            logging.info("Reconnecting")
            urwid.connect_signal(self.list_walker, "modified", self.item_focused)
            logging.info("Done")

            self.right_text.set_text(
                json.dumps(
                    self.list_walker[offset - self.list_box.get_focus()[1] - 1].original_widget.user_data['data']['leaf_cert'],
                    indent=4
                )
            )

        self.loop.draw_screen()

    def run(self):
        self.loop.run()

class Selector(urwid.SelectableIcon):
    def __init__(self, text, cursor_position):
        super(Selector, self).__init__(text, cursor_position)

import logging
logging.basicConfig(filename='out.log', level=logging.DEBUG)

urwid.escape.SHOW_CURSOR = ''

gui = CertStreamGui()

from urwid.widget import WidgetWrap, Divider, SolidFill, Text
from urwid.container import Pile, Columns
from urwid.decoration import WidgetDecoration

class FauxButton(urwid.Button):
    button_left = Text("")
    button_right = Text("")

    def __init__(self, label, on_press=None, user_data=None):
        self.user_data = user_data
        super(FauxButton, self).__init__(label, on_press, user_data)


class SidelessLineBox(WidgetDecoration, WidgetWrap):

    def __init__(self, original_widget, title="", title_align="center",
                 tlcorner='┌', tline='─', lline='│',
                 trcorner='┐', blcorner='└', rline='│',
                 bline='─', brcorner='┘'):
        """
        Draw a line around original_widget.
        Use 'title' to set an initial title text with will be centered
        on top of the box.
        Use `title_align` to align the title to the 'left', 'right', or 'center'.
        The default is 'center'.
        You can also override the widgets used for the lines/corners:
            tline: top line
            bline: bottom line
            lline: left line
            rline: right line
            tlcorner: top left corner
            trcorner: top right corner
            blcorner: bottom left corner
            brcorner: bottom right corner
        .. note:: This differs from the vanilla urwid LineBox by discarding
            the a line if the middle of the line is set to either None or the
            empty string.
        """

        if tline:
            tline = Divider(tline)
        if bline:
            bline = Divider(bline)
        if lline:
            lline = SolidFill(lline)
        if rline:
            rline = SolidFill(rline)
        tlcorner, trcorner = Text(tlcorner), Text(trcorner)
        blcorner, brcorner = Text(blcorner), Text(brcorner)

        if not tline and title:
            raise ValueError('Cannot have a title when tline is unset')

        self.title_widget = Text(self.format_title(title))

        if tline:
            if title_align not in ('left', 'center', 'right'):
                raise ValueError('title_align must be one of "left", "right", or "center"')
            if title_align == 'left':
                tline_widgets = [('flow', self.title_widget), tline]
            else:
                tline_widgets = [tline, ('flow', self.title_widget)]
                if title_align == 'center':
                    tline_widgets.append(tline)
            self.tline_widget = Columns(tline_widgets)
            top = Columns([
                ('fixed', 1, tlcorner),
                self.tline_widget,
                ('fixed', 1, trcorner)
            ])

        else:
            self.tline_widget = None
            top = None

        middle_widgets = []
        if lline:
            middle_widgets.append(('fixed', 1, lline))
        middle_widgets.append(original_widget)
        focus_col = len(middle_widgets) - 1
        if rline:
            middle_widgets.append(('fixed', 1, rline))

        middle = Columns(middle_widgets,
                box_columns=[0, 2], focus_column=focus_col)

        if bline:
            bottom = Columns([
                ('fixed', 1, blcorner), bline, ('fixed', 1, brcorner)
            ])
        else:
            bottom = None

        pile_widgets = []
        if top:
            pile_widgets.append(('flow', top))
        pile_widgets.append(middle)
        focus_pos = len(pile_widgets) - 1
        if bottom:
            pile_widgets.append(('flow', bottom))
        pile = Pile(pile_widgets, focus_item=focus_pos)

        WidgetDecoration.__init__(self, original_widget)
        WidgetWrap.__init__(self, pile)

    def format_title(self, text):
        if len(text) > 0:
            return "┤ {} ├".format(text)
        else:
            return ""

    def set_title(self, text):
        if not self.title_widget:
            raise ValueError('Cannot set title when tline is unset')
        self.title_widget.set_text(self.format_title(text))
        self.tline_widget._invalidate()


gui.run()


