import os
import sys
import cv2
import time
import psutil
import datetime
import numpy as np
from ownLibraries.irswitch import IRSwitch

directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'

date_string = datetime.datetime.now().strftime('%Y_%m_%d')

if not os.path.exists(directorioDeTrabajo+'/VideoCapture/'):
	os.makedirs(directorioDeTrabajo+'/VideoCapture/')

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
if resolucion == 5:
	width = 2592
	height = 1944
if resolucion == 1:
	width = 640
	height = 480
if resolucion == 0:
	width = 320
	height = 240


cam=cv2.VideoCapture(camaraAUsar)
cam.set(3,width)
cam.set(4,height)
miLista = []

while (1):
	ret0, image0=cam.read()
	miLista.append(image0)
	porcentajeDeMemoria = psutil.virtual_memory()[2]
	if porcentajeDeMemoria>90:
		miLista.pop(0)
		print('Alcanzado 90/100 de memoria con '+str(len(miLista))+' frames de '+str(len(resolucion))+'MP')

	ch = 0xFF & cv2.waitKey(5)
		#is_red = findColor()

	if ch == ord('q'):
		#print(myFlowMahine.velocidades)
		break
			
cv2.destroyAllWindows()
    
