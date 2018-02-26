import os
import sys
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np
import time
import datetime

directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeLibreriasPropias = directorioDeTrabajo +'/ownLibraries'

sys.path.insert(0, directorioDeLibreriasPropias)
from irswitch import IRSwitch

date_string = datetime.datetime.now().strftime('%Y_%m_%d')

if not os.path.exists('./VideoCapture/'):
	os.makedirs('./VideoCapture/')

try:
	camaraAUsar = int(sys.arg[2])
except:
	print('No se introdujo cambio de camara, usando la primera, 0, por defecto')
	camaraAUsar = 1

try:
	resolucion = int(sys.arg[1])
except:
	print('No se introdujo resolucion, usando la maxima, 8Mp, por defecto')
	resolucion = 5

factorDeInteres = 5

if resolucion == 8:
	width = 3280
	height = 2464
	wid5 = 2592
	hei5 = 1944
else:
	width = 3280   #640
	height = 2464  #480
	wid5 = 2592 	#320
	hei5 = 1944

xMin = int(2/5*width)
xMax = int(3/5*width)
yMin = int(2/5*height)
yMax = int(3/5*height)

xMin5 = int(2/5*wid5)
xMax5 = int(3/5*wid5)
yMin5 = int(2/5*hei5)
yMax5 = int(3/5*hei5)


# load the filter driver

miFiltro = IRSwitch(55)
miFiltro.quitarFiltroIR()


# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (3280, 2464)
camera.framerate = 2
rawCapture = PiRGBArray(camera, size=(3280, 2464))

# allow the camera to warmup
time.sleep(0.1)

#while True:
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image0 = frame.array
	# Genero la visualizacion:
	#cv2.imshow('PiCam',cv2.resize(image0,(320,240)))
	cv2.imshow('PiCam',  image0)
	cv2.imshow('Aumento',image0[yMin:yMax,xMin:xMax])

	ch = 0xFF & cv2.waitKey(5)
		#is_red = findColor()
	if ch == ord('s'):
		date_string = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
		cv2.imwrite('./VideoCapture/' + date_string + '_sinFiltro.png',image0)
		cv2.imwrite('./VideoCapture/' + date_string + '_ROIsinFiltro.png',image0[yMin:yMax,xMin:xMax])
		miFiltro.colocarFiltroIR()
		image1  = image0
		cv2.imwrite('./VideoCapture/' + date_string + '_conFiltro.png',image1)
		cv2.imwrite('./VideoCapture/' + date_string + '_ROIconFiltro.png',image1[yMin:yMax,xMin:xMax])
		cv2.imshow('Aumento',image1[yMin:yMax,xMin:xMax])
		#cam.set(3,wid5)
		#cam.set(4,hei5)
		image2 = image0
		#cv2.imwrite('./VideoCapture/' + date_string + '_a5mpConFiltro.png',image2)
		cv2.imwrite('./VideoCapture/' + date_string + '_ROIa5mpConFiltro.png',image2[yMin5:yMax5,xMin5:xMax5])
		#cv2.imwrite('./VideoCapture/' + date_string + '_zinFiltro.png',image0)		
		print('captured frame at: '+ date_string)
		#miFiltro.quitarFiltroIR()
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)
	if ch == ord('q'):
		#print(myFlowMahine.velocidades)
		break	
	if ch == ord('c'):
		print('activando')
		miFiltro.colocarFiltroIR()
	if ch == ord('r'):
		print('desactivando')
		miFiltro.quitarFiltroIR()
		
			
cv2.destroyAllWindows()
    
