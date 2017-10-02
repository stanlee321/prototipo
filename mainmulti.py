#!/usr/bin/python3
# -*- coding: utf-8 -*-

# import the necessary packages
#from __future__ import print_function
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
from multiprocessing import Process, Queue, Pool
import threading
import base64
import datetime
import pickle
import os
import some_math
import bgsubcnt 


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-d", "--display", type=int, default=1,
	help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

print("[INFO] sampling THREADED frames from webcam...")


ENCODING = 'utf-8'


# CREATE DB into the memory
#conn = sqlite3.connect('file::memory:?cache=shared'+'__1')
conn = sqlite3.connect(':memory:')
#conn = sqlite3.connect('data.db')
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
        print('HELLO FROM THE PARENNNNNNNNT')
        self.saver = SaveData()



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
		#pool1 = Pool(2,self.fun1.interfase_para_bg, (self.bg_object, self.frame_real,self.frame_resized, self.frame_number, self.state))

		
		p2 = Process(target=self.fun2.insert_data, args=(self.frame_resized, self.frame_number, self.state))

		p2.start()
		#pool2 = Pool(2,self.fun2.insert_data, (self.frame_resized, self.frame_number, self.state))



		#p1.join()
		#p2.join()



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

		if state == 'ROJO' or 'rojo':
			#print('form function 1...:', self.saver.ask_for_time)
			#print('from F1', self.saver.create_folder_and_save())
			#print(out)
			#return out
			x1 = 3000
			x2 = 3200

			y1 = 2200
			y2 = 2400
			frame_real = frame_real[y2:y1, x1:x2] 

			#frame_real = cv2.resize(frame_real, (2048, 1536))
			self.saver.create_folder_and_save(frame_number, frame_real,'FUN1')

			print('hello from red')
			print('HELLO FROM  FUNCTION 1', frame_number)
		elif state == 'AMARILLO'  or 'amarillo':

			print('HELLO FROM  FUNCTION 1', frame_number)

		elif state == 'VERDE' or 'verde':

			print('HELLO FROM  FUNCTION 1', frame_number)

		elif state == 'No hay semaforo':

			print('HELLO FROM  FUNCTION 1', frame_number)


class Function_2(PipelineProcessor):

	def __init__(self):
		super(Function_2, self).__init__()
		
	# function 2 to be injected to the parallel process
	def insert_data(self, frame_resized, frame_number, state):

		if state == 'ROJO' or 'rojo':
			#self.saver.create_folder_and_save(frame_number, frame_resized, 'FUN2')
						
			print('HELLO FROM  FUNCTION 2', frame_number)
		elif state == 'AMARILLO' or 'amarillo':

			
			print('HELLO FROM  FUNCTION 2', frame_number)

		elif state == 'VERDE' or 'rojo':
			
			
			print('HELLO FROM  FUNCTION 2', frame_number)


		elif state == 'No hay semaforo':

			
			print('HELLO FROM  FUNCTION 2', frame_number)
	
	


class SaveData(object):

	ask_for_time = datetime.datetime.now().strftime('%Y-%m-%d::%H:%M:%S')

	def __init__(self):
		self.save_folder = None
		self.save_file = None
	


	def folder_and_file(self, folderName, fileName):

		self.save_folder = folderName
		self.save_file = fileName

		return self.save_folder, self.save_file

	@classmethod
	def update_time(cls):
		cls.ask_for_time = datetime.datetime.now().strftime('%Y-%m-%d::%H:%M:%S')


	@classmethod
	def update_folders_and_files(cls):
		cls.update_time()

		folder_and_file_name = cls.ask_for_time.split('::')
		for_folder, for_file = folder_and_file_name[0], folder_and_file_name [1]

		path_for_folder = './data' + '/' + '{}'.format(for_folder)
		path_for_file = path_for_folder + '/' + '{}'.format(for_file)

		return path_for_folder, path_for_file
	@staticmethod
	def create_folder_and_save(frame_number, frame, tag):

		#folder_name, file_name = Saveto.folder_and_file(Saveto.get_time('forFolder'), './data/{}/{}_frame_{}.jpg'.format(Function_2.get_time('forFolder'),
		#											Function_2.get_time('forFile'), frame_number)  )
		

		path_to_folder, path_to_file = SaveData.update_folders_and_files()
		
		try:
			os.makedirs(path_to_folder)
		except Exception as e:
			print(e)
		if os.path.isdir(path_to_folder) == os.path.isdir(path_to_file[0:-9]):
			#print('Folder already exist or ..', e)
			print('Files are beeing created in .... ', path_to_folder)
			cv2.imwrite(path_to_file+'_{}_{}.jpg'.format(frame_number, tag), frame)
		#print(SaveData.update_folders_and_files())

		
		#return path_to_folder, path_to_file[0:-9]
		#return 
	@staticmethod
	def create_db_and_save(frame_number, frame, tag):

		retval, buff = cv2.imencode('.jpg', frame_resized)

		jpg_as_text = base64.b64encode(buff)


		image_64_encode = base64.encodestring(jpg_as_text)
		base64_string = image_64_encode.decode(ENCODING)

		base64_string_resized = base64_string
		with conn:
			c.execute("INSERT INTO infractions VALUES (:frame_resized, :frame_number)", {'frame_resized': base64_string_resized, 'frame_number': frame_number})


