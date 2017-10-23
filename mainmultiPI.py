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

from new_libs.videostream import VideoStream
from new_libs.videostream import FPS


from new_libs.semaforo import CreateSemaforo
from multiprocessing import Process, Queue, Pool
from new_libs.BackgroundsubCNT import CreateBGCNT

"""
from new_libs.pipeline import (
    PipelineRunner,
    CreateBGCNT,
    Filtering,
    FIFO,
    Save_to_Disk)

"""
# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-src", "--source", type=int or str, default=0,
	help="1 for PICAMERA and 0 for local source or video")

args = vars(ap.parse_args())


ENCODING = 'utf-8'



def create_main(fnt):

	data = np.load('./installationFiles/heroes.npy')
	fuente = ['./installationFiles/heroes.mp4', 0]
	#fuente = ['../trialVideos/mySquare.mp4', 0]
	print(data)
	semaforo = CreateSemaforo(periodoSemaforo = 0)
	poligono  = data[0]

	ON = True

	#height = 640
	#width = 480

	height = 3264
	width = 2448

	#bg = CreateBGCNT()
	vs = VideoStream(src = fuente[fnt], resolution = (height, width), poligono = poligono).start() # 0.5 pmx
	#vs = VideoStream(src = fuente[fnt], resolution = (height, width), poligono = poligono, draw=True).start() # 0.5 pmx
	#vs = WebcamVideoStream(src=src[1], height = 2048, width = 1536).start()	# 2 mpx
	#vs = WebcamVideoStream(src=src[1], height = 2560, width = 1920).start()	# 5 mpx
	#vs = WebcamVideoStream(src=src[1], height = 3264, width = 2448).start()
	fps = FPS().start()

	frame_number = -1
	_frame_number = -1
	#pipeline = PipelineRunner(pipeline=[CreateBGCNT(), Filtering(), FIFO(), Save_to_Disk()], log_level=logging.DEBUG)

	while ON:

		t5 = time.time()
		# grab the frame from the threaded video stream and resize it
		# in his core
		t1 = time.time()
		frame, frame_resized, imagen_semaforo,matches = vs.read()

		t2 = time.time()
		print('Producer took: ', t2-t1)

		_frame_number += 1

		t3 = time.time()
		# Get signals from the semaforo
		senalColor, colorLiteral, flancoSemaforo  = semaforo.obtenerColorEnSemaforo(imagen_semaforo)


		print(matches)
		t4 = time.time()

		
		print('sEMAForo took', t4-t3)
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
		
		
		t6 = time.time()
		print('alll the while took', t6-t5)

	
		#cv2.imshow('frame',cv2.resize(frame_resized,(640,480)))
		#cv2.imwrite('../frames/frame_{}.jpg'.format(frame_number), cv2.resize(frame_resized,(640,480)))
		#break
		if _frame_number == 1000:
			break

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
