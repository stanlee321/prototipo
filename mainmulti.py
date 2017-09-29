# import the necessary packages
from __future__ import print_function
from ownLibraries.utils import WebcamVideoStream
from ownLibraries.utils import FPS
from ownLibraries.semaforo import CreateSemaforo
import logging
import imutils
import cv2
import argparse
import time
import numpy as np
from bg import BackgroundSub
import logging
import sqlite3
from multiprocessing import Process
import threading
import base64



# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-d", "--display", type=int, default=1,
	help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

print("[INFO] sampling THREADED frames from webcam...")


ENCODING = 'utf-8'


# CREATE DB into the memory
conn = sqlite3.connect(':memory:')

#conn = sqlite3.connect('infractions.db')
c = conn.cursor()

c.execute("""CREATE TABLE infractions (
            frame_resized text,
            frame_number integer
            )""")





def mydecorator(function):

	def wrapper(*args, **kwargs):
		print('hello from here')
		return function(*args, **kwargs)
	return wrapper




class PipelineRunner(object):

	def __init__(self, pipeline, log_level=logging.DEBUG):

		self.pipeline = pipeline or []
		self.context = {}

		#thread = threading.Thread(target=self.run, args=())
		#thread.daemon = True                            # Daemonize thread
		#thread.start()                                  # Start the execution



	def load_data(self, data):

		self.context = data

	#@load_data.setter
	#def load_data(self):
	#	self.bg_object = self.context['bg_object']
	#	self.frame_real = self.context['frame_real']
	#	self.frame_resized = self.context['frame_resized']
	#	self.frame_number = self.context['frame_number']
	#	self.state = self.context['state']

	#@load_data.deleter
	#def load_data(self):
	#	self.bg_object = None
	#	self.frame_real = None
	#	self.frame_resized = None
	#	self.frame_number = None
	#	self.state = None

	def run(self):
		# Runing again the run() method.
		for p in self.pipeline:
			self.context = p(self.context)
		#thread = threading.Thread(target=self.run, args=())
		#thread.daemon = True                            # Daemonize thread
		#thread.start() 

class PipelineProcessor(object):
    '''
        Base class for processors.
    '''
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.contour = None


class MultiJobs(PipelineProcessor):

	def __init__(self, fun1, fun2 ):
		super(MultiJobs, self).__init__()


		# For functions
		self.bg_object = None
		self.frame_real = None
		self.frame_resized = None
		self.frame_number = None
		self.state = None

		self.fun1 = fun1
		self.fun2 = fun2


	def runInParallel(self):


		p1 = Process(target=self.fun1.interfase_para_bg, args=(self.bg_object, self.frame_real,
					 						self.frame_resized, self.frame_number, self.state))
		p1.start()
		
		p2 = Process(target=self.fun2.insert_data, args=(self.frame_resized, self.frame_number, self.state))
		p2.start()


		p1.join()
		p2.join()



	def __call__(self, context):

		self.bg_object = context['bg_object']
		self.frame_real = context['frame_real']
		self.frame_resized = context['frame_resized']
		self.frame_number = context['frame_number']
		self.state = context['state']

		self.runInParallel()
		#cv2.imshow('resized', cv2.resize(self.frame_resized,(self.frame_resized.shape[1]*2, self.frame_resized.shape[0]*2)))

		return context


class Function_1(PipelineProcessor):
	def __init__(self):
		super(Function_1, self).__init__()

	# function 1 to be injected to the parallel process
	def interfase_para_bg(self, bg_object, frame_real, frame_resized, frame_number, state):
		if state == 'ROJO':
			#out = bg_object.injector(frame_real = frame_real, frame_resized = frame_resized, frame_number = frame_number)
			#return out
			
			print('HELLO FROM  FUNCTION 1', frame_number)
		elif state == 'AMARILLO':

			print('HELLO FROM  FUNCTION 1', frame_number)

		elif state == 'VERDE':

			print('HELLO FROM  FUNCTION 1', frame_number)

		elif state == 'No hay semaforo':

			print('HELLO FROM  FUNCTION 1', frame_number)



