import cv2
import bgsubcnt
from multiprocessing import Process, Queue, Pool
from new_libs.math_and_utils import get_centroid
from new_libs.math_and_utils import distance







class CreateBGCNT():

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


	def __call__(self, LOW_RES_FRAM):

		self.input_q.put(LOW_RES_FRAM)

		matches = self.output_q.get()
		
		return matches, LOW_RES_FRAM



""" USELESS CLASS FOR NOW 

class CreateBG(object):
	def __init__(self):
		# Define the parameters needed for motion detection
		self.k = 31
		self.alpha = 0.02 # Define weighting coefficient for running average
		self.motion_thresh = 35 # Threshold for what difference in pixels  
		self.running_avg = None # Initialize variable for running average
		self.min_contour_width=15 
		self.min_contour_height=15
	#@property
	def visual(self, current_frame):

		gray_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
		t1 = time.time()
		smooth_frame = cv2.GaussianBlur(gray_frame, (self.k, self.k), 0)

		# If this is the first frame, making running avg current frame
		if self.running_avg is None:
			self.running_avg = np.float32(smooth_frame) 

		# Find absolute difference between the current smoothed frame and the running average
		diff = cv2.absdiff(np.float32(smooth_frame), np.float32(self.running_avg))
		t2 = time.time()

		print('THE DIFF TOOOOK', t2-t1)


		# Then add current frame to running average after
		cv2.accumulateWeighted(np.float32(smooth_frame), self.running_avg, self.alpha)

		# For all pixels with a difference > thresh, turn pixel to 255, otherwise 0
		_, subtracted = cv2.threshold(diff, self.motion_thresh, 1, cv2.THRESH_BINARY)

		matches = []
		
		subtracted = np.array(subtracted * 255, dtype = np.uint8)

		fg_mask = subtracted	

		im2, contours, hierarchy = cv2.findContours(subtracted, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

		#cv2.imshow('im2', im2)

		#print( len(contours))
		
		for (i, contour) in enumerate(contours):
		    (x, y, w, h) = cv2.boundingRect(contour)
		    contour_valid = (w >= self.min_contour_width) and (h >= self.min_contour_height)
		    if not contour_valid:
		        continue

		    centroid = math_and_utils.get_centroid(x, y, w, h)

		    matches.append(((x, y, w, h), centroid))


		#cv2.imshow('Thresholded difference', subtracted)

		return matches
		#cv2.imshow('Actual image', current_frame)
		#cv2.imshow('Gray-scale', gray_frame)
		#cv2.imshow('Smooth', smooth_frame)
		#cv2.imshow('Difference', diff)

	#cv2.destroyAllWindows()
"""