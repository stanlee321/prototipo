import threading
import time


class SemaforoSimulado(object):
    """ 
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=1):

        # STATE FOR RED
        self.RED = 30
        self.YELLOW = 5
        self.GREEN = 25
        self.back = False
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        self.state = 'NAN'
        self.numericValue = -1
        self.counter = 0

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start()                                  # Start the execution

    def run(self):
        """ Method that runs forever """
        self.state = 'rojo'
        self.numericValue = 1
        #print(' Starting... RED RED RED ')
        if self.state == 'rojo':
            for number in range(self.RED):
                time.sleep(self.interval)
                self.counter = number

        # STATE FOR GREEN
        #print(' Starting...GREEN GREEN GREEN')
        self.state = 'verde'
        self.numericValue = 0
        if self.state == 'verde':
            for number in range(self.GREEN):
                time.sleep(self.interval)
                self.counter = number

        # STATE FOR YELLOW
        self.state = 'amarillo'
        self.numericValue = 2
        #print('Starting...YELLOW YELLOW YELLOW')
        if self.state =='amarillo':
            for number in range(self.YELLOW):
                time.sleep(self.interval)
                self.state = 'amarillo'
                self.counter = number
        
        # RESTARTING THE INITIAL CONDITIONS
        self.state = 'rojo'
        self.numericValue = 1


        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True                            # Daemonize thread
        self.thread.start() 
        #print('Doing something imporant in the background')

    def getCurrentValue(self):
        return self.numericValue,self.state

    def obtenerDebugSemaforo(self):
        """
        Devuelve la duracion del ultimo periodo del semaforo, y el porcentaje de encuentros exitosos de color
        """
        periodoFinal = (self.RED+self.YELLOW+self.GREEN)*self.interval
        return periodoFinal, 'SemaforoSimulado'


"""
example = SemaforoSimulado()

while True:
    print(example.counter,':',example.numericValue)
    time.sleep(1)

"""