class CreateBG(object):
	def __init__(self):
		# Define the parameters needed for motion detection
		self.k = 31
		self.alpha = 0.02 # Define weighting coefficient for running average
		self.motion_thresh = 35 # Threshold for what difference in pixels  
		self.running_avg = None # Initialize variable for running average
		self.min_contour_width=15 
		self.min_contour_height=15
	#@property
	def visual(self, current_frame):

		gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
		t1 = time.time()
		smooth_frame = cv2.GaussianBlur(gray_frame, (self.k, self.k), 0)

		# If this is the first frame, making running avg current frame
		if self.running_avg is None:
			self.running_avg = np.float32(smooth_frame) 

		# Find absolute difference between the current smoothed frame and the running average
		diff = cv2.absdiff(np.float32(smooth_frame), np.float32(self.running_avg))
		t2 = time.time()

		print('THE DIFF TOOOOK', t2-t1)


		# Then add current frame to running average after
		cv2.accumulateWeighted(np.float32(smooth_frame), self.running_avg, self.alpha)

		# For all pixels with a difference > thresh, turn pixel to 255, otherwise 0
		_, subtracted = cv2.threshold(diff, self.motion_thresh, 1, cv2.THRESH_BINARY)

		matches = []
		
		subtracted = np.array(subtracted * 255, dtype = np.uint8)

		fg_mask = subtracted	

		im2, contours, hierarchy = cv2.findContours(subtracted, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

		#cv2.imshow('im2', im2)

		#print( len(contours))
		
		for (i, contour) in enumerate(contours):
		    (x, y, w, h) = cv2.boundingRect(contour)
		    contour_valid = (w >= self.min_contour_width) and (h >= self.min_contour_height)
		    if not contour_valid:
		        continue

		    centroid = some_math.get_centroid(x, y, w, h)

		    matches.append(((x, y, w, h), centroid))


		#cv2.imshow('Thresholded difference', subtracted)

		return matches
		#cv2.imshow('Actual image', current_frame)
		#cv2.imshow('Gray-scale', gray_frame)
		#cv2.imshow('Smooth', smooth_frame)
		#cv2.imshow('Difference', diff)

	#cv2.destroyAllWindows()


class CreateBG2():
	def __init__(self):
		# Define the parameters needed for motion detection

		self.fgbg = bgsubcnt.createBackgroundSubtractor(3, False, 3*60)
		self.k = 31
		self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
		self.min_contour_width=15 
		self.min_contour_height=15
		#self.kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3),(0,0))

		self.input_q = Queue(maxsize=5)
		self.output_q = Queue(maxsize=5)

		self.process = Process(target= self.worker, args=(self.input_q, self.output_q))
		self.process.daemon = True

		pool = Pool(2,self.worker, (self.input_q, self.output_q))
		#self.process.start()

		#thread = threading.Thread(target=self.worker, args=(self.input_q, self.output_q))
		#thread.daemon = True                            # Daemonize thread
		#thread.start() 


	def visual(self, current_frame):

		self.input_q.put(current_frame)

		matches = self.output_q.get()
		
		return matches

	def worker(self, input_q, output_q):

		while True:
			#print('WORKDERRR')
			matches = []

			gray = cv2.cvtColor(input_q.get(), cv2.COLOR_BGR2GRAY)

			smooth_frame = cv2.GaussianBlur(gray, (self.k,self.k), 1.5)
			#smooth_frame = cv2.bilateralFilter(gray,4,75,75)
			#smooth_frame =cv2.bilateralFilter(smooth_frame,15,75,75)


			self.fgmask = self.fgbg.apply(smooth_frame, self.kernel, 0.1)

			im2, contours, hierarchy = cv2.findContours(self.fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
			for (i, contour) in enumerate(contours):
			    (x, y, w, h) = cv2.boundingRect(contour)
			    contour_valid = (w >= self.min_contour_width) and (h >= self.min_contour_height)
			    if not contour_valid:
			        continue
			    centroid = some_math.get_centroid(x, y, w, h)

			    matches.append(((x, y, w, h), centroid))

			#return matches
			output_q.put(matches)




# Auxilar function to be the interfase for output resized frame and normal frame
def genero_frame(frame, size = (320,240)):

	real_frame = frame
	out = cv2.resize(frame, size)

	return  out, real_frame



def dump_to_disk(con, filename):
	"""
	Dumps the tables of an in-memory database into a file-based SQLite database.

	@param con:         Connection to in-memory database.
	@param filename:    Name of the file to write to.
	"""
	
	cur = c3.cursor()
	with c3:
		c3.execute("ATTACH DATABASE '{}' AS inmem".format(filename))

	print('Hi, saving...db')

def myTimedecorator(function):
	
	def wrapper(*args, **kwargs):
		t1 = time.time()
		f = function(*args,**kwargs)
		t2 = time.time()
		print('TIME TOOK:::', t2-t1)
	return wrapper

if __name__ == '__main__':

	data = np.load('./installationFiles/heroes.npy')
	print(data)
	semaforo = CreateSemaforo(periodoSemaforo = 10)
	poligono  = data[0]
	src = ['./installationFiles/mySquare.mp4', 0]
	#vs = WebcamVideoStream(src=src[0], height = 640, width = 480).start()
	#vs = WebcamVideoStream(src=src[1], height = 2048, width = 1536, queueSize=8).start()
	vs = WebcamVideoStream(src=src[1], height = 2048, width = 1536).start()

	#vs = WebcamVideoStream(src=src[1], height = 2592, width = 1944, queueSize=128).start()
	#vs = WebcamVideoStream(src=src[1], height = 3266, width = 2450, queueSize=128).start()
	time.sleep(1.0)

	fps = FPS().start() 

	ON = True
	# loop over some frames...this time using the threaded stream

	log = logging.getLogger("main")

	#bg_instance = cv2.createBackgroundSubtractorKNN(history=500,dist2Threshold=1 ,detectShadows=True)
	bg_instance = cv2.createBackgroundSubtractorMOG2(history=500, detectShadows=True)

	bg = BackgroundSub(bg = bg_instance)
	#bg = None
	frame_number = -1
	_frame_number = -1
	function1 = Function_1() # Saver to db
	function2 = Function_2() # BG substractor

	new_bg = CreateBG()
	new_2_bg = CreateBG2( )

	pipeline = PipelineRunner(pipeline=[MultiJobs( fun1 = function1, fun2 = function2)], log_level=logging.DEBUG)


	while ON:
		# grab the frame from the threaded video stream and resize it
		# to have a maximum width of 400 pixels
		
		t1 = time.time()

		frame = vs.read()


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

		t2 = time.time()



		# frame number that will be passed to pipline
		# this needed to make video from cutted frames
		frame_number += 1
		matches = new_2_bg.visual(frame_resized)

		pipeline.load_data({
	        'frame_resized': frame_resized,
	        'frame_real': frame_real,
	        'bg_object': bg,
	   	    'state': colorLiteral,
	        'frame_number': frame_number,})
		pipeline.run()


		#print('MATCHES', matches)
		"""
		for (i, match) in enumerate(matches):
			contour, centroid = match[0], match[1]
			print(contour, centroid)
			#if self.check_exit(centroid, exit_masks):
			#    continue
			print(match[0])

			x, y, w, h = contour
			#the_box.append([contour])
			print('THE BOXXXXXXXXXXXXXXXXXXXX', contour)
			cv2.rectangle(frame_resized, (x, y), (x + w - 1, y + h - 1),(0,0,255), 1)
			cv2.circle(frame_resized, centroid, 2, (0,255,0), -1)
		#cv2.imshow('boxes', frame_resized)
		"""

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break


		if _frame_number == 400:
			break
		#print('[INFO] elapsed time: {:.2f}'.format(time.time() - t))

		# update the FPS counter
		
		#print(senalColor, colorLiteral, flancoSemaforo)
	#dump_to_disk(conn, 'file::memory:?cache=shared')
	#with open('DATAPICKE.pickle', 'wb') as handle:
	#			pickle.dump(datadict, handle, protocol=pickle.HIGHEST_PROTOCOL)
	#conn.close()
		print('THE TIME THAT TAKE TO RUN THIS', t2-t1)
		fps.update()

	# stop the timer and display FPS information
	fps.stop()
	print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	 
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()


"""
def mydecorator(function):

	def wrapper(*args, **kwargs):
		print('hello from here')
		return function(*args, **kwargs)
	return wrapper
"""
