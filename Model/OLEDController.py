import os
from oled.device import ssd1306
from oled.render import canvas
from PIL import ImageFont, ImageDraw
from pytweening import easeOutQuad, easeInQuad
from threading import Thread


class OLEDController(object):

    def __init__(self):

        self.device = ssd1306(port=1, address=0x3C)
        self.font = ImageFont.truetype(os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'oled/font/OpenSans.ttf'), 14)
        self.width = self.device.width
        self.height = self.device.height
        # Clear the screen, as it sometimes draws some artifacts when initialized
        self.clear()

    def clear(self):
        with canvas(self.device) as draw:
            draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def print_message(self, message):
        raise NotImplementedError("OLEDController.print_message is not complete yet")

    def run_load_animation(self, message_queue, complete_token):
        """Plays spin animation and prints loading message during carputer startup
        Runs animation on a new thread so that startup events continue on main thread as animation plays.
        :param message_queue: Queue for passing message text from Carputer.setup to screen
        :param complete: flag that signals that setup is complete when is_set() returns True
        :returns: thread on which the animation runs. Thread should be joined before returning
        :rtype: threading.Thread"""
        speed = -35
        out_animation = easeOutQuad
        in_animation = easeInQuad

        def draw_frame(animation, message, i, counterclockwise=False):
            """Draws a single frame of the loading spin animation with message underneath"""
            if counterclockwise:
                stop = 0
                start = max(int(animation(i / 360.0) * 360), 1)
            else:
                stop = max(int(animation(i / 360.0) * 360), 1)
                start = 0
            font_size = self.font.getsize(message)
            with canvas(self.device) as draw:
                draw.text(((self.width / 2) - (font_size[0] / 2), (3 * self.height / 4) - (font_size[1] / 2)), message,
                          font=self.font, fill=255)
                draw.arc(((self.width / 2) - (self.height / 4), 0, (self.width / 2) + (self.height / 4),
                          self.height / 2), start, stop, fill=255)

        def loop(queue, token):
            status = queue.get()
            while not token.is_set():
                for i in xrange(360, 0, speed):
                    if not queue.empty():
                        status = queue.get()
                    draw_frame(out_animation, status, i)
                for i in xrange(360, 0, speed):
                    if not queue.empty():
                        status = queue.get()
                    draw_frame(in_animation, status, i, counterclockwise=True)
            self.clear()

        t = Thread(target=loop, args=(message_queue, complete_token))
        t.start()
        return t

