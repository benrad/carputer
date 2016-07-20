__author__ = 'benradosevich'

import logging
import signal
import sys
import traceback
from time import sleep, time

from DriveDatabase import DriveDatabase
from GPSController import GPSController
from Model.LCDController import LCDController
from OBDController import OBDController


def poll_obd(obdcontroller):
    """
    Takes OBD instance as argument, returns dict of instantaneous mpg and speed
    """
    speed = obdcontroller.get_pid_data('010D')
    maf = obdcontroller.get_pid_data('0110')

    try:
        # My calculation gives a constant of 7.100295, but the accepted value seems to be 7.107
        mpg = str(round((7.107 * speed) / maf, 2))
        return {'MPG': mpg, 'SPD': str(speed)}

    except Exception:
        raise Exception


def poll_gps(gps):
    """
    Gets current latitude, longitude, and course
    """
    # while session.fix.latitude == 0:  # will report '0' if we don't have a fix; if that's the case, just chug past it
    #     sleep(0.1)  # removing this because it could block main loop execution. Just strip bad vals in processing.
    return {'LAT': gps.fix.latitude, 'LON': gps.fix.longitude, 'TRA': str(gps.fix.track)}


def get_track(degrees):
    """
    Converts degree measurement to cardinal track
    """
    track = ''

    if 0 <= degrees < 39:
        track = 'N'
    elif 39 <= degrees < 84:
        track = 'NE'
    elif 84 <= degrees < 129:
        track = 'E'
    elif 129 <= degrees < 174:
        track = 'SE'
    elif 174 <= degrees < 219:
        track = 'S'
    elif 219 <= degrees < 264:
        track = 'SW'
    elif 264 <= degrees < 309:
        track = 'W'
    elif 309 <= degrees < 354:
        track = 'NW'
    elif 354 <= degrees:
        track = 'N'

    return track


def gen_timestamp():
    """
    Generates a unique (let's hope!), whole-number, unix-time timestamp.
    """
    return int(time() * 1e6)


def get_data(obd, gps):
    """
    Wrapper function to get all necessary data before db write. Takes OBDController and GPSController instances as
    arguments.
    """
    timestamp = gen_timestamp()
    gps_data = poll_gps(gps)
    obd_data = poll_obd(obd)

    return ({'TIMESTAMP': str(timestamp), 'MPG': str(obd_data['MPG']), 'SPD': str(obd_data['SPD']), 'LAT': str(gps_data['LAT']),
             'LON': str(gps_data['LON']), 'TRA': str(gps_data['TRA'])})
             # return strings as values so that we can join for DB commit


def main_loop():

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    logging.debug('Setting up handler')
    def handler(signum, stack):
        # TODO: TypeError: handler() takes no arguments (2 given)
        functions = [gps.stop(), obd.disconnect(), lcd.clear(),
                     lcd.print_message('Trip Average: {0}'.format(str(trip_avg))), sleep(5), lcd.clear()]
        # do neat server stuff here
        for function in functions:
            try:
                function
            except Exception as e:
                #todo:log here
                logging.debug(e.message)
        if lcd:
            lcd.print_message('Shutting Down...')
        logging.debug('Signal received ' + str(signum))
        sys.exit(0)

    signal.signal(signal.SIGUSR1, handler)

    logging.debug('Initializing LCD')
    lcd = LCDController()
    lcd.print_message('Initializing...')

    # init devices
    logging.debug('Initializing GPS')
    gps = GPSController()
    gps.start()

    lcd.clear()
    lcd.print_message('GPS initialized')

    logging.debug('Initializing OBD')
    obd = OBDController('/dev/ttyUSB0', DEBUG=True)
    obd.connect()

    lcd.clear()
    lcd.print_message('OBD initialized')

    logging.debug('Initializing DB')
    # connect to DB and create a trip-specific table
    db = DriveDatabase('/home/pi/databases/test_database.db')
    sleep(3)  # it can take the gps unit a few seconds to re-set the system time
    db.new_table()

    lcd.clear()
    lcd.print_message('DB initialized')

    # trip variables, used for calculating trip stats
    total_mpg = 0
    total_cycles = 0

    counter = 0
    while not gps.has_fix:
        logging.debug('No fix')
        logging.debug(gps.has_fix)
        logging.debug(gps.fix.mode)
        lcd.clear()
        lcd.print_message('No Satellite Fix')
        lcd.print_message('\n' + counter * '.')
        if counter == 16:
            counter = 0
        else:
            counter += 1
        sleep(.25)
    logging.debug('Fix obtained')
    while True:
        # get data, write to DB
        try:
            data = get_data(obd, gps)
            logging.debug(data)
            db.write_values(data)

        except Exception as e:
            lcd.clear()
            lcd.print_message(str(e.message))
            logging.debug((e.args, e.message))
            traceback.print_exc()
            sleep(5)
            continue

        # calculate 10 second and trip MPG averages
        total_mpg += float(data['MPG'])
        total_cycles += 1
        trip_avg = str(round(float(total_mpg)/total_cycles, 2))
        logging.debug('trip avg: ' + trip_avg)
        short_avg = str(round(float(db.query('SELECT avg(MPG) FROM {0} ORDER BY TIMESTAMP DESC LIMIT 10')[0]), 2))
        logging.debug('short avg: ' + short_avg)

        # create a properly-spaced string of averages to print to LCD
        top_pad = (7 - len(str(short_avg))) * ' '

        top_message = top_pad + str(short_avg) + ' | ' + str(trip_avg)

        # calculate minutes to consume one gallon at current speed and mpg
        try:
            minutes_per_gallon = str(round((float(data['SPD']) / 60) / (float(data['MPG'])), 2))

        except ZeroDivisionError:
            minutes_per_gallon = '0'

        # get track as cardinal direction
        degrees = float(data['TRA'])
        track = get_track(degrees)

        # create a message from track
        bottom_pad = (7 - len(track)) * ' '
        bottom_message = bottom_pad + track + ' | ' + minutes_per_gallon

        #create single message, print to LCD
        message = top_message + '\n' + bottom_message
        lcd.clear()
        lcd.print_message(message)

        sleep(1)


#todo: check for trouble codes on startup

if __name__ == '__main__':
    main_loop()