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

from ownLibraries.irswitch import IRSwitch
from ownLibraries.mireporte import MiReporte
from ownLibraries.visualizacion import Acetato
from ownLibraries.herramientas import total_size
from ownLibraries.videostream import VideoStream
from ownLibraries.semaforov2 import CreateSemaforo
from ownLibraries.determinacionCruces import PoliciaInfractor

# Se crean las variables de directorios
directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeVideos  = os.getenv('HOME')+'/trafficFlow/trialVideos'
nombreCarpeta = datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
directorioDeReporte = os.getenv('HOME')+'/'+nombreCarpeta
folderDeInstalacion = directorioDeTrabajo+'/installationFiles'
# Archivos
reporteDiario = directorioDeReporte+'/reporteDiario.npy'

### PARAMETROS DE CONTROL DE EJECUCIÓN DE PROGRAMA
archivoDeVideo = ''
videofps = 30
mifps = 8
saltarFrames = False
entradaReal = 'en tiempo real '													# Complementario
## Parametros semaforo
periodoDeSemaforo = 0
topeEjecucion = 0
semaforoSimuladoTexto = 'real '

generarArchivosDebug = False
mostrarImagen = False
longitudRegistro = 360
font = cv2.FONT_HERSHEY_SIMPLEX

# Temporizaciones
anocheciendo =  17*60+15														# Tiempo 17:30 am + 4 GMT
amaneciendo = 7*60																# Tiempo  7:00 am + 4 GMT
tiempoAhora = datetime.datetime.now().hour*60 +datetime.datetime.now().minute
maximoMemoria = 200
conVideoGrabado = False

gamma = 1.0
noDraw = False

# Función principal

def obtenerIndicesSemaforo(poligono640):
	punto0 = poligono640[0]
	punto1 = poligono640[1]
	punto2 = poligono640[2]
	punto3 = poligono640[3]

	vectorHorizontal = punto3 - punto0
	vectorVertical = punto1 - punto0
	pasoHorizontal = vectorHorizontal/8
	pasoVertical = vectorVertical/24

	indices = []

	for j in range(24):
		for i in range(8):
			indices.append((punto0+i*pasoHorizontal+j*pasoVertical).tolist())
	#print('len of indices', len(indices))
	#print('single index', indices[0])
	indices = [[round(x[0]),round(x[1])] for x in indices]
	return indices

