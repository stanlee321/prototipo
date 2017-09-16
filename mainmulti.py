# import the necessary packages
from __future__ import print_function
#from imutils.video import WebcamVideoStream
#from imutils.video import FPS
from ownLibraries.utils import WebcamVideoStream
from ownLibraries.utils import FPS
import imutils
import cv2
import argparse
import time

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-d", "--display", type=int, default=1,
	help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

print("[INFO] sampling THREADED frames from webcam...")
vs = WebcamVideoStream(src=0, height = 600, width = 400).start()
fps = FPS().start()
 
# loop over some frames...this time using the threaded stream
while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	frame = vs.read()

	t = time.time()
	# Resize??
	#frame = imutils.resize(frame, width=400)
 	# check to see if the frame should be displayed to our screen
	if args["display"] > 0:
		cv2.imshow("Frame", frame)

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
		print('[INFO] elapsed time: {:.2f}'.format(time.time() - t))

 	# update the FPS counter


	fps.update()
 
# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
 
# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
