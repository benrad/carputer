from __future__ import absolute_import
from Queue import Queue
from threading import Event
from time import sleep
from context import Model


def test_load_animation(oledcontroller):
    message_queue = Queue(1)
    cancellation_token = Event()

    message_queue.put('Event 1')
    t = oledcontroller.run_load_animation(message_queue, cancellation_token)
    sleep(2)
    message_queue.put('Event 2')
    sleep(3)
    message_queue.put('Event 3')
    sleep(1)
    message_queue.put('Event 4')
    sleep(1)
    cancellation_token.set()
    t.join()

if __name__ == '__main__':
    oc = Model.OLEDController()
    test_load_animation(oc)