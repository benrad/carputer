import signal
import sys
from Model.Carputer import Carputer
from Model.DriveDatabase import DriveDatabase
from Model.OBDController import OBDController
from Model.GPSController import GPSController
from Model.OLEDController import OLEDController


def signal_handler(signal, frame):
    carputer.stop()
    sys.exit(0)

carputer = Carputer(OBDController('/dev/ttyUSB0'),
                    GPSController(),
                    OLEDController(),
                    DriveDatabase('/home/pi/databases/drive_data.db'))

signal.signal(signal.SIGUSR1, signal_handler)
carputer.start()  # Confirmed that this script will not exit while carputer is running, even though run() returns

# I could handle some of the issues with shutdown by modifying the switch script to simply send the signal to carputer
# and then have carputer itself handle shutting down the machine
