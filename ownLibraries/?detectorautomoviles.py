#!/usr/bin/env python

import numpy as np
import cv2

class DetectorAutomoviles():
	def __init__(self):	#size (320,240)
	# BackGroundSubs
		self.carSize = 800
		self.carSizeMaximum = 6000
		self.kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
		self.back=cv2.createBackgroundSubtractorMOG2(detectShadows=True)

	def getCarCenters(self,current_image):
		fram = cv2.medianBlur(current_image,11) # 7 default
		fgmask = self.back.apply(fram)
		blur = cv2.GaussianBlur(fgmask,(7,7),1)
		fgmask = cv2.morphologyEx(blur, cv2.MORPH_OPEN, self.kernel)
		contor = fgmask.copy()
		im, contours,hierarchy =cv2.findContours(contor,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
		centers = []
		rectangles = []
		for cantObjetos in contours:
			if (cv2.contourArea(cantObjetos) >= self.carSize) & (cv2.contourArea(cantObjetos) <= self.carSizeMaximum):
			#if cv2.contourArea(cantObjetos) >=self.carSize:
				x,y,ancho,alto=cv2.boundingRect(cantObjetos)
				a=int(x+ancho/2)
				b=int(y+alto/2)
				centers.append([a,b])
				rectangles.append([x,y,ancho,alto])
		return np.array(centers), np.array(rectangles)