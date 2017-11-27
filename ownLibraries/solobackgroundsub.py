
# import the necessary packages
import cv2
import bgsubcnt
import numpy as np
import time
class SOLOBGSUBCNT():
	def __init__(self):
		
		##### BG part
			# (3, False, 3*15) are parameters to adjust the bgsub behavior
		# first parameter : Number of frames until the bg "rememver the differences"
		# second parameter : Remember Frames until the end?
		# thirth parameter : first parameter * FPS excpeted

		self.fgbg = bgsubcnt.createBackgroundSubtractor(3, False, 3 * 10) #self.fps
		self.k = 31
		self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

		# Adjust the minimum size of the blog matching contour
		self.min_contour_width = 30
		self.min_contour_height = 30

		# list like to append bounding box where is the moving object
		self.matches = []
		self.gray = None
		
	def feedbgsub(self, frame):
		#t0 = time.time()
		# Variable to track the "matched cars" in the bgsubcnt
		self.matches = []
		#t1 = time.time()
		# Starting the Bgsubcnt logic

		self.gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		smooth_frame = cv2.GaussianBlur(self.gray, (self.k,self.k), 1.5)
		#smooth_frame = cv2.bilateralFilter(gray,4,75,75)
		#smooth_frame =cv2.bilateralFilter(smooth_frame,15,75,75)

		# this is the bsubcnt result 
		self.fgmask = self.fgbg.apply(smooth_frame, self.kernel, 0.1)
		

	def __call__(self):
		return self.fgmask

if __name__ == '__main__':
	"""
	Debugss
	"""

	import numpy as np
	import argparse
	import imutils
	import time
	import cv2
	from videostreamv1 import VideoStream
	# construct the argument parse and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-v", "--video", default = 0,
		help="path to input video file", type = str)
	args = vars(ap.parse_args())

	# 8 mp ????
	height = 640
	width = 480

	resolution = (height, width)

	vs = VideoStream(src = 0, resolution = resolution).start()

	# start the FPS timer
	backgroundsub = SOLOBGSUBCNT()

	# loop over frames from the video file stream
	while True:

		frame = vs.read()

		# Feed to BGSUB
		backgroundsub.feedbgsub(frame)
		"""
		poligonos_reales = f(poligonos_warp)
		"""
		sub = backgroundsub().shape
		imagen = np.vstack(sub)
		
		#cv2.imshow('bgsub', f)
		cv2.imshow("Frame", imagen)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break	
	 
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()
