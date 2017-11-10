
# import the necessary packages
import cv2
import bgsubcnt
import numpy as np
import time
class BGSUBCNT():
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
		
	def feedbgsub(self, frame):
		# Variable to track the "matched cars" in the bgsubcnt
		print('HELLO :::FEEDING...')
		self.matches = []
		t1 = time.time()
		# Starting the Bgsubcnt logic

		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		smooth_frame = cv2.GaussianBlur(gray, (self.k,self.k), 1.5)
		#smooth_frame = cv2.bilateralFilter(gray,4,75,75)
		#smooth_frame =cv2.bilateralFilter(smooth_frame,15,75,75)

		# this is the bsubcnt result 
		self.fgmask = self.fgbg.apply(smooth_frame, self.kernel, 0.1)

		print('FOOR LOOP TOOK', time.time-t1)

		
		# just thresholding values
		self.fgmask[self.fgmask < 240] = 0
		
		self.fgmask = self.filter_mask(self.fgmask)

		#return self.fgmask

		
		# Find the contours 
		im2, contours, hierarchy = cv2.findContours(self.fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
		
		# for all the contours, calculate his centroid and position in the current frame
		
		for (i, contour) in enumerate(contours):
			(x, y, w, h) = cv2.boundingRect(contour)
			contour_valid = (w >= self.min_contour_width) and (h >= self.min_contour_height)
			if not contour_valid:
				continue
			centroid = BGSUBCNT.get_centroid(x, y, w, h)

			# apeend to the matches for output from current frame
			self.matches.append([(x, y, w, h), centroid])
			
			# Optional, draw rectangle and circle where you find "movement"
			#if self.draw == True:
			#cv2.rectangle(frame, (x,y),(x+w-1, y+h-1),(0,0,255),1)
			#cv2.circle(frame, centroid,2,(0,255,0),-1)
			#else:
			#	pass
		return self.matches
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

	def __call__(self):
		return self.matches


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



if __name__ == '__main__':
	"""
	Debugss

	"""
	import numpy as np
	import argparse
	import imutils
	import time
	import cv2
	from videostreamv2 import VideoStream
	from videostreamv2 import FPS
	# construct the argument parse and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-v", "--video", default=0,
		help="path to input video file", type= str)
	args = vars(ap.parse_args())

	print("[INFO] starting video file thread...")

	# 8 mp ????
	height = 640
	width = 480

	resolution = (height, width)

	vs = VideoStream(src = args["video"], resolution = resolution).start()

	time.sleep(1.0)
	# start the FPS timer
	fps = FPS().start()
	backgroundsub = BGSUBCNT()
	# loop over frames from the video file stream
	while True:
		t1 = time.time()
		# grab the frame from the threaded video file stream, resize
		# it, and convert it to grayscale (while still retaining 3
		# channels)
		data = vs.read()

		frame = data['HRframe']

		LRFrame = data['LRframe']

		# Feed to BGSUB
		poligonos_warp = backgroundsub.feedbgsub(LRFrame)


		"""
		RESERVADO DANIEL WARP

		"""
	
		#poligonos_warp = backgroundsub()

		print(poligonos_warp)
		"""
		poligonos_reales = f(poligonos_warp)
		"""


		
		#cv2.imshow('bgsub', f)
		#cv2.imshow("Frame", LRFrame)

		print('TOOK', time.time() - t1)
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
