
# import the necessary packages
from threading import Thread
import cv2
import datetime
import time
import numpy as np
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

class VideoStream:
	def __init__(self, src=0, resolution = (320,240), poligono = [(0,0),(640,480)], debug = False, fps = 10):
		self.debug = debug
		width, height = resolution[0], resolution[1]
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
		#self.stream.set(cv2.CAP_PROP_EXPOSURE, -1)
		#self.stream.set(cv2.CAP_PROP_EXPOSURE, 50)


		(self.grabbed, self.frame) = self.stream.read()
		
		# initialize the variable used to indicate if the thread should
		# be stopped
		time.sleep(1)
		self.stopped = False

		self.font = cv2.FONT_HERSHEY_SIMPLEX
		self.frame_number = -1

		print('-----------------------------------------------')
		print("FRAME ORIGIN SHAPE", self.frame.shape)
		print('-----------------------------------------------')

		# If is debug mode
		if self.debug == True:
			print('::::::::BIENBENIDOS AL MODO DEBUG::::::::::')

			self.frame_resized = cv2.resize(self.frame, (320,240))
			print('FRAME:RESIZED', self.frame_resized.shape)
			print('FRAME', self.frame.shape)

			##### Semaforo part
			# find MAX, MIN values  in poligono
			maxinX = max([x[0] for x in poligono])
			maxinY = max([y[1] for y in poligono])

			mininX = min([x[0] for x in poligono])
			mininY = min([y[1] for y in poligono])
			# Values to cut the self.frame_resized for the 
			# semaforo input

			self.x0 = mininX //2 
			self.x1 = maxinX //2

			self.y0 = mininY //2
			self.y1 = maxinY //2

		else:
			# Resized normal frame
			self.frame_medium = cv2.resize(self.frame, (640,480))
			# Set new resolution for the consumers
			self.frame_resized = cv2.resize(self.frame_medium, (320,240))
			print('FRAME:RESIZED', self.frame_resized.shape)
			print('FRAME MEDIUM', self.frame_medium.shape)


			##### Semaforo part
			# find MAX, MIN values  in poligono
			maxinX = max([x[0] for x in poligono])
			maxinY = max([y[1] for y in poligono])

			mininX = min([x[0] for x in poligono])
			mininY = min([y[1] for y in poligono])
			# Values to cut the self.frame_resized for the 
			# semaforo input

			self.x0 = mininX
			self.x1 = maxinX

			self.y0 = mininY
			self.y1 = maxinY
			
		self.imagen_semaforo = self.frame_resized[self.y0:self.y1,self.x0:self.x1]
		self.data = {'HRframe': self.frame, 'LRframe': self.frame_resized, 'frame_semaforo' : self.imagen_semaforo}
		
		if self.debug == True:
			self.ratio = 30 / fps
	

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
			#t1 = time.time()
			self.frame_medium = cv2.resize(self.frame, (640,480), interpolation = cv2.INTER_NEAREST)
			# Set new resolution for the consumers
			self.frame_resized = cv2.resize(self.frame_medium, (320,240), interpolation = cv2.INTER_NEAREST)
			# Cut imagen for the semaforo
			#print('rezising took', time.time()- t1)
			self.imagen_semaforo = self.frame_medium[self.y0:self.y1,self.x0:self.x1]

			self.data = {'HRframe': self.frame, 'LRframe': self.frame_resized, 'frame_semaforo' : self.imagen_semaforo}

	def read(self):
		# return the frame most recently read
		return self.data
	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True

if __name__ == '__main__':
	"""
	Debugss

	"""
	import argparse
	import imutils
	import time
	 
	# construct the argument parse and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-v", "--video", default=0,
		help="path to input video file", type=int or str)
	args = vars(ap.parse_args())

	print("[INFO] starting video file thread...")

	# 8 mp ????
	height = 640
	width = 480

	resolution = (height, width)

	vs = VideoStream(src = args["video"], resolution = (640,480)).start()

	# start the FPS timer
	fps = FPS().start()

	# loop over frames from the video file stream
	counter  = -1
	while True:
		# grab the frame from the threaded video file stream, resize
		# it, and convert it to grayscale (while still retaining 3
		# channels)
		t1 = time.time()
		data = vs.read()
		
		frame = data['HRframe']

		LRFrame = data['LRframe']

		#print('shape', frame)
		#frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		#frame = np.dstack([frame, frame, frame])
	 
		# show the frame and update the FPS counter
		cv2.putText(frame, str('out took: ') + str('{:0.5f}'.format(time.time()-t1)),(20,100), cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0,255,0),1,cv2.LINE_AA)
		cv2.putText(frame, str('FRAME OUT: ') + str(counter),(20,120), cv2.FONT_HERSHEY_SIMPLEX, 0.4,(0,255,0),1,cv2.LINE_AA)

		cv2.imshow('frame_hd', frame)
		cv2.imshow('frame_lr', LRFrame)

		counter += 1
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