def __main_function__():
	# Import some global varialbes
	global archivoDeVideo
	global acaboDeIniciarNuevoCiclo
	acaboDeIniciarNuevoCiclo = False
	global tuveInfracciones
	tuveInfracciones = False

	# Creamos el reporte inicial
	miReporte = MiReporte(levelLogging=logging.INFO,nombre=__name__)			# Se crea por defecto con nombre de la fecha y hora actual
	miReporte.info('Programa iniciado exitosamente con ingreso de senal video '+archivoDeVideo+entradaReal+' con semaforo '+semaforoSimuladoTexto+str(periodoDeSemaforo) +', corriendo a '+str(mifps)+' Frames por Segundo')
	# Si no existe el directorio de reporte lo creo
	if not os.path.exists(directorioDeReporte):
		os.makedirs(directorioDeReporte)
	# Vector de inicio:
	# vector de inicio = [tiempo, periodo semaforo, cruce, giro, infraccion, otros]
	vectorDeInicio = [[datetime.datetime.now(),0,0,0,0,0]]
	if os.path.isfile(reporteDiario):
		miReporte.info('Continuando reporte')
		np.save(reporteDiario,np.append(np.load(reporteDiario),vectorDeInicio,0))
	else:
		miReporte.info('Creando reporte desde cero')
		np.save(reporteDiario,vectorDeInicio)
	
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
	indicesSemaforo = obtenerIndicesSemaforo(np.array(poligonoSemaforo))
	angulo = parametrosInstalacion[3]
	poligonoEnAlta = parametrosInstalacion[4]

	miReporte.info('Cargado exitosamente parametros de instalacion ')#+str(parametrosInstalacion))

	# Arrancando camara
	if len(archivoDeVideo) == 0:
		conVideoGrabado = False												# modo real
		miCamara = cv2.VideoCapture(0)
		miCamara.set(3,640)
		miCamara.set(4,480)
		time.sleep(1)
		miReporte.info('Activada Exitosamente cámara en tiempo real')
	else:
		conVideoGrabado = True
		try:
			miCamara = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)
			time.sleep(1)
			miReporte.info('Archivo de video cargado exitosamente: '+directorioDeVideos+'/'+archivoDeVideo)
		except Exception as currentException:
			miReporte.error('No se pudo cargar el video por '+str(currentException))

	# Se captura la imagen de flujo inicial y se trabaja con la misma
	ret, frameVideo = miCamara.read()
	frameFlujo = cv2.resize(frameVideo,(320,240))

	# Creación de objetos:
	if os.uname()[1] == 'raspberrypi':
		trabajoConPiCamara = True
	else:
		trabajoConPiCamara = False
	miPoliciaReportando = PoliciaInfractor(frameFlujo,verticesPartida,verticesLlegada,mifps,generarArchivosDebug)
	
	miFiltro = IRSwitch()
	miAcetatoInformativo = Acetato()
	miSemaforo = CreateSemaforo(periodoDeSemaforo)
	miAcetatoInformativo.colocarPoligono(np.array(poligonoSemaforo)//2)
	miAcetatoInformativo.colocarPoligono(np.array(verticesPartida))
	miAcetatoInformativo.colocarPoligono(np.array(verticesLlegada))
	miAcetatoInformativo.colocarPoligono(miPoliciaReportando.carrilValido)

	# El historial sera una lista de la siguiente forma:
	# {numeroFrame: {'frame':np.array((320,240)),'data':{"info"}}}
	global historial
	historial = {}
	frame_number  = 0
	tiempoAuxiliar = time.time()
	periodoDeMuestreo = 1.0/mifps
	grupo = [0]

		
	for i in range(20):
		ret, frameVideo = miCamara.read()

	pixeles = np.array([frameVideo[indicesSemaforo[0][1],indicesSemaforo[0][0]]])
			
	#print('IndicesPixel: ',indicesSemaforo[0][0],indicesSemaforo[0][1])
	#print('La longitud semaforo: ',len(indicesSemaforo),' inicial ',pixeles.shape)
	#print('La longitud interna: ',len(indicesSemaforo[0]),' inicial ',pixeles.shape)
	for indiceSemaforo in indicesSemaforo[1:]:
		pixeles = np.append(pixeles,[frameVideo[indiceSemaforo[1],indiceSemaforo[0]]], axis=0)
		
		#cv2.circle(frameVideo, (indiceSemaforo[0],indiceSemaforo[1]), 1, (100,100,100), -1)
	#print('Pixeles: ',pixeles)
	wtf = pixeles.reshape((24,8,3))
	#cv2.imshow('Semaforo', cv2.resize(wtf, (240,320)))
	#print('La longitud pixels: ',pixeles.shape)
	senalSemaforo, semaforoLiteral, flanco, periodo = miSemaforo.obtenerColorEnSemaforo(pixeles)
			
	
	frameFlujo = cv2.resize(frameVideo,(320,240))

	#ntoResguardo in miPoliciaReportando.obtenerLineasDeResguardo(False):
	miAcetatoInformativo.colocarObjeto(miPoliciaReportando.obtenerLineasDeResguardo(True),'Referencia')
	
	miAcetatoInformativo.colorDeSemaforo(senalSemaforo)

	frameFlujo = miAcetatoInformativo.aplicarAFrame(frameFlujo)
	
	cv2.imwrite(directorioDeReporte+'/view_{}.jpg'.format(datetime.datetime.now().strftime('%Y%m%d_%H%M')),frameFlujo)

if __name__ == '__main__':
	for input in sys.argv:

		if ('.mp4' in input)|('.avi' in input):
			archivoDeVideo = input
			entradaReal = ''
			saltarFrames = True

	__main_function__()
