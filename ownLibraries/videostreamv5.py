
# import the necessary packages
from threading import Thread
import cv2
import datetime
import bgsubcnt
import time
from semaforo import CreateSemaforo

class FPS:
    def __init__(self):
        # store the start time, end time, and total number of frames
        # that were examined between the start and end intervals
        self._start = None
        self._end = None
        self._numFrames = 0

    def start(self):
        # start the timer
        self._start = datetime.datetime.now()
        return self

    def stop(self):
        # stop the timer
        self._end = datetime.datetime.now()

    def update(self):
        # increment the total number of frames examined during the
        # start and end intervals
        self._numFrames += 1

    def elapsed(self):
        # return the total number of seconds between the start and
        # end interval
        return (self._end - self._start).total_seconds()

    def fps(self):
        # compute the (approximate) frames per second
        return self._numFrames / self.elapsed()


class WebcamVideoStream:
	def __init__(self, src=0, resolution = (320,240), poligono=None, draw=False):

		width, height= resolution[0], resolution[1]
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
		(self.grabbed, self.frame) = self.stream.read()
		# initialize the variable used to indicate if the thread should
		# be stopped
		time.sleep(1)
		self.stopped = False
		self.draw = draw

		print(self.frame)
		print('-----------------------------------------------')
		print("FRAME ORIGIN SHaPe????????????", self.frame.shape)
		print('-----------------------------------------------')
		# Resized artifact variable
		#self.frame_resized = cv2.resize(self.frame, (320,240))	
		self.frame_resized =  cv2.resize(self.frame, (320,240))
		print('FRAME:RESIZED', self.frame_resized.shape)

		# Semaforo part

		# find MAX, MIN values  in poligono
		maxinX = max([x[0] for x in poligono])
		maxinY = max([y[1] for y in poligono])

		mininX = min([x[0] for x in poligono])
		mininY = min([y[1] for y in poligono])

		# Values to cut the self.frame_resized for the 
		# semaforo input

		self.x0 = mininX//2
		self.x1 = maxinX//2

		self.y0 = mininY//2
		self.y1 = maxinY//2

		self.imagen_semaforo = self.frame_resized[self.y0:self.y1,self.x0:self.x1]



		##### BG part

		# (3, False, 3*15) are parameters to adjust the bgsub behavior
		# first parameter : Number of frames until the bg "rememver the differences"
		# second parameter : Remember Frames until the end?
		# thirth parameter : first parameter * FPS excpeted
		print('INIT_PARAMS FOR BG')
		self.fgbg = bgsubcnt.createBackgroundSubtractor(3, False, 3*10)
		self.k = 31
		self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

		# Adjust the minimum size of the blog matching contour
		self.min_contour_width=30
		self.min_contour_height=30

		self.matches = []
		self.recordados = {}

		self.frame_number = -1


		# FOR SEMAFORO

		self.semaforo = CreateSemaforo(periodoSemaforo = 0)


		self.senalColor = None
		self.colorLiteral = None
		self.flancoSemaforo  = None


		# For CUT the HD IMAGE

		# Get shape from HD frame and LR frame

		self.scale = self.frame.shape[0] * self.frame.shape[1] // self.frame_resized.shape[0] * self.frame_resized.shape[1]

	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()

			# Set new resolution for the consumers
			self.frame_resized = cv2.resize(self.frame, (320,240))

			self.imagen_semaforo = self.frame_resized[self.y0:self.y1,self.x0:self.x1]
			#print('shape?',self.frame_resized.shape)


			##  BackGroundSub part
			print('ENTERING BG SUBBBBBBBBBBBBBBB')
			self.BgSubCNT(self.frame_resized)
			print('EXITING BG SUBBBBBBBBBBBBBBB')
			self.frame_number += 1

			# RETURNING VALUES FOR SEMAFORO
			self.senalColor, self.colorLiteral, self.flancoSemaforo  = self.semaforo.obtenerColorEnSemaforo(self.imagen_semaforo)

			# Cutting the HD image
			self.cutHDImage(self.frame)

	def read(self):
		# return the frame most recently read
		return self.frame_resized, self.senalColor, self.colorLiteral, self.flancoSemaforo 

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True



	def BgSubCNT(self,frame,frame_number = None):
		# Variable to track the "matched cars" in the bgsubcnt 
		self.matches = []

		# Starting the Bgsubcnt logic

		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		smooth_frame = cv2.GaussianBlur(gray, (self.k,self.k), 1.5)
		#smooth_frame = cv2.bilateralFilter(gray,4,75,75)
		#smooth_frame =cv2.bilateralFilter(smooth_frame,15,75,75)

		# this is the bsubcnt result 
		self.fgmask = self.fgbg.apply(smooth_frame, self.kernel, 0.1)

		# just thresholding values
		self.fgmask[self.fgmask < 240] = 0
		
		self.fgmask = self.filter_mask(self.fgmask, self.frame_number)


		# Find the contours 
		im2, contours, hierarchy = cv2.findContours(self.fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
		

		# for all the contours, calculate his centroid and position in the current frame
		for (i, contour) in enumerate(contours):
			(x, y, w, h) = cv2.boundingRect(contour)
			contour_valid = (w >= self.min_contour_width) and (h >= self.min_contour_height)
			if not contour_valid:
				continue
			centroid =  WebcamVideoStream.get_centroid(x, y, w, h)

			# apeend to the matches for output from current frame
			self.matches.append(((x, y, w, h), centroid))
			# Optional, draw rectangle and circle where you find "movement"
			if self.draw == True:
				cv2.rectangle(frame, (x,y),(x+w-1, y+h-1),(0,0,255),1)
				cv2.circle(frame, centroid,2,(0,255,0),-1)
			else:
				pass
	def filter_mask(self, img, a=None):
		'''
		This filters are hand-picked just based on visual tests
		'''

		kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))

		# Fill any small holes
		closing = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
		# Remove noise
		opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)

		# Dilate to merge adjacent blobs
		dilation = cv2.dilate(opening, kernel, iterations=2)

		#cv2.imwrite('../blob/blob_frame_{}.jpg'.format(a), img)
		return dilation

	def cutHDImage(self, HDframe):
		self.recordados = {}

		if len(self.matches) > 0:

			listaderecortados = []

			for match in self.matches:

				box = match[0]

				x = box[0] * self.scale
				y = box[1] * self.scale
				w = box[2] * self.scale
				h = box[3] * self.scale

				recortado = HDframe[y:h, x:w]
				listaderecortados.append(recortado)

			self.recortado[self.frame_number] = listaderecortados
		else:
			pass

	@staticmethod
	def distance(x, y, type='euclidian', x_weight=1.0, y_weight=1.0):

		if type == 'euclidian':
			return math.sqrt(float((x[0] - y[0])**2) / x_weight + float((x[1] - y[1])**2) / y_weight)

	@staticmethod
	def get_centroid(x, y, w, h):
		x1 = int(w / 2)
		y1 = int(h / 2)

		cx = x + x1
		cy = y + y1

		return (cx, cy)

