# import the necessary packages
from imutils.video import VideoStream
import datetime
import argparse
import imutils
import time
import cv2
import sys
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--picamera", type=int, default=0,
	help="whether or not the Raspberry Pi camera should be used")
args = vars(ap.parse_args())

# initialize the video stream and allow the cammera sensor to warmup
#vs = VideoStream(0, resolution=(640,480)).start()
vs = cv2.VideoCapture(0)

vs.set(cv2.CAP_PROP_FRAME_WIDTH, 2592)  #3240
vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 1944)  #2464
time.sleep(2.0)
#killyourself=[]
counter  = 0
# loop over the frames from the video stream
while True:
	# grab the frame from the threaded video stream and resize it
	# to have a maximum width of 400 pixels
	ret, frame = vs.read()
	#killyourself.append(frame)
	#print(frame.shape)
	#frame = imutils.resize(frame, width=400)

	# draw the timestamp on the frame
	timestamp = datetime.datetime.now()
	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)

	# show the frame
	cv2.imshow("Frame", cv2.resize(frame,(320,240)))
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		break
	if key == ord("s"):
		cv2.imwrite('./demo_cv2_{}.jpg'.format(counter), frame)
		print('image saved to disk..{}'.format(counter))
		counter += 1

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
