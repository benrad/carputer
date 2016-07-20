from oled.device import ssd1306
from oled.render import canvas
from PIL import ImageFont, ImageDraw
from pytweening import easeOutQuad, easeInQuad
from threading import Thread
from Queue import Queue
from time import sleep


class OLEDController(object):

    def __init__(self):

        self.device = ssd1306(port=1, address=0x3C)
        self.width = self.device.width
        self.height = self.device.height
        self.messageQueue = Queue(1)
        self.message = None
        # Clear the screen, as it sometimes draws some artifacts when initialized
        self.clear()

    def clear(self):
        with canvas(self.device) as draw:
            draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def print_message(self, message):
        with canvas(self.device) as draw:


    def runner(self):

        loop = Thread(target=self.load, args = (self.messageQueue, ))
        loop.start()
        while some_signal is True
            work, self.message = self.messageQueue.get()
            work()
        loop.join()

    def load_animation(self, messageQueue):
        speed = -35
        easeout = easeOutQuad
        easein = easeInQuad
        font = ImageFont.truetype("fonts/OpenSans.ttf", 14)
        for rep in xrange(length):
            for i in xrange(360, 0, speed):
                d = int(easeout(i/360.0)*360) if int(easeout(i/360.0)*360) > 1 else 1
                print d
                size = font.getsize(text)
                with canvas(self.device) as draw:
                    draw.text(((self.width/2)-(size[0]/2), (3*self.height/4)-(size[1]/2)), text, font=font, fill=255)
                    draw.arc(((self.width/2)-(self.height/4), 0, (self.width/2)+(self.height/4), self.height/2), d, 0, fill=255)
            for i in xrange(360, 0, speed):
                d = int(easein(i/360.0)*360) if int(easein(i/360.0)*360) > 1 else 1
                print d
                size = font.getsize(text)
                with canvas(self.device) as draw:
                    draw.text(((self.width/2)-(size[0]/2), (3*self.height/4)-(size[1]/2)), text, font=font, fill=255)
                    draw.arc(((self.width/2)-(self.height/4), 0, (self.width/2)+(self.height/4), self.height/2), 0, d, fill=255)
        self.clear()