class VideoStream:
	def __init__(self, src=0, usePiCamera=False, resolution=(320, 240),	framerate=32, poligono = None, draw=False):
		# check to see if the picamera module should be used
		if usePiCamera:
			# only import the picamera packages unless we are
			# explicity told to do so -- this helps remove the
			# requirement of `picamera[array]` from desktops or
			# laptops that still want to use the `imutils` package
			from .pivideostreamlib import PiVideoStream

			# initialize the picamera stream and allow the camera
			# sensor to warmup
			self.stream = PiVideoStream(resolution=resolution, framerate=framerate)

		# otherwise, we are using OpenCV so initialize the webcam
		# stream
		else:
			self.stream = WebcamVideoStream(src=src, resolution=resolution, poligono = poligono, draw=draw)

	def start(self):
		# start the threaded video stream
		return self.stream.start()

	def update(self):
		# grab the next frame from the stream
		self.stream.update()

	def read(self):
		# return the current frame
		return self.stream.read()

	def stop(self):
		# stop the thread and release any resources
		self.stream.stop()




if __name__ == '__main__':
	"""
	Debugss

	"""
	import numpy as np
	import argparse
	import imutils
	import time
	import cv2
	 
	# construct the argument parse and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-v", "--video", required=True,
		help="path to input video file", type=int)
	args = vars(ap.parse_args())

	print("[INFO] starting video file thread...")

	# 8 mp ????
	height = 3264
	width = 2448

	resolution = (height, width)

	vs = VideoStream(src = args["video"], resolution = (640,480)).start()

	time.sleep(1.0)

	# start the FPS timer
	fps = FPS().start()


	# loop over frames from the video file stream
	while True:
		# grab the frame from the threaded video file stream, resize
		# it, and convert it to grayscale (while still retaining 3
		# channels)
		frame, frame_resized,_ = vs.read()
		
		#print('shape', frame)
		#frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		#frame = np.dstack([frame, frame, frame])
	 
		# show the frame and update the FPS counter
		cv2.imshow('frame_hd', frame)
		cv2.imshow("Frame", frame_resized)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
		fps.update()

	# stop the timer and display FPS information
	fps.stop()
	print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	 
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()