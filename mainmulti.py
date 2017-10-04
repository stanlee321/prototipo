#!/usr/bin/python3
# -*- coding: utf-8 -*-

# import the necessary packages
#from __future__ import print_function

import cv2
import bgsubcnt 
import numpy as np
import time
import argparse
import logging


#from new_libs import math_and_utils
#from new_libs.BackgroundsubCNT import CreateBGCNT
from new_libs.math_and_utils import genero_frame

from new_libs.utilsforFPS import WebcamVideoStream
from new_libs.utilsforFPS import FPS
from new_libs.semaforo import CreateSemaforo

from multiprocessing import Process, Queue, Pool

from new_libs.pipeline import (
    PipelineRunner,
    CreateBGCNT,
    Filtering)


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-d", "--display", type=int, default=1,
	help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

print("[INFO] sampling THREADED frames from webcam...")


ENCODING = 'utf-8'



# CREATE DB into the memory
#conn = sqlite3.connect('file::memory:?cache=shared'+'__1')
#conn = sqlite3.connect(':memory:')
#conn = sqlite3.connect('data.db')
#conn = sqlite3.connect('infractions.db')
#c = conn.cursor()

#c.execute("""CREATE TABLE infractions (
#           frame_resized text,
#            frame_number integer
#            )""")

def mydecorator(function):

	def wrapper(*args, **kwargs):
		print('hello from here')
		return function(*args, **kwargs)
	return wrapper


def show_bg(matches):

	for (i, match) in enumerate(matches):
		contour, centroid = match[0], match[1]
		#if self.check_exit(centroid, exit_masks):
		#    continue
		x, y, w, h = contour

		cv2.rectangle(frame_resized, (x, y), (x + w - 1, y + h - 1),
		              BOUNDING_BOX_COLOUR, 1)
		cv2.circle(frame_resized, centroid, 2, CENTROID_COLOUR, -1)


	cv2.imshow('boxes', cv2.resize(frame_resized,(frame_resized.shape[1]*2, frame_resized.shape[0]*2)))


if __name__ == '__main__':

	print('here we start')

	data = np.load('./installationFiles/heroes.npy')
	print(data)
	semaforo = CreateSemaforo(periodoSemaforo = 10)
	poligono  = data[0]
	src = ['./installationFiles/mySquare.mp4', 0]
	vs = WebcamVideoStream(src=src[0], height = 640, width = 480).start()
	#vs = WebcamVideoStream(src=src[1], height = 2048, width = 1536, queueSize=8).start()
	#vs = WebcamVideoStream(src=src[1], height = 2048, width = 1536).start()
	#vs = WebcamVideoStream(src=src[1], height = 2592, width = 1944).start()
	#vs = WebcamVideoStream(src=src[1], height = 3266, width = 2450).start()
	


	time.sleep(1.0)
	fps = FPS().start() 
	ON = True

	# loop over some frames...this time using the threaded stream
	log = logging.getLogger("mainmulti")


	frame_number = -1
	_frame_number = -1


	#function1 = Function_1() # Saver to db
	#function2 = Function_2() # BG substractor
	#bgsub_CNT = CreateBGCNT()

	#pipeline = PipelineRunner(pipeline=[MultiJobs( fun1 = function1, fun2 = function2)], log_level=logging.DEBUG)
	pipeline = PipelineRunner(pipeline=[CreateBGCNT(), Filtering()], log_level=logging.DEBUG)

	DIVIDER_COLOUR = (255, 255, 0)
	BOUNDING_BOX_COLOUR = (255, 0, 0)
	CENTROID_COLOUR = (0, 0, 255)
	CAR_COLOURS = [(0, 0, 255)]
	EXIT_COLOR = (66, 183, 42)

	print('jhello')
	while ON:

		# grab the frame from the threaded video stream and resize it
		# to have a maximum width of 400 pixels
		
		t1 = time.time()
		frame = vs.read()

		if not frame.any():
			log.error("Frame capture failed, stopping...")
			break
		#frame_resized, frame_real = genero_frame(frame)

		# Get signals from the semaforo
		senalColor, colorLiteral, flancoSemaforo  = semaforo.obtenerColorEnSemaforo(poligono = poligono, img = frame)
		# fake frame for debugs
		_frame_number += 1



		# skip every 2nd frame to speed up processing
		if _frame_number % 2 != 0:
			continue
		#print(frame_resized.shape)
		#matches,_ = bgsub_CNT(frame_resized)
		#show_bg(matches)
		# frame number that will be passed to pipline
		# this needed to make video from cutted frames
		frame_number += 1

		
		#pipeline.load_data({
	    #    'frame_resized': frame_resized,
	    #    'frame_real': frame_real,
	   	#    'state': colorLiteral,
	    #    'frame_number': frame_number,})
		#pipeline.run()


		t2 = time.time()

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

		if _frame_number == 1000:
			break
		#print('[INFO] elapsed time: {:.2f}'.format(time.time() - t))


		#print(senalColor, colorLiteral, flancoSemaforo)
	
		print('THE TIME THAT TAKE TO RUN THIS', t2-t1)
		# update the FPS counter
		fps.update()

	# stop the timer and display FPS information
	fps.stop()
	print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	 
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()


"""
def mydecorator(function):

	def wrapper(*args, **kwargs):
		print('hello from here')
		return function(*args, **kwargs)
	return wrapper
"""