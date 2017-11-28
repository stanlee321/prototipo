import numpy as np 
import cv2
import sys
size=0.9
if sys.argv[1] == 'picam':
	cap=cv2.VideoCapture(1)
	cont=0
	while(1):
		ret,frame=cap.read()
		mensaje='Picamera puerto(1)'
		cv2.putText(frame, mensaje, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,size, (0, 0, 255), 2)
		cv2.imshow('frame',frame)
		if cv2.waitKey(1) & 0xFF == ord("s"):
			cv2.imwrite('/home/pi/trafficFlow/imagen_Picam_{}.jpg'.format(cont),frame)
			print('saved_'+str(cont))
			cont=cont+1
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break
if sys.argv[1] == 'webcam':
	cap=cv2.VideoCapture(0)
	cont=0
	while(1):
		ret,frame=cap.read()
		mensaje='WebCam puerto(0)'
		cv2.putText(frame, mensaje, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,size, (0, 0, 255), 2)
		cv2.imshow('frame',frame)
		if cv2.waitKey(1) & 0xFF == ord("s"):
			cv2.imwrite('/home/pi/trafficFlow/imagen_Webcam_{}.jpg'.format(cont),frame)
			print('saved_'+str(cont))
			cont=cont+1
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break
if sys.argv[1] == 'ambas':
	pi=cv2.VideoCapture(1)
	cam=cv2.VideoCapture(0)
	cont=0
	while(1):
		ret,frame=cam.read()
		ret,frame2=pi.read()
		mensaje='WebCam puerto(0)'
		mensaje2='PiCamera puerto(1)'
		cv2.putText(frame, mensaje, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,size, (0, 0, 255), 2)
		cv2.putText(frame2, mensaje2, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,size, (0, 0, 255), 2)
		cv2.imshow('frame',frame)
		cv2.imshow('frame2',frame2)
		if cv2.waitKey(1) & 0xFF == ord("s"):
			cv2.imwrite('/home/pi/trafficFlow/imagen_Webcam_{}.jpg'.format(cont),frame)
			cv2.imwrite('/home/pi/trafficFlow/imagen_Picam_{}.jpg'.format(cont),frame2)
			print('saved_'+str(cont))
			cont=cont+1
		if cv2.waitKey(1) & 0xFF == ord("q"):
			break
cv2.destroyAllWindows()
