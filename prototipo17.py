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

from multiprocessing import Queue
from multiprocessing import Process

from ownLibraries.irswitch import IRSwitch
from ownLibraries.mireporte import MiReporte
from ownLibraries.visualizacion import Acetato
from ownLibraries.herramientas import total_size
from ownLibraries.policiainfractor import PoliciaInfractor
from ownLibraries.generadorevidencia import GeneradorEvidencia
from ownLibraries.videostreamv2 import VideoStream
from ownLibraries.backgroundsub import BGSUBCNT

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
noDraw = False


def child_process_detect_objects_with_bg(input_q, output_q):
	while True:
		LRframe = input_q.get()
		print(LRframe.shape)
		poligonos_warp  = backgroundsub.feedbgsub(LRframe)
		output_q.put(poligonos_warp)


# Función principal
def __main_function__():
	# Import some global varialbes
	global archivoDeVideo
	global cambiosImportantes
	cambiosImportantes = False
	global numeroDeObjetos
	numeroDeObjetos = 0

	shapeUR = (3296,2512)
	shapeMR = (640,480)
	shapeLR = (160,120)

	# Creamos el reporte inicial
	miReporte = MiReporte(levelLogging=logging.INFO,nombre=__name__)			# Se crea por defecto con nombre de la fecha y hora actual
	miReporte.info('Programa iniciado exitosamente con ingreso de senal video '+archivoDeVideo+entradaReal+' con semaforo '+semaforoSimuladoTexto+str(periodoDeSemaforo) +', corriendo a '+str(mifps)+' Frames por Segundo')
	# Si no existe el directorio de reporte lo creo
	if not os.path.exists(directorioDeReporte):
		os.makedirs(directorioDeReporte) 
	
	# Is statements
	if generarArchivosDebug:
		miReporte.info('Generando Archivos de Debug')
	else:
		miReporte.info('Generando infracciones unicamente (No debug video)')
	
	# If mostrar Imagenes
	if mostrarImagen:
		miReporte.info('Pantalla de muestra de funcionamiento en tiempo real encendida')
	else:
		miReporte.info('Pantalla de muestra de funcionamiento en tiempo real apagada')

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
	miReporte.info('Datos de Instalacion de: '+folderDeInstalacion+'/'+archivoParametrosACargar)
	poligonoSemaforo = parametrosInstalacion[0]
	verticesPartida = parametrosInstalacion[1]
	verticesLlegada = parametrosInstalacion[2]
	angulo = parametrosInstalacion[3]

	miReporte.info('Cargado exitosamente parametros de instalacion: '+str(parametrosInstalacion))

	# Arrancando camara
	if len(archivoDeVideo) == 0:												# modo real
		if os.uname()[1] == 'alvarohurtado-305V4A':
			miCamara = VideoStream(src = 0, resolution = shapeMR).start()
			time.sleep(1)
		elif os.uname()[1] == 'stanlee321-MS-7693':
			print('Hello stanlee321')
			miCamara = VideoStream(src = 0, resolution = shapeMR).start()
		else:
			miCamara = VideoStream(src = 0, resolution = shapeUR).start()
		miReporte.info('Activada Exitosamente cámara en tiempo real')
	else:
		try:
			miCamara = miCamara = VideoStream(src = directorioDeVideos+'/'+archivoDeVideo, resolution = shapeMR).start()
			miReporte.info('Archivo de video cargado exitosamente: '+directorioDeVideos+'/'+archivoDeVideo)
		except Exception as currentException:
			miReporte.error('No se pudo cargar el video por '+str(currentException))

	# Se captura la imagen de flujo inicial y se trabaja con la misma
	data = miCamara.read()

	capturaEnBaja =  data['LRframe']
	# Creación de objetos:
	miPoliciaReportando = PoliciaInfractor( capturaEnBaja, verticesPartida, verticesLlegada)
	miGrabadora = GeneradorEvidencia(directorioDeReporte,mifps,guardarRecortados)
	miFiltro = IRSwitch()
	miAcetatoInformativo = Acetato()
	miAcetatoInformativo.colocarPoligono(np.array(poligonoSemaforo)//2)
	miAcetatoInformativo.colocarPoligono(np.array(verticesPartida))
	miAcetatoInformativo.colocarPoligono(np.array(verticesLlegada))	

	frame_number  = 0
	tiempoAuxiliar = time.time()
	periodoDeMuestreo = 1.0/mifps
	periodoReal = time.time()


	# Create BGSUBCNT object
	backgroundsub = BGSUBCNT()

	# Create Multiprocessing parameters
	#input_q = Queue(5)
	#output_q = Queue(5)

	#child_process = Process(target = child_process_detect_objects_with_bg, args=(input_q, output_q))
	#child_process.daemon = True
	#child_process.start()

	while True:
		tiempoAuxiliar = time.time()
		data = miCamara.read()

		capturaEnAlta = data['HRframe']
		capturaEnBaja = data['LRframe']

		print('Lectura: ',time.time()-tiempoAuxiliar)
		
		tiempoAuxiliar = time.time()
		#feed data to queues
		#input_q.put(capturaEnBaja)
		#poligonos_warp = output_q.get()
		poligonos_warp  = backgroundsub.feedbgsub(capturaEnBaja)
		print(poligonos_warp)
		#print('Put: ',time.time()-tiempoAuxiliar)
		#if mostrarImagen:
		#	tiempoAuxiliar = time.time()
		#	cv2.imshow('Camara',capturaEnBaja)
		#	print('Show: ',time.time()-tiempoAuxiliar)

		print('Periodo total: ',time.time()-periodoReal)
		periodoReal = time.time()

		#tiempoAuxiliar = time.time()
		#if filaImagenes.qsize() > 10:
		#miImagen = filaImagenes.get()
		#	print('Borrado elemento en la fila')
		#print('Get: ',time.time()-tiempoAuxiliar)
		if frame_number>100:
			break
		frame_number +=1
		
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por salida manual')
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
		if input =='Kill':
			topeEjecucion = int(input[:-1])
		if 'gamma' in input:
			gamma = float(input[:-5])
		if input == 'noRec':
			guardarRecortados = False
		if input == 'noDraw':
			noDraw = True

	__main_function__()