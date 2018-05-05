import os
import cv2
import time
import numpy as np

directorioDeVideos  = os.getenv('HOME') + '/trafficFlow/trialVideos'
archivoDeVideo = 'mySquare.mp4'

fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()

miCamara = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)

tiempo = time.time()

while True:
	ret, frameVideo = miCamara.read()
	frameVideo = cv2.resize(frameVideo,(320,240))
	cv2.imshow('Normal',frameVideo)
	#BLUR:
	frameVideo = cv2.blur(frameVideo,(5,5))
	#EDGES:
	frameVideo = cv2.Canny(frameVideo,100,200)
	cv2.imshow('Canny',frameVideo)

	#BACKGROUND:
	frameVideo = fgbg.apply(frameVideo)
	cv2.imshow('Canny & BSMOG',frameVideo)
	#plt.subplot(121),plt.imshow(frameVideo,cmap = 'gray')
	#plt.title('Original Image'), plt.xticks([]), plt.yticks([])
	#plt.subplot(122),plt.imshow(edges,cmap = 'gray')
	#plt.title('Edge Image'), plt.xticks([]), plt.yticks([])

	#plt.show()
	
	print(time.time()-tiempo)
	tiempo = time.time()

	ch = 0xFF & cv2.waitKey(5)
	if ch == ord('q'):
		break