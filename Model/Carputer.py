import sys
import traceback
import logging
from OBDController import NoOBDDataException
from threading import Thread, Event
from Queue import Queue
from time import sleep, time, mktime, strptime


class Carputer(object):

    def __init__(self, obdcontroller, gpscontroller, oledcontroller, drivedatabase):
        # trip variables, used for calculating trip stats
        self.running = False
        self.loop_thread = None
        self.total_gal = 0.0
        self.total_distance = 0.0

        self.obd = obdcontroller
        self.gps = gpscontroller
        self.screen = oledcontroller
        self.db = drivedatabase

    @staticmethod
    def get_track(degrees):
        """
        Converts degree measurement to cardinal track
        This is probably not especially accurate, but that's fine for now.
        """

        tracks = {xrange(39): 'N', xrange(39, 84): 'NE', xrange(84, 129): 'E',
                  xrange(129, 174): 'SE', xrange(174, 219): 'S', xrange(219, 264): 'SW',
                  xrange(264, 309): 'W', xrange(309, 354): 'NW', xrange(354, 360): 'N'}

        for key in tracks:
            if int(degrees) in key:
                return tracks[key]

    def gen_timestamp(self):
        """
        Converts date string from gps to epoch time and returns that as an int.
        """
        pattern = '%Y-%m-%dT%H:%M:%S'
        timestamp = int(mktime(strptime(self.gps.time, pattern)))
        return timestamp

    @staticmethod
    def create_message(values):
        """
        Takes data values in format trip average, MinPG, track and creates a
        properly-spaced string of averages to print to LCD

        Returns lcd-ready message that is broken in half by a newline.
        """
        trip_avg, minutes_per_gallon, track = values

        # Center messages on 16x2 LCD
        top_pad = (7 - len(minutes_per_gallon.split('.')[0])) * ' '
        top_message = top_pad + str(minutes_per_gallon)
        bottom_pad = (6 - len(track)) * ' '
        bottom_message = bottom_pad + track + ' | ' + str(trip_avg)

        # create single message
        message = top_message + '\n' + bottom_message
        return message

    # Data capture

    def poll_obd(self):
        """
        Gets current speed and mass air flow, returns instantaneous MPG and speed
        """
        speed = self.obd.speed
        maf = self.obd.maf

        # My calculation gives a constant of 7.100295,
        # but the accepted value seems to be 7.107
        mpg = 7.107 * speed / maf
        return {'MPG': str(mpg), 'SPD': str(speed)}

    def poll_gps(self):
        """
        Gets current latitude, longitude, and course
        """
        return {'LAT': str(self.gps.fix.latitude), 'LON': str(self.gps.fix.longitude),
                'TRA': str(self.gps.fix.track)}

    def get_data(self):
        """
        Gets speed and MAF from OBD; lat, long, track and timestamp from GPS; length of OBD 'tick' from systime and
        returns them as a dict of strings. Strings are returned to make joining into a db commit easier.
        """
        timestamp = str(self.gen_timestamp())
        gps_data = self.poll_gps()
        # Sys time is more granular than GPS module time, so use it since we care about the interval, not actual time
        # GPS can do better, I just haven't implemented it
        start = time()
        obd_data = self.poll_obd()
        tick_length = str(time() - start)

        """
        TODO: get speed from GPS instead of OBD?
        Advantages: probably more accurate, definitely faster, reduces load on OBD (which is the main bottleneck)
        Disadvantages: Can't continue tracking MPG data when satellite fix lost
        """
        return ({'TIMESTAMP': timestamp, 'MPG': obd_data['MPG'], 'SPD': obd_data['SPD'],
                 'LAT': gps_data['LAT'], 'LON': gps_data['LON'], 'TRA': gps_data['TRA'], 'TICK': tick_length})

    def process_data(self, data):
        """
        Processes data received from gps and obd instruments into current trip mpg average,
        minutes of driving at current speed to consume one gallon of fuel, and current cardinal track (based on gps val).

        Returns processed values as strings in format trip average, MinPG, track
        """
        # Fuel consumed in one second is (vss/3600)/mpg, so fuel/tick is that times the length of the tick
        # So then total mpg is (total distance)/(total gallons)
        speed = float(data['SPD'])
        mpg = float(data['MPG'])
        tick_length = float(data['TICK'])
        degrees = float(data['TRA'])

        tick_distance = (speed/3600.0) * tick_length
        # Consumtion could also be mpg/mph/3600
        tick_consumption = tick_distance/mpg if mpg else 0.0

        self.total_gal += tick_consumption
        self.total_distance += tick_distance

        try:
            trip_avg = round(self.total_distance/self.total_gal, 2)
        except ZeroDivisionError:
            trip_avg = 0.0
        logging.debug('tick length: {0}\ntick distance: {1}\nconsumption: {2}'
                      '\ntrip avg: {3}'.format(tick_length, tick_distance, tick_consumption, trip_avg))

        try:
            minutes_per_gallon = round(tick_length/(tick_consumption * 60.0), 2)

        except ZeroDivisionError:
            minutes_per_gallon = 0.0

        # get track as cardinal direction
        track = self.get_track(degrees)

        return str(trip_avg), str(minutes_per_gallon), track

    def setup(self):
        """Initializes GPS and OBD devices, waits for satellite fix, then creates DB table for drive"""

        # Loading animation is run on another thread so setup can occur while maintaining seamless animation
        message_queue = Queue(1)
        complete_token = Event()
        # Prime the queue
        message_queue.put('Initializing GPS')
        # Begin setup
        t = self.screen.run_load_animation(message_queue, complete_token)
        self.gps.start()
        message_queue.put('Connecting OBD')
        self.obd.connect()
        # Wait for GPS to get fix, as we'll use the GPS's time for timestamps
        message_queue.put('Waiting For Fix')
        while not self.gps.has_fix:
            sleep(.25)
        message_queue.put('Initializing DB')
        self.db.new_table(self.gen_timestamp())
        complete_token.set()
        t.join()

    def start(self):
        self.setup()
        # TODO: logging may not cover methods running on other threads, e.g. runloop
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            filename="/home/pi/" + self.db.current_table + ".log")
        self.loop_thread = Thread(target=self.run_loop)

        self.running = True
        # Is the change to False not seen by thread?
        self.loop_thread.start()

    def run_loop(self):
        while self.running:

            # TODO: Continue to collect data even when GPS loses satellite fix
            if not self.gps.has_fix:
                self.screen.clear()
                sleep(.5)
                self.screen.print_message('Lost Satellite Fix')
                sleep(.5)

            # get data, write to DB
            try:
                data = self.get_data()
                self.db.write_values(data)
                message = self.create_message(self.process_data(data))
                self.screen.clear()
                self.screen.print_message(message)

            except NoOBDDataException as e:
                # Raised in poll_obd when a bad message is received from OBD device (after car shuts off)
                logging.debug("Bad OBD message received, terminating")
                logging.debug("Command: {0}\nResponse: {1}".format(e.command, e.response))
                self.screen.clear()
                self.screen.print_message("No OBD Data Received")

            except Exception as e:
                self.screen.clear()
                self.screen.print_message(str(e.message)[:16] + '\n' + str(e.message)[16:])
                logging.debug(e.message)
                logging.debug(traceback.format_exc())
                logging.debug("----------------------\n\n")

        return None  # We're probably not shutting down gracefully because an error condition causes us to return before stop() is called

    def stop(self):
        # Signal to loop that it's time to stop
        self.running = False
        # Wait for the loop to terminate
        self.loop_thread.join(timeout=5)
        if self.loop_thread.is_alive():
            self.screen.clear()
            self.screen.print_message("Abnormal termination")
        for method in self.obd.disconnect, self.gps.stop, self.screen.clear:
            try:
                method()
            except Exception as e:
                logging.debug(e.message)
        self.screen.print_message("Powering off.")

