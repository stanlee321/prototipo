"""
This file simulates simple captures for the raspberry pi camera
"""

# import the necessary packages
from __future__ import print_function
#from imutils.video import WebcamVideoStream
#from imutils.video import FPS

import os
import cv2
import time
import imutils
import datetime
import argparse

directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
saveDirectory = directorioDeTrabajo+'/VideoCapture/'

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
cam=cv2.VideoCapture(0)
cam.set(3,width)
cam.set(4,height)
 
# loop over some frames...this time using the threaded stream
#while fps._numFrames < args["num_frames"]:
counter = 0
tiempoAuxiliar = time.time()
while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	ret0, frame=cam.read()
	print(frame.shape)
	if True:#comparator == 0:
		#cv2.imwrite(saveDirectory+'frame_{}_{}.jpg'.format(counter, date_string), frame[yMin:yMax,xMin:xMax])
		print(counter)
		# update the FPS counter
	counter +=1
	print(time.time()-tiempoAuxiliar)
	tiempoAuxiliar = time.time()
	ch = 0xFF & cv2.waitKey(5)
	if ch == ord('q'):
		break
 
# stop the timer and display FPS information
 
# do a bit of cleanup
cv2.destroyAllWindows()
