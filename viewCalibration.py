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
anocheciendo =  17*60+15														# Tiempo 17:30 am + 4 GMT
amaneciendo = 8*60

saltarFrames = False
entradaReal = 'en tiempo real '													# Complementario
## Parametros semaforo
periodoDeSemaforo = 0
topeEjecucion = 0

tiempoAhora = datetime.datetime.now().hour*60 +datetime.datetime.now().minute

conVideoGrabado = False

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
	global tuveInfracciones
	tuveInfracciones = False

	print('Programa de visualizacion exitosamente con ingreso de senal video '+archivoDeVideo)
	# Si no existe el directorio de reporte lo creo
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
	indicesSemaforo = obtenerIndicesSemaforo(np.array(poligonoSemaforo))
	angulo = parametrosInstalacion[3]
	poligonoEnAlta = parametrosInstalacion[4]

	# Arrancando camara
	if len(archivoDeVideo) == 0:
		conVideoGrabado = False												# modo real
		miCamara = cv2.VideoCapture(0)
		miCamara.set(3,640)
		miCamara.set(4,480)
		time.sleep(1)
		print('Activada Exitosamente cámara en tiempo real')
	else:
		conVideoGrabado = True
		try:
			miCamara = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)
			time.sleep(1)
			print('Archivo de video cargado exitosamente: '+directorioDeVideos+'/'+archivoDeVideo)
		except Exception as currentException:
			print('No se pudo cargar el video por '+str(currentException))

	# Se captura la imagen de flujo inicial y se trabaja con la misma
	for descarte in range(50):
		ret, frameVideo = miCamara.read()
	cv2.imwrite(folderDeInstalacion+'/flujo.jpg',frameVideo)
	print('Generada Imagen de Instalacion')
	# Se captura para la cámara de Alta:
	try:
		miCamaraAlta = cv2.VideoCapture(1)
		miCamaraAlta.set(3,3280)
		miCamaraAlta.set(4,2464)
		ret, framePlaca = miCamaraAlta.read()
		cv2.imwrite(folderDeInstalacion+'/placa.jpg',framePlaca)
		print('Imagen de 8 Mp para instalacion capturada con exito')
	except:
		print('No se pudo capturar la imagen de 8 Mp')

	frameFlujo = cv2.resize(frameVideo,(320,240))
	miPoliciaReportando = PoliciaInfractor(frameFlujo,verticesPartida,verticesLlegada,8,directorioDeReporte,False)

	miSemaforo = CreateSemaforo(0)

	pixeles = np.array([frameVideo[indicesSemaforo[0][1],indicesSemaforo[0][0]]])
			
	for indiceSemaforo in indicesSemaforo[1:]:
		pixeles = np.append(pixeles,[frameVideo[indiceSemaforo[1],indiceSemaforo[0]]], axis=0)

	senalSemaforo, semaforoLiteral, flanco, periodo = miSemaforo.obtenerColorEnSemaforo(pixeles)
	tiempoAhora = datetime.datetime.now().hour*60 + datetime.datetime.now().minute
	
	miFiltro = IRSwitch()
	if (tiempoAhora > amaneciendo) & (tiempoAhora < anocheciendo) & ((miFiltro.ultimoEstado == 'Filtro Desactivado')|(miFiltro.ultimoEstado =='Inicializado')):
		miFiltro.colocarFiltroIR()
		print('Active Filtro'+ datetime.datetime.now().strftime('%H:%M:%S'))
	if ((tiempoAhora < amaneciendo) | (tiempoAhora > anocheciendo)) & ((miFiltro.ultimoEstado == 'Filtro Activado')|(miFiltro.ultimoEstado =='Inicializado')):
		miFiltro.quitarFiltroIR()
		print('Desactive Filtro')

	# Se introduce el acetato con el fin de determinar la calidad de la instalación actual
	miAcetatoInformativo = Acetato()
	miAcetatoInformativo.colocarPoligono(np.array(poligonoSemaforo)//2)
	miAcetatoInformativo.colocarPoligono(np.array(verticesPartida))
	miAcetatoInformativo.colocarPoligono(np.array(verticesLlegada))
	miAcetatoInformativo.colocarPoligono(miPoliciaReportando.areaFlujo)
	miAcetatoInformativo.colocarPoligono(miPoliciaReportando.carrilValido)
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
