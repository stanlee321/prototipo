import os
import sys
import cv2
import time
import datetime
import numpy as np

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
	camaraAUsar = 0

try:
	resolucion = int(sys.arg[1])
except:
	print('No se introdujo resolucion, usando la maxima, 8Mp, por defecto')
	resolucion = 8

factorDeInteres = 5

if resolucion == 8:
	width = 3280
	height = 2464
else:
	width = 640
	height = 480

xMin = int(2/5*width)
xMax = int(3/5*width)
yMin = int(2/5*height)
yMax = int(3/5*height)

cam=cv2.VideoCapture(camaraAUsar)
cam.set(3,width)
cam.set(4,height)

miFiltro = IRSwitch()




while (1):
	# Establezco las configuraciones iniciales
	miFiltro.quitarFiltroIR()
	cam.set(3,3280)
	cam.set(4,2464)
	# Leo el frame de prueba
	ret0, image0=cam.read()
	# Genero la visualizacion:
	cv2.imshow('PiCam',cv2.resize(image0,(320,240)))
	cv2.imshow('Aumento',image0[yMin:yMax,xMin:xMax])

	ch = 0xFF & cv2.waitKey(5)
		#is_red = findColor()
	if ch == ord('s'):
		date_string = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
		cv2.imwrite('./VideoCapture/' + date_string + '_sinFiltro.jpg',image0)
		miFiltro.colocarFiltroIR()
		ret0, image1=cam.read()
		cv2.imwrite('./VideoCapture/' + date_string + '_conFiltro.jpg',image1)
		cam.set(3,2592)
		cam.set(4,1944)
		ret0, image2=cam.read()
		cv2.imwrite('./VideoCapture/' + date_string + '_a5mp.jpg',image2)
		print('captured frame at: '+ date_string)

	if ch == ord('q'):
		#print(myFlowMahine.velocidades)
		break
cv2.destroyAllWindows()
    
