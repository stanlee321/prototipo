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

from ownLibraries.videostream import FPS
from ownLibraries.irswitch import IRSwitch
from ownLibraries.mireporte import MiReporte
from ownLibraries.visualizacion import Acetato
from ownLibraries.herramientas import total_size
from ownLibraries.videostream import VideoStream
from ownLibraries.semaforov2 import CreateSemaforo
from ownLibraries.policiainfractor import PoliciaInfractor
from ownLibraries.generadorevidenciasimple import GeneradorEvidencia

# Se crean las variables de directorios
directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeVideos  = os.getenv('HOME')+'/trafficFlow/trialVideos'
directorioDeReporte = os.getenv('HOME')+'/casosReportados'
folderDeInstalacion = directorioDeTrabajo+'/installationFiles'

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

generarArchivosDebug = True
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
	global cambiosImportantes
	cambiosImportantes = False

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
	indicesSemaforo = obtenerIndicesSemaforo(np.array(poligonoSemaforo))
	angulo = parametrosInstalacion[3]
	poligonoEnAlta = parametrosInstalacion[4]

	miReporte.info('Cargado exitosamente parametros de instalacion: '+str(parametrosInstalacion))

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
	miPoliciaReportando = PoliciaInfractor(frameFlujo,verticesPartida,verticesLlegada,True)
	miPoliciaReportando.establecerRegionInteresAlta(poligonoEnAlta)
	miGrabadora = GeneradorEvidencia(directorioDeReporte,mifps,False)
	miFiltro = IRSwitch()
	miAcetatoInformativo = Acetato()
	miSemaforo = CreateSemaforo(periodoDeSemaforo)
	miAcetatoInformativo.colocarPoligono(np.array(poligonoSemaforo)//2)
	miAcetatoInformativo.colocarPoligono(np.array(verticesPartida))
	miAcetatoInformativo.colocarPoligono(np.array(verticesLlegada))	

	informacionTotal = {}
	frame_number  = 0
	tiempoAuxiliar = time.time()
	periodoDeMuestreo = 1.0/mifps
	grupo = [0]

	try: 
		while True:
			# LEEMOS LA CAMARA DE FLUJO
			if conVideoGrabado:
				for i in range(videofps//mifps):
					ret, frameVideo = miCamara.read()
			else:
				ret, frameVideo = miCamara.read()
			
			pixeles = np.array([frameVideo[indicesSemaforo[0][1],indicesSemaforo[0][0]]])

			#print('IndicesPixel: ',indicesSemaforo[0][0],indicesSemaforo[0][1])
			#print('La longitud semaforo: ',len(indicesSemaforo),' inicial ',pixeles.shape)
			#print('La longitud interna: ',len(indicesSemaforo[0]),' inicial ',pixeles.shape)
			for indiceSemaforo in indicesSemaforo[1:]:
				pixeles = np.append(pixeles,[frameVideo[indiceSemaforo[1],indiceSemaforo[0]]], axis=0)
				#print('>>> ',pixeles.shape,' in ',indiceSemaforo)
				#cv2.circle(frameVideo, (indiceSemaforo[0],indiceSemaforo[1]), 1, (100,100,100), -1)
			#print('Pixeles: ',pixeles)
			wtf = pixeles.reshape((24,8,3))
			#cv2.imshow('Semaforo', cv2.resize(wtf, (240,320)))
			#print('La longitud pixels: ',pixeles.shape)
			senalSemaforo, semaforoLiteral, flanco, periodo = miSemaforo.obtenerColorEnSemaforo(pixeles)
			frameFlujo = cv2.resize(frameVideo,(320,240))

			if periodo != 0:
				miReporte.info('SEMAFORO EN VERDE, EL PERIODO ES '+str(periodo))
			else:
				pass
			# Si tengo infracciones pendientes las evoluciono
			cambiosImportantes, ondaFiltrada, frenteAutomovil, flujoTotal = miPoliciaReportando.seguirImagen(frame_number,frameFlujo,colorSemaforo = senalSemaforo)
			if senalSemaforo >= 1 :							# Si estamos en rojo, realizamos una accion
				if flanco == 1:							# esto se inicia al principio de este estado
					miReporte.info('SEMAFORO EN ROJO')
					del informacionTotal
					informacionTotal = {}
					frame_number = 0
				else:
					pass			
			else:
				pass

			if senalSemaforo == 0:							# Si estamos en verde realizamos otra accion
				if flanco == -1:					# Si estamos en verde y en flanco, primer verde, realizamos algo
					miReporte.info('Infracciones: '+str(miPoliciaReportando.numeroInfraccionesConfirmadas()))
					if generarArchivosDebug:
						miGrabadora.generarReporteInfraccion(informacionTotal, False,miPoliciaReportando.numeroInfraccionesConfirmadas())
					miPoliciaReportando.purgeInfractions()					
				if miPoliciaReportando.numeroInfraccionesConfirmadas() > 0:
					infraccionEnRevision = miPoliciaReportando.popInfraccion()
					miGrabadora.generarReporteInfraccion(informacionTotal, infraccionEnRevision)
				else:
					#Si no hay infracciones a reportar me fijo el estado del filtro:
					tiempoAhora = datetime.datetime.now().hour*60 + datetime.datetime.now().minute
					if (tiempoAhora > amaneciendo) & (miFiltro.ultimoEstado != 'Filtro Activado'):
						miFiltro.colocarFiltroIR()
					if (tiempoAhora < amaneciendo) & (miFiltro.ultimoEstado != 'Filtro Desactivado'):
						miFiltro.quitarFiltroIR()
				pass

			# Draw frame number into image on top
			for infraction in miPoliciaReportando.listaDeInfracciones:
				for puntos in infraction['desplazamiento']:
					puntosExtraidos = puntos.ravel().reshape(puntos.ravel().shape[0]//2,2)
					for punto in puntosExtraidos:
						if infraction['estado'] == 'Confirmado':
							miAcetatoInformativo.colocarPunto(tuple(punto),0)
						else:
							miAcetatoInformativo.colocarPunto(tuple(punto),1)

			# Configs and displays for the MASK according to the semaforo
			#miAcetatoInformativo.agregarTextoEn("I{}".format(miPoliciaReportando.infraccionesConfirmadas), 2)
			
			miAcetatoInformativo.colorDeSemaforo(senalSemaforo)

			frameFlujo = miAcetatoInformativo.aplicarAFrame(frameFlujo)

			if mostrarImagen:
				#cv2.imshow('Visual', miAcetatoInformativo.aplicarAFrame(frameFlujo)[120:239,60:360])
				cv2.imshow('Visual',frameFlujo)
			
			informacionTotal[frame_number] = frameFlujo.copy()
			miAcetatoInformativo.inicializar()
			
			tiempoEjecucion = time.time() - tiempoAuxiliar
			if tiempoEjecucion>periodoDeMuestreo:
				miReporte.warning('Tiempo Afuera {0:2f}'.format(tiempoEjecucion)+ '[s] en frame {}'.format(frame_number))

			#sys.stdout.write("\033[F")
			while time.time() - tiempoAuxiliar < periodoDeMuestreo:
				True
			tiempoAuxiliar = time.time()

			if cambiosImportantes:
				miReporte.info('F{} Sema: '.format(frame_number)+semaforoLiteral+' I: '+str(miPoliciaReportando.numeroInfraccionesConfirmadas())+'/'+str(miPoliciaReportando.numeroInfraccionesTotales()))
			
			porcentajeDeMemoria = psutil.virtual_memory()[2]
			
			if (porcentajeDeMemoria > 80)&(os.uname()[1] == 'raspberrypi'):
				miReporte.info('Estado de Memoria: '+str(porcentajeDeMemoria)+'/100')

			if porcentajeDeMemoria > 96:
				miReporte.warning('Alcanzado 96/100 de memoria, borrando todo e inicializando')
				del informacionTotal
				informacionTotal = {}
				frame_number = 0

			frame_number += 1
			if (frame_number >= topeEjecucion) &(topeEjecucion!=0):
				miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por indice de auto acabado predeterminado')
				miPoliciaReportando.apagarCamara()
				break
			if senalSemaforo == -2:
				miReporte.critical('ABANDONANDO LA EJECUCION DE PROGRAMA El semaforo ya no obtuvo señal, necesito recalibrar, abandonando la ejecución del programa')
				break
			ch = 0xFF & cv2.waitKey(5)
			if ch == ord('q'):
				miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por salida manual')
				break
			if ch == ord('s'):
				cv2.imwrite(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'.jpg',frameFlujo)
	except KeyboardInterrupt as e:
		miReporte.info('Salida forzada')
		miPoliciaReportando.apagarCamara()


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
		if input == 'noDraw':
			noDraw = True

	__main_function__()
