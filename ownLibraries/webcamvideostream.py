# import the necessary packages
from threading import Thread
import cv2
import numpy as np
class WebcamVideoStream:
	def __init__(self, src=0, resolution = (320,240)):
		print('JALLO AUS VideoCapture!!')
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		time.sleep(5)
		#self.stream.set(cv2.CAP_PROP_EXPOSURE, 100)

		width, height = resolution[0], resolution[1]
		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)


		#(self.grabbed, self.frame) = self.stream.read()
		self.frame = np.zeros(resolution, np.int8)
		self.frame_resized = np.zeros((320,240), np.int8)

		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False

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

			#self.stream.set(cv2.CAP_PROP_EXPOSURE, 100)

			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()
			self.frame_resized = cv2.resize(self.frame, (320,240))


	def read(self):
		# return the frame most recently read
		return self.frame, self.frame_resized

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True