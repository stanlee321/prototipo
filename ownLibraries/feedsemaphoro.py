"""
Calculate the seamaphoro parameters
"""

import cv2
import numpy as np
class SemaphoroParameters():
	def __init__(self, poligono640, debug = False):

		
		maxinX = max([x[0] for x in poligono640])
		maxinY = max([y[1] for y in poligono640])

		mininX = min([x[0] for x in poligono640])
		mininY = min([y[1] for y in poligono640])

		self.x0 = mininX
		self.x1 = maxinX 
		self.y0 = mininY
		self.y1 = maxinY

		# YELLOW /(Orangen) range
		self.lower_yellow = np.array([18,100,0], dtype=np.uint8)
		self.upper_yellow = np.array([190,255,255], dtype=np.uint8)

		# RED range
		self.lower_red = np.array([140,100,0], dtype=np.uint8) #_,100,_
		self.upper_red = np.array([180,255,255], dtype=np.uint8)

		# GREEN range
		self.lower_green = np.array([70,0,0], dtype=np.uint8)
		self.upper_green = np.array([90,255,255], dtype=np.uint8)

		# SOME VARIABLES for SVM, if retrain the SVM in another
		# resolution, change this val to this resolution.
		self.SHAPE = (30,30)


	def __call__(self, frame):


		f = frame[self.y0 : self.y1, self.x0 : self.x1]

		"""

		hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
		
		# SOME MASKS
		mask_red = cv2.inRange(hsv, self.lower_red, self.upper_red)
		mask_yellow = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)
		mask_green = cv2.inRange(hsv, self.lower_green, self.upper_green)

		full_mask = mask_red + mask_yellow + mask_green

		# Put the mask and filter the R, Y , G colors in _imagen_
		res = cv2.bitwise_and(f, f, mask= full_mask)

		#res = cv2.GaussianBlur(res,(15,15),2)

		#res = cv2.medianBlur(res,15)

		#res = cv2.bilateralFilter(res,30,75,75,75/2)
		res = cv2.bilateralFilter(res,35,75,75)


		pixeles1 = cv2.resize(res, (8,24), interpolation = cv2.INTER_NEAREST)
		pixeles2 = cv2.resize(res, (8,24), interpolation = cv2.INTER_LANCZOS4)
		pixeles3 = cv2.resize(res, (8,24), interpolation = cv2.INTER_CUBIC)
		"""

		pixeles1 = cv2.resize(f, (8,24), interpolation = cv2.INTER_NEAREST)
		pixeles2 = cv2.resize(f, (8,24), interpolation = cv2.INTER_LANCZOS4)
		pixeles3 = cv2.resize(f, (8,24), interpolation = cv2.INTER_CUBIC)


		cv2.imshow('nearest', cv2.resize(pixeles1,(320,240)))
		cv2.imshow('slanczos4', cv2.resize(pixeles2,(320,240)))
		cv2.imshow('cubic', cv2.resize(pixeles3,(320,240)))

		pixeles = pixeles1.flatten()

		return pixeles
