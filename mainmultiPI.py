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
from multiprocessing import Process, Queue, Pool

from new_libs.pipeline import (
    PipelineRunner,
    CreateBGCNT,
    Filtering,
    FIFO,
    Save_to_Disk)


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-src", "--source", type=int, default=0,
	help="1 for PICAMERA and 0 for local source or video")

args = vars(ap.parse_args())


ENCODING = 'utf-8'


def create_main(src):

	data = np.load('./installationFiles/heroes.npy')
	print(data)
	semaforo = CreateSemaforo(periodoSemaforo = 10)
	poligono  = data[0]

	ON = True

	if src == 0:
		fuente = ['./installationFiles/heroes.mp4', 0]
		vs = WebcamVideoStream(src=fuente[0], height = 640, width = 480).start() # 0.5 pmx
		#vs = WebcamVideoStream(src=src[1], height = 2048, width = 1536).start()	# 2 mpx
		#vs = WebcamVideoStream(src=src[1], height = 2560, width = 1920).start()	# 5 mpx
		#vs = WebcamVideoStream(src=src[1], height = 3264, width = 2448).start()
		fps = FPS().start()

		frame_number = -1
		_frame_number = -1
		pipeline = PipelineRunner(pipeline=[CreateBGCNT(), Filtering(), FIFO(), Save_to_Disk()], log_level=logging.DEBUG)


	elif src == 1:

		from new_libs.camPi import PiVideoStream

		framerate = 16

		#width = 2048
		#height = 1536

		width = 2240
		height = 1680 

		width_low = 320
		height_low = 240

		vflip = 1
		hflip = 1
		mins = 1
		vs = PiVideoStream(resolution=(width,height), framerate = framerate).start()

		time.sleep(1.0)
		fps = FPS().start() 

		log = logging.getLogger("mainmulti")

		frame_number = -1
		_frame_number = -1

		resolution_hight = width*height

		resolution_low = width_low*height_low

		scale = resolution_hight/resolution_low
		print('SCALE', scale)

		Filtering.scale =  scale 

		pipeline = PipelineRunner(pipeline=[CreateBGCNT(), Filtering(), FIFO(), Save_to_Disk()], log_level=logging.DEBUG)
	else:
		print('please put:  0 for local source or 1 for PicamSource')

	while ON:

		# grab the frame from the threaded video stream and resize it
		# in his core
		t1 = time.time()
		frame, frame_resized = vs.read()
		#print(frame.shape,frame_resized.shape)


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
		
		"""
		pipeline.load_data({
	        'frame_resized': frame_resized,
	        'frame_real': frame,
	   	    'state': colorLiteral,
	        'frame_number': frame_number,})
		pipeline.run()
		"""
		

		#if _frame_number == 400:
		#	break
		t2 = time.time()

		print('alll the while took', t2-t1)
		# update the FPS counter
		
		cv2.imshow('frame', frame_resized)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

		fps.update()

	# stop the timer and display FPS information
	fps.stop()
	print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	 
	# do a bit of cleanup
	cv2.destroyAllWindows()
	vs.stop()

if __name__ == '__main__':

	create_main(args['source'])
