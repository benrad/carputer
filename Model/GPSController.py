"""
Used from http://www.stuffaboutcode.com/2013/09/raspberry-pi-gps-setup-and-python.html
Original author is Martin O'Hanlon. Modified for threading.
"""

from gps import *
import threading


class GPSController():
    def __init__(self):
        self.gpsd = gps(mode=WATCH_ENABLE)
        self.running = False
        self.thread = None

    def update(self):
        while self.running:
            self.gpsd.next()

    # todo: this and stop() changed 11/22. if gps issues, investigate here
    def run(self):
        self.running = True
        self.thread = threading.Thread(target=self.update)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    @property
    def fix(self):
        return self.gpsd.fix

    @property
    def has_fix(self):
        return self.gpsd.fix.mode != 1

    @property
    def time(self):
        # fix.time alternately returns date string or epoch, with no regularity
        return self.gpsd.utc.split('.')[0]  # Format: u'2016-01-03T22:51:50'
