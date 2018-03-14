"""
This new prototipe includes huge improvements in flow detection and image capture for the raspberry pi 
"""
import os
import sys
import cv2
import time
import psutil
import logging
import datetime
import numpy as np

from ownLibraries.videostreamv5 import FPS
from ownLibraries.videostreamv5 import VideoStream

# Se crean las variables de directorios
directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeVideos  = os.getenv('HOME')+'/trafficFlow/trialVideos'
directorioDeReporte = os.getenv('HOME')+'/casosReportados'
folderDeInstalacion = directorioDeTrabajo+'/installationFiles'

### PARAMETROS DE CONTROL DE EJECUCIÓN DE PROGRAMA
archivoDeVideo = ''
videofps = 30
mifps = 10
saltarFrames = False
entradaReal = 'en tiempo real '													# Complementario
## Parametros semaforo
periodoDeSemaforo = 0
topeEjecucion = 0
semaforoSimuladoTexto = 'real '

generarArchivosDebug = True
mostrarImagen = False
longitudRegistro = 360
font = cv2.FONT_HERSHEY_SIMPLEX

# Temporizaciones
anocheciendo =  21*60+30														# Tiempo 17:30 am + 4 GMT
amaneciendo = 11*60																# Tiempo  7:00 am + 4 GMT
tiempoAhora = datetime.datetime.now().hour*60 +datetime.datetime.now().minute
maximoMemoria = 200
guardarRecortados = True

gamma = 1.0

# Función principal
def __main_function__():
	# Import some global varialbes
	global archivoDeVideo
	global cambiosImportantes
	cambiosImportantes = False
	global numeroDeObjetos
	numeroDeObjetos = 0

	# Creamos el reporte inicial

	if not os.path.exists(directorioDeReporte):
		os.makedirs(directorioDeReporte) 
	
	# El directorio de reporte debe crearse al inicio del programa
	# Variables de control:
	
	numeroDeFrame = 0
	maximoInfraccionesPorFrame = 20
	#colores = np.random.randint(0,100,(maximoInfraccionesPorFrame,3))

	# Cargando los parametros de instalacion:
	# El archivo de video debe tener como minimo 5 caracteres para estar trnajando en modo simulado, de lo contrario estamos trabajando en modo real
	if len(archivoDeVideo) > 4:
		archivoParametrosACargar = archivoDeVideo[:-4]+'.npy'
	else:
		archivoParametrosACargar = 'datos.npy'
	
	parametrosInstalacion = np.load(folderDeInstalacion+'/'+archivoParametrosACargar)
	poligonoSemaforo = parametrosInstalacion[0]
	verticesPartida = parametrosInstalacion[1]
	verticesLlegada = parametrosInstalacion[2]
	angulo = parametrosInstalacion[3]

	# Arrancando camara
	if len(archivoDeVideo) == 0:												# modo real
		miCamara = VideoStream(src = 0, resolution = (3296,2512),poligono = poligonoSemaforo, debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma).start()
		#miCamara = VideoStream(src = 0, resolution = (1920,1080),poligono = poligonoSemaforo, debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma).start()
		#miCamara = VideoStream(src = 0, resolution = (1280,960),poligono = poligonoSemaforo, debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma).start()
		time.sleep(1)

		
	else:
		try:
			miCamara = VideoStream(src = directorioDeVideos+'/'+archivoDeVideo, resolution = (640,480),poligono = poligonoSemaforo,debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma).start()
			time.sleep(1)
		
		except Exception as currentException:
			print('ERRORMI. O',currentException)
	frame_number = 0

	while True:
		# LEEMOS LA CAMARA DE FLUJO
		
		# Ways to access to the information 

		# information['frame'] ; numpy array containing the low res frame 
		# information['semaforo'] ; list like [self.senalColor, self.colorLiteral, self.flancoSemaforo]
		# information['recortados'] ; list like of tuples  representing listaderecortados from hd frame [(_numpy arrays_)n+1]
		# information['rectangulos'] ; list like of tuples  representing listaderectangulos and centroids in frame [((x,y,h,w),(p1,p2))n+1]
		# n+1 ; represent the 1 by 1 correspndencia de los rectangulos encontrados y imagenes recortadas
		
		informacion = miCamara.read() # Ways to access

		# Asign number rfame to the information from miCamara.read()		
		
		cv2.imshow('Visual', informacion['frame'])
		frame_number+=1
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break

if __name__ == '__main__':
	# Tomamos los ingresos para controlar el video
	for input in sys.argv:
		if input == 'NoDebug':
			generarArchivosDebug = False
		if ('.mp4' in input)|('.avi' in input):
			archivoDeVideo = input
			entradaReal = ''
			saltarFrames = True
		if 'seg' in input:
			periodoDeSemaforo = int(input[:-3])
			semaforoSimuladoTexto = 'simulado a '
		if input == 'Show':
			mostrarImagen = True
		if 'fps' in input:
			mifps = int(input[:-3])
		if 'd' in input:
			topeEjecucion = int(input[:-1])
		if 'gamma' in input:
			gamma = float(input[:-5])
		if 'norec' in input:
			guardarRecortados = False

	__main_function__()