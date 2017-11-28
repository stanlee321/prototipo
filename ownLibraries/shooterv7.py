#!/usr/bin/env python
# semaforo como clase

import os
import cv2
import time
import datetime
import threading
import multiprocessing
import picamera
import time
#from io import BytesIO
#from skimage.io import imsave

class Shooter(picamera):
	""" General PICAMERA DRIVER Prototipe
	"""
	directorioDeReporte = os.getenv('HOME')+'/casosReportados'
	date_hour_string = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S:%f')

	def __init__(self, video_source = 0, width = 3280, height = 2464, cutPoly=([0,0],[3280,2464]), capturas = 3):
	#def __init__(self, video_source = 0, width = 680, height = 420, cutPoly=([0,0],[200,200]), saveDir='./test/'):
		#self.miReporte = MiReporte(levelLogging=10)
		#self.miReporte.info( 'Starting the  PiCam')
		#print('Cree objeto de forma exitosa')
		picamera.__init__(self)

		self.eyesOpen = False
		# Initial aparemeters
		self.video_source = video_source
		self.width = width		# Integer Like
		self.height = height	# Integer Like
		self.maxCapturas = capturas
		# FOR ROI
		self.cutPoly = cutPoly 	# ARRAY like (primerPunto, segundoPunto)
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]				# Array like [p0,p1]

		# Dir where to save images
		
		self.directorioDeGuardadoGeneral = self.directorioDeReporte
		self.fechaInfraccion = str
		self.saveDir = str
		self.frame_number = 0

		# PICMEARA INIT
		self.camera= picamera.PiCamera()
		#self.camera.resolution = (3240,2464)
		self.camera.resolution = (self.width,self.height)
		self.camera.framerate = 1
		self.camera.start_preview()
		print('EXITOSAMENTE CREE LA CLASE SHOOTER')


	def establecerRegionInteres(self,cutPoly):
		self.cutPoly = cutPoly
		self.primerPunto = self.cutPoly[0] 				# Array like [p0,p1]
		self.segundoPunto = self.cutPoly[1]

	def encenderCamaraEnSubDirectorio(self, folder, fecha):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.fechaInfraccion = fecha
		self.saveDir = self.directorioDeGuardadoGeneral +"/" + folder
		if not os.path.exists(self.saveDir):
			os.makedirs(self.saveDir) 
		self.eyesOpen = True
		#self.start()
		print('Encendi Camara de Forma Exitosa en ' + self.saveDir)

	def encenderCamara(self):
		#self.miReporte.moverRegistroACarpeta(fecha)
		self.eyesOpen = True

	def apagarCamara(self):
		self.eyesOpen = False
		print('Realizada las capturas, cerrando ojos...')
	

	def writter(self):
		#while not input_queue.empty:
		self.frame_number = 0
		while self.frame_number < self.maxCapturas:
			#print('GUARDADO en: '+ self.saveDir+'/{}-{}.jpg'.format(self.fechaInfraccion[:-3], self.frame_number))
			#yield "image%02d.jpg" % frame
			
			#yield self.saveDir+"/{}-{}.jpg".format(self.fechaInfraccion, self.frame_number)
			yield "./imagen_{}.jpg".format(self.frame_number)
			self.frame_number += 1

	def start(self):
		start = time.time()
		self.camera.capture_sequence(self.writter(), use_video_port=True)
		finish = time.time()
		self.eyesOpen = False
		print("Captured %d frames at %.2ffps" % (self.maxCapturas,self.maxCapturas / (finish - start)))



import multiprocessing
import sys
import re

class ProcessWorker(multiprocessing.Process):
    """
    This class runs as a separate process to execute worker's commands in parallel
    Once launched, it remains running, monitoring the task queue, until "None" is sent
    """

    def __init__(self, task_q, result_q):
        multiprocessing.Process.__init__(self)
        self.task_q = task_q
        self.result_q = result_q
        return

    def run(self):
        """
        Overloaded function provided by multiprocessing.Process.  Called upon start() signal
        """
        proc_name = self.name
        print '%s: Launched' % (proc_name)
        while True:
            next_task_list = self.task_q.get()
            if next_task is None:
                # Poison pill means shutdown
                print '%s: Exiting' % (proc_name)
                self.task_q.task_done()
                break
            next_task = next_task_list[0]
            print '%s: %s' % (proc_name, next_task)
            args = next_task_list[1]
            kwargs = next_task_list[2]
            answer = next_task(*args, **kwargs)
            self.task_q.task_done()
            self.result_q.put(answer)
        return
# End of ProcessWorker class

class Worker(object):
    """
    Launches a child process to run commands from derived classes in separate processes,
    which sit and listen for something to do
    This base class is called by each derived worker
    """
    def __init__(self, config, index=None):
        self.config = config
        self.index = index

        # Launce the ProcessWorker for anything that has an index value
        if self.index is not None:
            self.task_q = multiprocessing.JoinableQueue()
            self.result_q = multiprocessing.Queue()

            self.process_worker = ProcessWorker(self.task_q, self.result_q)
            self.process_worker.start()
            print "Got here"
            # Process should be running and listening for functions to execute
        return

    def enqueue_process(target):  # No self, since it is a decorator
        """
        Used to place an command target from this class object into the task_q
        NOTE: Any function decorated with this must use fetch_results() to get the
        target task's result value
        """
        def wrapper(self, *args, **kwargs):
            self.task_q.put([target, args, kwargs]) # FAIL: target is a class instance method and can't be pickled!
        return wrapper

    def fetch_results(self):
        """
        After all processes have been spawned by multiple modules, this command
        is called on each one to retreive the results of the call.
        This blocks until the execution of the item in the queue is complete
        """
        self.task_q.join()                          # Wait for it to to finish
        return self.result_q.get()                  # Return the result

    @enqueue_process
    def run_long_command(self, command):
        print "I am running number % as process "%number, self.name

        # In here, I will launch a subprocess to run a  long-running system command
        # p = Popen(command), etc
        # p.wait(), etc
        return 

    def close(self):
        self.task_q.put(None)
        self.task_q.join()


if __name__ == '__main__':
	#DEMO DEMO DEMO 

	shoot = Shooter()
	counter = 0
	eyes = False

	while True:
		counter +=1 
		if counter == 10:
			eyes = not eyes
			shoot(state = eyes)
			counter = 0
			#main()
		print(counter)
		time.sleep(1)