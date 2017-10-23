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

<<<<<<< HEAD
	data = np.load('./installationFiles/heroes.npy')
	fuente = ['./installationFiles/heroes.mp4', 0]
	#fuente = ['../trialVideos/mySquare.mp4', 0]
=======
	data = np.load('./installationFiles/mySquare.npy')
	fuente = ['./installationFiles/mySquare.mp4', 0]
>>>>>>> 5bb557a5944f673fbd51a77f744499f529c97340
	print(data)
	semaforo = CreateSemaforo(periodoSemaforo = 0)
	poligono  = data[0]

	ON = True

<<<<<<< HEAD
	#height = 640
	#width = 480

	height = 3264
	width = 2448

	#bg = CreateBGCNT()
	vs = VideoStream(src = fuente[fnt], resolution = (height, width), poligono = poligono, draw=True).start() # 0.5 pmx
	#vs = VideoStream(src = fuente[fnt], resolution = (height, width), poligono = poligono, draw=True).start() # 0.5 pmx
=======
	height = 640
	width = 480

	#bg = CreateBGCNT()
	vs = VideoStream(src = fuente[fnt], resolution = (height, width), poligono = poligono).start() # 0.5 pmx
>>>>>>> 5bb557a5944f673fbd51a77f744499f529c97340
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
<<<<<<< HEAD
		frame, frame_resized, imagen_semaforo, matches = vs.read()
=======
		frame, frame_resized, imagen_semaforo = vs.read()
>>>>>>> 5bb557a5944f673fbd51a77f744499f529c97340

		t2 = time.time()
		print('Producer took: ', t2-t1)

		_frame_number += 1

		t3 = time.time()
		# Get signals from the semaforo
<<<<<<< HEAD
		senalColor, colorLiteral, flancoSemaforo  = semaforo.obtenerColorEnSemaforo(imagen_semaforo)


		print(matches)
=======
		#senalColor, colorLiteral, flancoSemaforo  = semaforo.obtenerColorEnSemaforo(poligono = poligono, img = frame_resized)
		senalColor, colorLiteral, flancoSemaforo  = semaforo.obtenerColorEnSemaforo(imagen_semaforo)

>>>>>>> 5bb557a5944f673fbd51a77f744499f529c97340
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
		
<<<<<<< HEAD
		
		t6 = time.time()
		print('alll the while took', t6-t5)

		cv2.imshow('frame',frame_resized)

		#cv2.imshow('frame',cv2.resize(frame_resized,(640,480)))
		#cv2.imwrite('../frames/frame_{}.jpg'.format(frame_number), cv2.resize(frame_resized,(640,480)))
		#break
		#if _frame_number == 1000:
		#	break

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

=======
		#bg.draw()
		
		t6 = time.time()

		print('alll the while took', t6-t5)
		# update the FPS counter
		#print(poligono)
		#x,y,w,h = poligono[0][0],poligono[1],poligono[2],poligono[3]

		"""
		x1,x2,x3,x4 = poligono

		#print(x1,x2,x3,x4)

		x = x1[0]//2
		y = x1[1]//2

		w = x3[0]//2
		h = x3[1]//2
		
		cv2.rectangle(frame_resized, (x,y),(w-1, h-1),(0,0,255),1)

		cv2.circle(frame_resized, (x,y),2,(0,255,0),-1)
		cv2.circle(frame_resized, (w,h),2,(0,255,255),-1)
		#cv2.circle(frame_resized, poligono[2],2,(0,255,0),-1)
		#cv2.circle(frame_resized, poligono[3],2,(0,255,0),-1)

		"""


		#cv2.imshow('frame', cv2.resize(frame_resized,(640,480)))
		#cv2.imwrite('frame.jpg', cv2.resize(frame_resized,(640,480)))
		#break
		if _frame_number == 2500:
			break

		#if cv2.waitKey(1) & 0xFF == ord('q'):
		#	break

>>>>>>> 5bb557a5944f673fbd51a77f744499f529c97340
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
