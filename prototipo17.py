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
from multiprocessing.dummy import Pool as ThreadPool 


from ownLibraries.irswitch import IRSwitch
from ownLibraries.mireporte import MiReporte
from ownLibraries.visualizacion import Acetato
from ownLibraries.herramientas import total_size
from ownLibraries.policiainfractor import PoliciaInfractor
from ownLibraries.generadorevidencia import GeneradorEvidencia
from ownLibraries.videostreamv2 import VideoStream
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
			miCamara = VideoStream(src = 0, resolution = shapeMR, poligono = poligonoSemaforo, debug = saltarFrames, fps = mifps).start()
			time.sleep(1)
		elif os.uname()[1] == 'stanlee321-MS-7693':
			print('Hello stanlee321')
			miCamara = VideoStream(src = 0, resolution = shapeMR, poligono = poligonoSemaforo, debug = saltarFrames, fps = mifps).start()
		elif os.uname()[1] == 'stanlee321-HP-240-G1-Notebook-PC':
			print('Hello stanlee321')
			miCamara = VideoStream(src = 0, resolution = shapeMR, poligono = poligonoSemaforo, debug = saltarFrames, fps = mifps).start()

		else:
			miCamara = VideoStream(src = 0, resolution = shapeUR, poligono = poligonoSemaforo, debug = saltarFrames, fps = mifps).start()
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

	#pool = ThreadPool(2) 

	#input_q = Queue(5)
	#output_q = Queue(5)

	#child_process = Process(target = child_process_detect_objects_with_bg, args=(input_q, output_q))
	#child_process.daemon = True
	#child_process.start()
	# Create CUT Object
	if os.uname()[1] == 'stanlee321-MS-7693': 
		cutImage = cutHDImage(shapeHR = shapeMR, shapeLR = shapeLR)
	else:
		cutImage = cutHDImage(shapeHR = shapeUR, shapeLR = shapeLR)

	# Create Semaphro
	periodo = 0
	semaforo = CreateSemaforo(periodoSemaforo = periodo)
	listaderecortados = list
	informacion = dict
	while True:
		tiempoAuxiliar = time.time()
		data = miCamara.read()
		data['index'] = frame_number

		capturaEnAlta = data['HRframe']
		capturaEnBaja = data['LRframe']
		capturaSemaforo = data['frame_semaforo']

		senalColor, colorLiteral, flancoSemaforo, periodoSemaforo = semaforo.obtenerColorEnSemaforo(capturaSemaforo)
		#print('Lectura: ',time.time()-tiempoAuxiliar)
		poligonos_warp = backgroundsub.feedbgsub(capturaEnBaja)
		#poligonos_warp = pool.starmap(backgroundsub.feedbgsub, capturaEnBaja)


		# close the pool and wait for the work to finish 
		#pool.close() 
		#pool.join()
		#print(poligonos_warp)
		listaderecortados = cutImage(HDframe = capturaEnBaja, matches = poligonos_warp)

		informacion = {'semaforo': [senalColor, colorLiteral, flancoSemaforo, periodoSemaforo],\
						'frame':capturaEnBaja, 'rectangulos': listaderecortados, 'index': data['index']}


		"""
		#print('SEMAPHORO STATES: ', senalColor, colorLiteral, flancoSemaforo, periodoSemaforo)
		print('Lectura: ',time.time()-tiempoAuxiliar)
		tiempoAuxiliar = time.time()


		#informacionTotal[frame_number] = informacion.copy() #<------ ese .copy() faltaba
		print('Out: ', informacion['semaforo'][2])
		# Si forzamos por entrada o si estamos en verde botamos la información de los rectangulos:

		if (guardarRecortados == False) | (informacion['semaforo'][0]==0):
			#del informacion['recortados']
			#informacionTotal[frame_number]['recortados'] = {}
			pass
		# Se reporta el periodo del semaforo si es necesario:

		if informacion['semaforo'][3] != 0:
			miReporte.info('SEMAFORO EN VERDE, EL PERIODO ES '+str(informacion['semaforo'][3]))
		else:
			pass
		# Si tengo infracciones pendientes las evoluciono
		if informacion['semaforo'][0] >= 1 :							# Si estamos en rojo, realizamos una accion
			if informacion['semaforo'][2] == 1:							# esto se inicia al principio de este estado
				miReporte.info('SEMAFORO EN ROJO')
				miPoliciaReportando.inicializarAgente()
				#del informacionTotal
				#informacionTotal = {}
				frame_number = 0
			else:
				pass
			cambiosImportantes = miPoliciaReportando.seguirObjeto(informacion['index'], informacion)
		else:
			pass

		if informacion['semaforo'][0] == 0:							# Si estamos en verde realizamos otra accion
			if informacion['semaforo'][2] == -1:					# Si estamos en verde y en flanco, primer verde, realizamos algo
				miReporte.info('Infracciones: ' + str(miPoliciaReportando.numeroInfraccionesConfirmadas()))
				if generarArchivosDebug:
					miGrabadora.generarReporteInfraccion(informacionTotal, False,miPoliciaReportando.numeroInfraccionesConfirmadas())
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
		
		miAcetatoInformativo.colorDeSemaforo(informacion['semaforo'][0])

		# Draw the rectangles
		for rectangulo in informacion['rectangulos']:
			miAcetatoInformativo.colocarObjetivo(rectangulo[0],rectangulo[2])

		if mostrarImagen:
			#cv2.imshow('Visual', miAcetatoInformativo.aplicarAFrame(informacion['frame'])[120:239,60:360])
			cv2.imshow('Visual', miAcetatoInformativo.aplicarAFrame(informacion['frame']))
		miAcetatoInformativo.inicializar()
		
		tiempoEjecucion = time.time() - tiempoAuxiliar
		#if tiempoEjecucion>periodoDeMuestreo:
		miReporte.warning('Tiempo Afuera {0:2f}'.format(tiempoEjecucion)+ '[s] en frame {}'.format(frame_number))

		#sys.stdout.write("\033[F")
		while time.time() - tiempoAuxiliar < periodoDeMuestreo:
			True
		tiempoAuxiliar = time.time()

		if (cambiosImportantes)|(numeroDeObjetos != len(informacion['rectangulos'])):
			miReporte.info('F{} Sema: '.format(frame_number)+informacion['semaforo'][1]+' I: '+str(miPoliciaReportando.numeroInfraccionesConfirmadas())+'/'+str(miPoliciaReportando.numeroInfraccionesTotales())+' Objetos: {}'.format(len(informacion['rectangulos'])))
		numeroDeObjetos = len(informacion['rectangulos'])
		
		porcentajeDeMemoria = psutil.virtual_memory()[2]
		
		if porcentajeDeMemoria > 80:
			miReporte.info('Estado de Memoria: '+str(porcentajeDeMemoria)+'/100')
		if porcentajeDeMemoria > 92:
			frameAOptimizar = min(informacionTotal)
			miReporte.warning('Alcanzado 92/100 de memoria, borrando frame: '+str(frameAOptimizar))
			del informacionTotal[frameAOptimizar]['recortados']
			informacionTotal[frameAOptimizar]['recortados'] = {}

		if porcentajeDeMemoria > 96:
			miReporte.warning('Alcanzado 96/100 de memoria, borrando todo e inicializando')
			del informacionTotal
			informacionTotal = {}
			frame_number = 0

		frame_number += 1
		if (frame_number >= topeEjecucion) &(topeEjecucion!=0):
			miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por indice de auto acabado predeterminado')
			break
		if informacion['semaforo'][0] == -2:
			miReporte.critical('ABANDONANDO LA EJECUCION DE PROGRAMA El semaforo ya no obtuvo señal, necesito recalibrar, abandonando la ejecución del programa')
			break
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por salida manual')
			break
		if ch == ord('s'):
			cv2.imwrite(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'.jpg',informacion['frame'])
		fps.update()
		#if colorLiteral == 'Rojo':
			#poligonos_warp = backgroundsub.feedbgsub(capturaEnBaja)
			#poligonos_warp = pool.starmap(backgroundsub.feedbgsub, capturaEnBaja)
			# close the pool and wait for the work to finish 
			#pool.close() 
			#pool.join()
			#print(poligonos_warp)
			#listaderecortados = cutImage(HDframe = capturaEnBaja, matches = poligonos_warp)

		#if len(listaderecortados) > 0:
		#	for i, image in enumerate(listaderecortados):
		#		cv2.imwrite('imagen_{}_.jpg'.format(i), image)
		#else:
		#	pass
		#print('Put: ',time.time()-tiempoAuxiliar)
		if mostrarImagen:
			tiempoAuxiliar = time.time()
			cv2.imshow('Camara', cv2.resize(capturaEnBaja,(640,480)))
			print('Show: ',time.time()-tiempoAuxiliar)

		print('Periodo total: ',time.time()-periodoReal)


		periodoReal = time.time()

		#tiempoAuxiliar = time.time()
		#if filaImagenes.qsize() > 10:
		#miImagen = filaImagenes.get()
		#	print('Borrado elemento en la fila')
		#print('Get: ',time.time()-tiempoAuxiliar)
		if frame_number>200:
			break
		frame_number +=1
		"""
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