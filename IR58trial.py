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
	width = 640
	height = 480
	wid5 = 320
	hei5 = 240

xMin = int(2/5*width)
xMax = int(3/5*width)
yMin = int(2/5*height)
yMax = int(3/5*height)

xMin5 = int(2/5*wid5)
xMax5 = int(3/5*wid5)
yMin5 = int(2/5*hei5)
yMax5 = int(3/5*hei5)

cam=cv2.VideoCapture(camaraAUsar)
cam.set(3,width)
cam.set(4,height)

miFiltro = IRSwitch(55)
miFiltro.quitarFiltroIR()

while (1):
	# Establezco las configuraciones iniciales
	
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
		cv2.imwrite('./VideoCapture/' + date_string + '_sinFiltro.png',image0)
		cv2.imwrite('./VideoCapture/' + date_string + '_ROIsinFiltro.png',image0[yMin:yMax,xMin:xMax])
		miFiltro.colocarFiltroIR()
		ret0, image1=cam.read()
		cv2.imwrite('./VideoCapture/' + date_string + '_conFiltro.png',image1)
		cv2.imwrite('./VideoCapture/' + date_string + '_ROIconFiltro.png',image1[yMin:yMax,xMin:xMax])
		cv2.imshow('Aumento',image1[yMin:yMax,xMin:xMax])
		cam.set(3,wid5)
		cam.set(4,hei5)
		ret0, image2=cam.read()
		#cv2.imwrite('./VideoCapture/' + date_string + '_a5mpConFiltro.png',image2)
		cv2.imwrite('./VideoCapture/' + date_string + '_ROIa5mpConFiltro.png',image2[yMin5:yMax5,xMin5:xMax5])
		#cv2.imwrite('./VideoCapture/' + date_string + '_zinFiltro.png',image0)		
		print('captured frame at: '+ date_string)
		miFiltro.quitarFiltroIR()

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
    
