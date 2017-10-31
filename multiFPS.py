"""
This file simulates a multithreading for the raspberry pi, improves the image adquisition but not saving process
"""

# import the necessary packages
from __future__ import print_function
#from imutils.video import WebcamVideoStream
#from imutils.video import FPS

import os
import cv2
import sys
import time
import imutils
import datetime
import argparse
import numpy as np
directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeLibreriasPropias = directorioDeTrabajo +'/ownLibraries'
saveDirectory = directorioDeTrabajo+'/VideoCapture/'

sys.path.insert(0, directorioDeLibreriasPropias)
from ownLibraries.webcamvideostream import WebcamVideoStream
from ownLibraries.videostreamv5 import FPS

if not os.path.exists(saveDirectory):
	os.makedirs(saveDirectory)

date_string = datetime.datetime.now().strftime('%Y-%m-%d-%H:%M')
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--num-frames", type=int, default=100,
    help="# of frames to loop over for FPS test")
ap.add_argument("-d", "--display", type=int, default=1,
    help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

# created a *threaded* video stream, allow the camera sensor to warmup,
# and start the FPS counter
print("[INFO] sampling THREADED frames from webcam...")
width = 3280
height = 2464
xMin = int(1/5*width)
xMax = int(4/5*width)
yMin = int(1/5*height)
yMax = int(4/5*height)
#vs = WebcamVideoStream(src=0,width=2592, height=1944).start()
vs = WebcamVideoStream(src=0,width=width, height=height).start()
fps = FPS().start()
 
# loop over some frames...this time using the threaded stream
#while fps._numFrames < args["num_frames"]:
counter = 0
tiempoAuxiliar = time.time()


def adjust_gamma(image, gamma=1.0):
	# build a lookup table mapping the pixel values [0, 255] to
	# their adjusted gamma values
	invGamma = gamma#1.0 / gamma
	table = np.array([((i / 255.0) ** invGamma) * 255
		for i in np.arange(0, 256)]).astype("uint8")
 
	# apply gamma correction using the lookup table
	return cv2.LUT(image, table)


while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	frame = vs.read()
	print('BEFORE', frame.shape)
	frame = imutils.resize(frame, width=320)
	print('AFTER', frame.shape)


	# check to see if the frame should be displayed to our screen
	#if args["display"] > 0:
	#	cv2.imshow("Frame", cv2.resize(frame,(640,480)))
	#	key = cv2.waitKey(1) & 0xFF
	#comparator = counter %100

	#if True:#comparator == 0:
	#	cv2.imwrite(saveDirectory+'frame_{}_{}.jpg'.format(counter, date_string), frame[yMin:yMax,xMin:xMax])
	#	print(counter)
		# update the FPS counter
		# loop over various values of gamma
	for gamma in np.arange(0.0, 3.5, 0.5):
		# ignore when gamma is 1 (there will be no change to the image)
		if gamma == 1:
			continue
	 
		# apply gamma correction and show the images
		gamma = gamma if gamma > 0 else 0.1
		adjusted = adjust_gamma(frame, gamma=gamma)
		cv2.putText(adjusted, "g={}".format(gamma), (10, 30),
			cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
		cv2.imshow("Images", np.hstack([frame, adjusted]))

		cv2.imshow('frame', frame)
	counter +=1
	fps.update()
	print(time.time()-tiempoAuxiliar)
	tiempoAuxiliar = time.time()
	ch = 0xFF & cv2.waitKey(5)
	if ch == ord('q'):
		break
 
# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
 
# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
