########################################################################################################################
# For information on speeding up responses, see                                                                        #
# http://www.obd2crazy.com/techatst.html                                                                               #
# and                                                                                                                  #
# http://stackoverflow.com/questions/21334147/send-multiple-obd-commands-together-and-get-response-simultaneously      #
# Responses are in format                                                                                              #
# 010D SPEED FORMAT '010D\r41 0D 00 \r\r'                                                                              #
# 0110 MAF FORMAT '0110\r41 10 01 7B \r\r'                                                                             #
########################################################################################################################

import serial
from DecodeFunctions import decode_obd_data


class NoOBDDataException(Exception):

    def __init__(self, command, response):
        self.command = command
        self.response = response


class OBDController():

    def __init__(self, path, DEBUG=False):
        self._baudrate = 38400
        self._path = path
        self._debug = DEBUG
        self._connection = None

    def connect(self):
        # todo: set locale? turn echo off?
        if self._debug:
            self._connection = True
            return True

        try:
            self._connection = serial.Serial(self._path, self._baudrate, timeout=1)
            return True

        except Exception as e:
            self._connection = None
            return False

    # def check_trouble(self):
    #     # this needs work
    #
    #     command = '03\r'
    #     self._connection.write(command)
    #     return self._connection.readline()

    def get_pid_data(self, pid):
        """
        Enter mode and hex PID (e.g. '010D' for current speed data)
        Returns response in decimal
        """

        pid = pid.replace(' ', '')  # Can't have spaces.

        if self._debug:
            return 10

        self._connection.write(pid + '1\r')
        # Adding the "1" after the command should force a wait for only one response from the CAN bus

        response = self._connection.readline().split(' ')
        # response.split is ['010D101\r41', '0D', '00', '10', '00', 'BD', '\r\r>']

        return response[2: -1]

    @property
    def is_connected(self):
        return self._connection

    @property
    def speed(self):
        pid = '010D'
        data = self.get_pid_data(pid)
        return decode_obd_data(pid, data)

    @property
    def maf(self):
        pid = '0110'
        data = self.get_pid_data('0110')
        return decode_obd_data(pid, data)

    def disconnect(self):
        """
        Closes connection
        """
        if self._debug:
            return "Disconnected"

        self._connection.close()
        return "Disconnected"
