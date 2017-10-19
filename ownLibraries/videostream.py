
# import the necessary packages
from videostreamerlib import WebcamVideoStream
from videostreamerlib import FPS


class VideoStream:
	def __init__(self, src=0, usePiCamera=False, resolution=(320, 240),	framerate=32):
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
			self.stream = WebcamVideoStream(src=src, resolution=resolution)

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
		frame, frame_resized = vs.read()
		
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