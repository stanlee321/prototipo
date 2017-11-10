
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
	def __init__(self, src=0, resolution = (320,240)):
		
		width, height = resolution[0], resolution[1]
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)

		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
		#self.stream.set(cv2.CAP_PROP_EXPOSURE, -1)
		#self.stream.set(cv2.CAP_PROP_EXPOSURE, 50)
		(self.grabbed, self.frame) = self.stream.read()
		

		self.frame_resized = np.zeros((320,240,3), dtype='f')
		# initialize the variable used to indicate if the thread should
		# be stopped
		time.sleep(1)
		self.stopped = False

		self.font = cv2.FONT_HERSHEY_SIMPLEX
		self.frame_number = -1

		self.data = {'HRframe': self.frame, 'LRframe': self.frame_resized}

	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			t1 = time.time()
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return
			# otherwise, read the next frame from the stream

			(self.grabbed, self.frame) = self.stream.read()
			self.frame_resized = cv2.resize(self.frame, (320,240))


			#cv2.putText(self.frame, str('Frame: ') + str(self.frame_number),(20,20), self.font, 0.4,(255,0,0),1,cv2.LINE_AA)
			#cv2.putText(self.frame, str('In took: ') + str(time.time()-t1),(20,60), self.font, 0.4,(255,0,0),1,cv2.LINE_AA)
			#self.frame_number +=1

			self.data = {'HRframe': self.frame[:,:,:], 'LRframe': self.frame_resized[:,:,:]}

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
