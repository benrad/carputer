__author__ = 'benradosevich'

import sqlite3 as lite


class DriveDatabase(object):

    def __init__(self, path):
        self.__path = path
        self.open = False
        self.__current_table = None

    @property
    def path(self):
        """
        Filesystem path to database
        """
        return self.__path

    @path.setter
    def path(self, p):
        self.__path = p

    @property
    def current_table(self):
        return self.__current_table

    def new_table(self, timestamp):
        """
        Creates a unique table in the db for the current drive. Table name is in format D[unique timestamp]. Need first
        character to be alpha for sqlite3.
        """
        name = 'D' + str(timestamp)
        self.__current_table = name
        con = lite.connect(self.path)

        with con:
            cur = con.cursor()
            cur.execute('CREATE TABLE {0}(TIMESTAMP INT PRIMARY KEY, MPG REAL, '
                        'SPD REAL, LAT REAL, LON REAL, TRA VARCHAR)'.format(name))

    def write_values(self, data):
        """
        Takes absolute path of db, table name, and dict with column:value format, writes selected data to db.
        """
        # TODO: maybe enclose strings in quotes to prevent "no such column NaN" when gps fix lost?
        keys = ['TIMESTAMP', 'MPG', 'SPD', 'LAT', 'LON', 'TRA']
        values = [data[k] for k in keys]
        columns = ', '.join(keys)
        values = ', '.join(values)
        con = lite.connect(self.path)

        with con:
            cur = con.cursor()
            cur.execute('INSERT INTO {0}({1}) VALUES({2})'.format(self.__current_table, columns, values))

    def query(self, q):
        """
        @param q: sqlite query with {0} for table name
        """
        con = lite.connect(self.path)

        with con:
            cur = con.cursor()
            cur.execute(q.format(self.__current_table))
            response = cur.fetchone()

        return response