class Function_2(PipelineProcessor):

	def __init__(self):
		super(Function_2, self).__init__()

	# function 2 to be injected to the parallel process
	def insert_data(self, frame_resized, frame_number, state):

		retval, buff = cv2.imencode('.jpg', frame_resized)

		jpg_as_text = base64.b64encode(buff)


		image_64_encode = base64.encodestring(jpg_as_text)
		base64_string = image_64_encode.decode(ENCODING)

		base64_string_resized = base64_string

		if state == 'ROJO':
			with conn:
				c.execute("INSERT INTO infractions VALUES (:frame_resized, :frame_number)", {'frame_resized': base64_string_resized, 'frame_number': frame_number})
			
			print('HELLO FROM  FUNCTION 2', frame_number)
		elif state == 'AMARILLO':

			
			print('HELLO FROM  FUNCTION 2', frame_number)

		elif state == 'VERDE':

			
			print('HELLO FROM  FUNCTION 2', frame_number)


		elif state == 'No hay semaforo':

			
			print('HELLO FROM  FUNCTION 2', frame_number)



# Auxilar function to be the interfase for output resized frame and normal frame
def genero_frame(frame, size = (320,240)):

	real_frame = frame.copy()
	out = cv2.resize(frame, size)

	return  out, real_frame



# parallel process to be worked
def runInParallel(*fns):
	"""
		Function to run in parallel two or more functions *fns
	"""
	proc = []
	for fn in fns:
		p = Process(target=fn)
		p.start()
		proc.append(p)
	for p in proc:
		p.join()


if __name__ == '__main__':

	data = np.load('./installationFiles/heroes.npy')
	print(data)
	semaforo = CreateSemaforo(periodoSemaforo = 0)
	poligono  = data[0]
	src = ['./installationFiles/heroes.mp4', 0]
	vs = WebcamVideoStream(src=src[0], height = 640, width = 480).start()
	fps = FPS().start() 

	ON = True
	# loop over some frames...this time using the threaded stream

	log = logging.getLogger("main")

	bg_instance = cv2.createBackgroundSubtractorMOG2(history=500, detectShadows=True)
	bg = BackgroundSub(bg = bg_instance)

	frame_number = -1
	_frame_number = -1

	function1 = Function_1() # Saver to db
	function2 = Function_2() # BG substractor


	pipeline = PipelineRunner(pipeline=[MultiJobs( fun1 = function1, fun2 = function2)], log_level=logging.DEBUG)


	while ON:
		# grab the frame from the threaded video stream and resize it
		# to have a maximum width of 400 pixels
		frame = vs.read()

		t = time.time()

		if not frame.any():
			log.error("Frame capture failed, stopping...")
			break

		frame_resized, frame_real = genero_frame(frame)

		# Get signals from the semaforo
		senalColor, colorLiteral, flancoSemaforo  = semaforo.obtenerColorEnSemaforo(poligono = poligono, img = frame_real)
		


		# fake frame for debugs
		_frame_number += 1

		# skip every 2nd frame to speed up processing
		if _frame_number % 2 != 0:
			continue

		# frame number that will be passed to pipline
		# this needed to make video from cutted frames
		frame_number += 1	
		pipeline.load_data({
	        'frame_resized': frame_resized,
	        'frame_real': frame_number,
	        'bg_object': bg,
	        'state': colorLiteral,
	        'frame_number': frame_number,})

		pipeline.run()

		#cv2.imshow('resized', cv2.resize(frame_resized,(frame_resized.shape[1]*2,frame_resized.shape[0]*2)))
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break


		if _frame_number == 400:
			break
		#print('[INFO] elapsed time: {:.2f}'.format(time.time() - t))

		# update the FPS counter
		
		fps.update()
	conn.close()

	# stop the timer and display FPS information
	fps.stop()
	print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	 
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()

