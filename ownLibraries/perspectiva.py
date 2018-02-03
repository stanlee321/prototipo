import cv2
import numpy as np
import math


class Perspective():
	def __init__(self,srcPoligon):
		# Take the poligon cuted ROI IMAGE
		self.src = srcPoligon # Expected something like srcPol = [[pt1],[pt2],[pt3],[pt4]]
		self.src_point1 = self.src[0]
		self.src_point2 = self.src[1]
		self.src_point3 = self.src[2]
		self.src_point4 = self.src[3]

	def transformar(self,image):
		a=math.sqrt((self.src_point1[0]-self.src_point2[0])**2+(self.src_point1[1]-self.src_point2[1])**2)
		b=math.sqrt((self.src_point2[0]-self.src_point3[0])**2+(self.src_point2[1]-self.src_point3[1])**2)
		c=math.sqrt((self.src_point3[0]-self.src_point4[0])**2+(self.src_point3[1]-self.src_point4[1])**2)
		d=math.sqrt((self.src_point4[0]-self.src_point1[0])**2+(self.src_point4[1]-self.src_point1[1])**2)
		#print(a)
		#print(b)
		#print(c)
		#print(d)
		# como los lados se daran en orden se tomara la mayor longitud entre a y c y b y d:
		if a>c:
			lado1 = int(a)
		else:
			lado1 = int(c)
		if b>d:
			lado2 = int(b)
		else:
			lado2 = int(d)
		if lado1 < lado2:
			img_size = (lado1, lado2)
		else:
			img_size = (lado2, lado1)
		
		dst = np.float32([[0,0], [img_size[0],0], [img_size[0],img_size[1]], [0,img_size[1]]])

		# For source points I'm grabbing the outer four detected corners
		src = np.float32([self.src_point4, self.src_point3, self.src_point2, self.src_point1])
		
		# Given src and dst points, calculate the perspective transform matrix
		M = cv2.getPerspectiveTransform(src, dst)
		# Warp the image using OpenCV warpPerspective()

		transformado = cv2.warpPerspective(image, M, img_size)
		print(transformado.shape)
		transformado = cv2.resize(transformado,(transformado.shape[1]//2,transformado.shape[0]//2))
		print(transformado.shape)
		
		# Just comment the vizualization
		#cv2.imshow("original",image)
		cv2.imshow("perspective",transformado)
		#cv2.waitKey(0)

		return transformado