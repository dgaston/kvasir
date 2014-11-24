from threading import Thread
from kvasir import app

#To do, change this to the multiprocessing module and Pool instead of Threads

def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target = f, args = args, kwargs = kwargs)
        thr.start()
    return wrapper

class with_request_context(object):
    def __init__(self, f):
        self.f = f
        self.app = app
        self.request = '/'
        self.__name__ = f.__name__ + 'with_request_context'

    def __call__(self, *args):
        with self.app.test_request_context(self.request):
            return self.f(*args)