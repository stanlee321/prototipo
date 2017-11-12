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
from multiprocessing import Process, Queue, Value

from ownLibraries.irswitch import IRSwitch
from ownLibraries.mireporte import MiReporte
from ownLibraries.visualizacion import Acetato
from ownLibraries.herramientas import total_size
from ownLibraries.policiainfractor import PoliciaInfractor
from ownLibraries.generadorevidencia import GeneradorEvidencia
from ownLibraries.backgroundsub import BGSUBCNT
from ownLibraries.cutHDImage import cutHDImage
from ownLibraries.semaforo import CreateSemaforo

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
estadoDeEjecucionDePrograma = Value('i',1)

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
	shapeLR = (320,240)

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
			miCamara = cv2.VideoCapture(1)
		else:
			miCamara = cv2.VideoCapture(0)
			miCamara.set(3,3280)
			miCamara.set(4,2464)
			#miCamara.set(3,2592)
			#miCamara.set(4,1944)
		miReporte.info('Activada Exitosamente cámara en tiempo real')
	else:
		try:
			miCamara = miCamara = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)
			miReporte.info('Archivo de video cargado exitosamente: '+directorioDeVideos+'/'+archivoDeVideo)
		except Exception as currentException:
			miReporte.error('No se pudo cargar el video por '+str(currentException))

	# Se captura la imagen de flujo inicial y se trabaja con la misma
	ret, capturaEnAlta = miCamara.read() 
	capturaEnBaja =  cv2.resize(capturaEnAlta,(320,240))

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

	# Create Semaphro
	periodo = 0
	semaforo = CreateSemaforo(periodoSemaforo = periodo)
	periodoReal = time.time()

	### HERRAMIENTAS MULTIPROCESSING:
	imagenes = Queue()
	procesoDeAcondicionado = Process(name = 'Acondicionado',target = procesoAcondicionado,args = (imagenes,estadoDeEjecucionDePrograma))
	procesoDeAcondicionado.start()
	while True:
		tiempoAuxiliar = time.time()
		ret, capturaEnAlta = miCamara.read() 
		print('0 Tiempo de captura: ',time.time()-tiempoAuxiliar)
		tiempoAuxiliar = time.time()
		capturaEnBaja =  cv2.resize(capturaEnAlta,(320,240))
		print('0 Tiempo de Resize: ',time.time()-tiempoAuxiliar)
		tiempoAuxiliar = time.time()
		imagenes.put(capturaEnBaja)
		print('0 Tiempo de Colocado: ',time.time()-tiempoAuxiliar)

		#print('Put: ',time.time()-tiempoAuxiliar)
		if mostrarImagen:
			tiempoAuxiliar = time.time()
			cv2.imshow('Camara', capturaEnBaja)
			print('0 Show: ',time.time()-tiempoAuxiliar)

		print('0 Periodo total: ',time.time()-periodoReal)
		periodoReal = time.time()

		frame_number +=1
		
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por salida manual')
			estadoDeEjecucionDePrograma.value = 0
			procesoDeAcondicionado.join()
			break

def procesoAcondicionado(fila,estado):
	#En este proceso simplemente imprimimos el numero de Queue y en caso de ser muy elevado los eliminamos
	while estado.value == 1:
		tiempoAuxiliarEnProceso = time.time()
		numero = fila.qsize()
		if numero <= 12:
			continue
		else:
			print('1 La fila tiene: ',numero,' tiempo: ',time.time()-tiempoAuxiliarEnProceso)
			tiempoAuxiliarEnProceso = time.time()
			variableLeida = fila.get()
			print('Dimensiones recibidas: ',variableLeida.shape)
			print('1 Tiempo de lectura: ', time.time()-tiempoAuxiliarEnProceso)
	else:
		print('Salida externa del while en el processo interno')
	
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