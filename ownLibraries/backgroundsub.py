
# import the necessary packages
import cv2
import bgsubcnt
import numpy as np
import time
class BGSUBCNT():
	def __init__(self, thresh=5):
		##### BG part
			# (3, False, 3*15) are parameters to adjust the bgsub behavior
		# first parameter : Number of frames until the bg "rememver the differences"
		# second parameter : Remember Frames until the end?
		# thirth parameter : first parameter * FPS excpeted

		self.fgbg 	= bgsubcnt.createBackgroundSubtractor(3, False, 3 * 10) #self.fps
		self.k 		= 15
		self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

		# Adjust the minimum size of the blog matching contour
		self.min_contour_width 	= thresh
		self.min_contour_height = thresh

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
		
		im2, contours, hierarchy = cv2.findContours(self.fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
		
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

		return self.fgmask, self.matches
		
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

		return dilation

	def __call__(self):
		return [self.fgmask, self.gray]


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
	import os
	# construct the argument parse and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-v", "--video",  default=0,  help="path to input video file", type = str)
	ap.add_argument("-t", "--thress", default= 5, help="thress to manage the rectangles", type=int)
	ap.add_argument("-hh", "--height", default = 320, help="inputa resolution", type=int)
	ap.add_argument("-ww", "--width",  default =  240, help="input resolution", type=int)

	args = vars(ap.parse_args())

	print("[INFO] starting video file thread...")

	wHeight = args['height']
	wWidth 	= args['width']
	print(wHeight ,wWidth )
	input_res = (wHeight,wWidth)
	print(args)
	thresh 				= args['thress']
	path_to_video_test	= os.getenv('HOME') + '/' + 'trafficFlow' + '/' + 'trialVideos' +'/' + args['video']#'sar.mp4'
	cap 				= cv2.VideoCapture(path_to_video_test)
	resolution 			= (wHeight, wWidth)
	time.sleep(1.0)
	# start the FPS timer
	backgroundsub = BGSUBCNT(thresh)
	# loop over frames from the video file stream
	#scale = 10
	while True:
		time.sleep(0.03)
		t1 = time.time()
		_, img = cap.read()
		# Feed to BGSUB
		img 			= cv2.resize(img, input_res)
		#xShape, yShape 	= img.shape[0], img.shape[1]
		#img = cv2.resize(img,(int(xShape/scale), int(yShape/scale)))
		mask, poligonos_warp = backgroundsub.feedbgsub(img)


		if len(poligonos_warp) > 0:
			for box in poligonos_warp:
				rectangle, centroid = box[0], box[1]
				(x, y, w, h) = rectangle
				cv2.rectangle(img, (x,y),(x+w-1, y+h-1),(0,0,255),1)
				cv2.circle(img, centroid,2,(0,255,0),-1)

		font = cv2.FONT_HERSHEY_SIMPLEX

		#imagen = np.hstack([img,mask])

		shape = img.shape
		print(shape)
		px = int(shape[0]*scale)
		py = int(shape[1]*0.95*scale)
		cv2.putText(img,str('shape is'+ str(shape)),(px,py), font, 1,(0,255,3),2,cv2.LINE_AA)
		cv2.imshow("Frame", 	cv2.resize(img,  (640,480)))
		cv2.imshow('bgresult', 	cv2.resize(mask, (640,480)))
		#cv2.imshow('Subresults', cv2.resize(img,(0,240)))
		print('TOOK', time.time() - t1)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	# do a bit of cleanup
	cv2.destroyAllWindows()

