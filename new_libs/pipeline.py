import cv2
import numpy as np
import os

from multiprocessing import Process

import base64
import logging
import datetime

import bgsubcnt
from multiprocessing import Process, Queue, Pool
from new_libs.math_and_utils import get_centroid
from new_libs.math_and_utils import distance



class PipelineRunner(object):

	"""
	Pipeline that take frame_array and frame_integer from the exterior and 
	make some magic with this this stuffs, parallel process like save to this and bg sub

	"""

	def __init__(self, pipeline, log_level=logging.DEBUG):

		self.pipeline = pipeline or []
		self.context = {}

	def load_data(self, data):

		self.context = data


	def run(self):
		# Runing again the run() method.
		for p in self.pipeline:
			self.context = p(self.context)

class PipelineProcessor(object):
    '''
        Base class for processors.
    '''
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        print('HELLO FROM THE PARENNNNNNNNT')



class CreateBGCNT(PipelineProcessor):

	"""
	CLASS used to create BGCNT for purposes of extract the rectangle where the 
	car is in the screen, inputs: cls.visual(frame), outputs: list((rectanglex, rectangley)) positions.
	"""
	def __init__(self):
		# Define the parameters needed for motion detection

		self.fgbg = bgsubcnt.createBackgroundSubtractor(3, False, 3*60)
		self.k = 31
		self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
		self.min_contour_width=30
		self.min_contour_height=30

		self.input_q = Queue(maxsize=5)
		self.output_q = Queue(maxsize=5)

		self.process = Process(target= self.worker, args=(self.input_q, self.output_q))
		self.process.daemon = True

		pool = Pool(2,self.worker, (self.input_q, self.output_q))

	def worker(self, input_q, output_q):
		"""
		This class is used for multiprocessing the blop detector 
		, using this we increase the FPS
		Inputs:

		input_queue, numpy array like image frame

		Outputs:

		outputs_queue, 
		"""

		while True:

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
			    centroid = get_centroid(x, y, w, h)

			    matches.append(((x, y, w, h), centroid))
			output_q.put(matches)


	def __call__(self, context):

		self.input_q.put(context['frame_resized'])

		matches = self.output_q.get()
		
		context['matches'] = matches
		#return context['matches'], context['frame_resized'], context['frame_number'], context['frame_real']
		return context


class Filtering(PipelineProcessor):

	def __init__(self):

		self.counter = -1
		self.HR_IMAGE = None
		self.frame_number = None
		self.matches = None

		#self.process = Process(target= self.cutHighResImage, args=(self.HR_IMAGE, self.frame_number, self.matches))
		#self.process.daemon = True

		#pool = Pool(2, self.cutHighResImage,(,) )

	def cutHighResImage(self, HR_IMAGE, FRAME_NUMBER, MATCHES):

		for (i, match) in enumerate(MATCHES):
			contour, centroid = match[0], match[1]

			x, y, w, h = contour

			x1, y1 = x, y 
			x2, y2 = x + w - 1, y + h - 1

			nx1, ny1 = 2*x1, 2*y1
			nx2, ny2 = 2*x2, 2*y2


			out = HR_IMAGE[ny1:ny2, nx1:nx2]
			#cv2.imwrite('./data/tests/save_{}_{}.jpg'.format(FRAME_NUMBER, self.counter), out)
			#self.counter +=1
			return out

	def __call__(self,context):
		print('cleaning...')

		date =  datetime.datetime.now().strftime('%Y-%m-%d::%H:%M:%S')


		cutted = self.cutHighResImage(context['frame_real'],context['frame_number'],context['matches'])

		data = [context['frame_number'], cutted, context['frame_resized'], date]

		return data
		#self.cutHighResImage(context['frame_real'],context['frame_number'],context['matches'])


class FIFO(PipelineProcessor):
	def __init__(self, queue_size = 3):
		super(FIFO, self).__init__()

		self.input_q = Queue(maxsize = queue_size)

	def __call__(self, context):

		self.input_q.put(context)

		return self.input_q.get()



class Save_to_Disk(PipelineProcessor):
	ask_for_time = datetime.datetime.now().strftime('%Y-%m-%d::%H:%M:%S')
	def __init__(self):
		pass
	@classmethod
	def update_folders_and_files(cls):
		cls.update_time()

		folder_and_file_name = cls.ask_for_time.split('::')
		for_folder, for_file = folder_and_file_name[0], folder_and_file_name [1]

		path_for_folder = './data' + '/' + '{}'.format(for_folder)
		path_for_file = path_for_folder + '/' + '{}'.format(for_file)

		return path_for_folder, path_for_file
	
	def create_folder_and_save(self, frame_number, matches, frame, tag):

		#folder_name, file_name = Saveto.folder_and_file(Saveto.get_time('forFolder'), './data/{}/{}_frame_{}.jpg'.format(Function_2.get_time('forFolder'),
		#											Function_2.get_time('forFile'), frame_number)  )
		path_to_folder, path_to_file = SaveData.update_folders_and_files()
		
		try:
			os.makedirs(path_to_folder)
		except Exception as e:
			print(e)
		if os.path.isdir(path_to_folder) == os.path.isdir(path_to_file[0:-9]):
			print('Files are beeing created in .... ', path_to_folder)
			cv2.imwrite(path_to_file+'_{}_{}.jpg'.format(frame_number, tag), frame)
			#print('matCHEEEEEEEEEEE', matches.shape)
			#for match in matches:
			#print('match_shape',match.shape)
			print('Files are beeing created for matches in .... ', path_to_folder)
			cv2.imwrite(path_to_file+'_{}_{}_matches.jpg'.format(frame_number, tag), matches)

	def __call__(self,context):

		print(context)
		#self.create_folder_and_save(context[0], context[1], context[2], context[3])















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
			#x1 = 3000
			#x2 = 3200

			#y1 = 2200
			#y2 = 2400
			#frame_real = frame_real[y1:y2, x1:x2] 

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
			self.saver.create_folder_and_save(frame_number, frame_resized, 'FUN2')
						
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
	@staticmethod
	def create_db_and_save(frame_number, frame, tag):

		retval, buff = cv2.imencode('.jpg', frame_resized)

		jpg_as_text = base64.b64encode(buff)


		image_64_encode = base64.encodestring(jpg_as_text)
		base64_string = image_64_encode.decode(ENCODING)

		base64_string_resized = base64_string
		with conn:
			c.execute("INSERT INTO infractions VALUES (:frame_resized, :frame_number)", {'frame_resized': base64_string_resized, 'frame_number': frame_number})


"""

class Queue:
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def dequeue(self):
        return self.items.pop()

    def size(self):
        return len(self.items)


q=Queue()
	
q.enqueue(4)
q.enqueue('dog')
q.enqueue(True)
print(q.size())

"""