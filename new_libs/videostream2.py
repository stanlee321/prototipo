
# import the necessary packages
from threading import Thread
import cv2
import datetime
import bgsubcnt
import time

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
	def __init__(self, src=0, resolution = (320,240), poligono=None):

		width, height= resolution[0], resolution[1]
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
		(self.grabbed, self.frame) = self.stream.read()
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False

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

			#self.frame_number += 1


	def read(self):
		# return the frame most recently read
		return self.frame, self.frame_resized, self.imagen_semaforo

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True



	

class VideoStream:
	def __init__(self, src=0, usePiCamera=False, resolution=(320, 240),	framerate=32, poligono = None):
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
			self.stream = WebcamVideoStream(src=src, resolution=resolution, poligono = poligono)

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