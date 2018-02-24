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
import imutils
from new_libs.utilsforFPS import WebcamVideoStream
from new_libs.utilsforFPS import FPS

from new_libs.semaforo import CreateSemaforo
from new_libs.camPi import PiVideoStream
from multiprocessing import Process, Queue, Pool

from pipeline import (
    PipelineRunner,
    CreateBGCNT,
    Filtering,
    FIFO,
    Save_to_Disk)


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()

ap.add_argument("-d", "--display", type=int, default=1,
	help="Whether or not frames should be displayed")
args = vars(ap.parse_args())

print("[INFO] sampling THREADED frames from webcam...")


ENCODING = 'utf-8'




if __name__ == '__main__':

	data = np.load('./installationFiles/heroes.npy')
	print(data)
	semaforo = CreateSemaforo(periodoSemaforo = 10)
	poligono  = data[0]
	src = ['./installationFiles/mySquare.mp4', 0]
	#vs = WebcamVideoStream(src=src[0], height = 640, width = 480).start()
	#vs = WebcamVideoStream(src=src[1], height = 2048, width = 1536).start()
	#vs = WebcamVideoStream(src=src[1], height = 2592, width = 1944).start()
	#vs = WebcamVideoStream(src=src[1], height = 3266, width = 2450).start()
	

	fps = 30
	width = 3266
	height = 2450
	vflip = 1
	hflip = 1
	mins = 1


	vs = PiVideoStream(resolution=(width,height), framerate= 30).start()

	time.sleep(1.0)
	fps = FPS().start() 
	ON = True

	# loop over some frames...this time using the threaded stream
	log = logging.getLogger("mainmulti")


	frame_number = -1
	_frame_number = -1

	pipeline = PipelineRunner(pipeline=[CreateBGCNT(), Filtering(), FIFO(), Save_to_Disk()], log_level=logging.DEBUG)


	while ON:

		# grab the frame from the threaded video stream and resize it
		# in his core
		t1 = time.time()
		frame, frame_resized = vs.read()

		_frame_number += 1
		

		# Get signals from the semaforo
		senalColor, colorLiteral, flancoSemaforo  = semaforo.obtenerColorEnSemaforo(poligono = poligono, img = frame_resized)

		# skip every 2nd frame to speed up processing
		if _frame_number % 2 != 0:
			continue
		# frame number that will be passed to pipline
		# this needed to make video from cutted frames
		frame_number += 1

		print(colorLiteral)
		pipeline.load_data({
	        'frame_resized': frame_resized,
	        'frame_real': frame,
	   	    'state': colorLiteral,
	        'frame_number': frame_number,})
		pipeline.run()

		t4 = time.time()
		
		if _frame_number == 400:
			break
		t2 = time.time()

		print('alll the while took', t2-t1)
		# update the FPS counter
		fps.update()

	# stop the timer and display FPS information
	fps.stop()
	print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	 
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()

