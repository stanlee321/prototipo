import multiprocessing
import time


'''
class Timer(multiprocessing.Process):
    """A simple timer class"""
    

    def __init__(self):
        super(Timer, self).__init__()
        self.init_time = time.time()


    @property
    def init_time(self):
        return self.__init_time
    @init_time.setter
    def init_time(self,t):
        self.__init_time = t

    def stop(self, message="Total: "):
        """Stops the timer.  Returns the time elapsed"""
        self.stop_l = time.time()
        return  message + str(self.stop_l - self.__init_time)

    def elapsed(self, message="Elapsed: "):
        """Time elapsed since start was called"""
        return message + str(time.time() - self.__init_time)
    
    def split(self, message="Split started at: "):
        """Start a split timer"""
        self.split_start = time.time()
        return message + str(self.split_start)
    
    def unsplit(self, message="Unsplit: "):
        """Stops a split. Returns the time elapsed since split was called"""

        return message + str(time.time() - self.split_start)

    def run(self):
        """Starts the timer"""
        self.__init_time = time.time()
        return self.__init_time

'''


class Timer():
    """A simple timer class"""
    
    def __init__(self, periodos=[]):
        self.periodos = periodos
        self.init_time = None#time.time()
    @property
    def init_time(self):
        return self.__init_time
    @init_time.setter
    def init_time(self,t):
        self.__init_time = t

    def stop(self, message="Total: "):
        """Stops the timer.  Returns the time elapsed"""
        self.stop_l = time.time()
        self.__init_time = None
        #print(message + str(self.stop_l - self.__init_time))

    def elapsed(self, message="Elapsed: "):
        """Time elapsed since start was called"""
        return message + str(time.time() - self.__init_time)


    def start(self):
        """Starts the timer"""
        self.__init_time = time.time()
        return self.__init_time

    def __call__(self):
        self.init_time = time.time()


if __name__ == '__main__':

    t = Timer()
    t.start()


    counter = 0
    while True:
        time.sleep(1)
        print(t.elapsed())
        counter +=1
        print('COUNTER', counter)
        if float(t.elapsed().split(': ')[-1]) > 3.0:
            print(t.stop())
            t.start()
            #break

