"""
This new prototipe includes huge improvements in flow detection and image capture for the raspberry pi 
"""
import os
import sys
import cv2
import time
import logging
import datetime
import numpy as np

from ownLibraries.mask import VisualLayer
from ownLibraries.irswitch import IRSwitch
from ownLibraries.videostreamv5 import FPS
from ownLibraries.mireporte import MiReporte
from ownLibraries.herramientas import total_size
from ownLibraries.videostreamv5 import VideoStream
from ownLibraries.policiainfractor import PoliciaInfractor
from ownLibraries.generadorevidencia import GeneradorEvidencia


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
guardarRecortados = True
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
	miReporte = MiReporte(levelLogging=logging.DEBUG,nombre=__name__)			# Se crea por defecto con nombre de la fecha y hora actual
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
			miCamara = VideoStream(src = 1, resolution = (640,480),poligono = poligonoSemaforo, debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma ).start()
			time.sleep(1)
		else:
			#miCamara = VideoStream(src = 0, resolution = (3296,2512),poligono = poligonoSemaforo, debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma).start()
			miCamara = VideoStream(src = 0, resolution = (1920,1080),poligono = poligonoSemaforo, debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma).start()

			time.sleep(1)

		miReporte.info('Activada Exitosamente cámara en tiempo real')
	else:
		try:
			miCamara = VideoStream(src = directorioDeVideos+'/'+archivoDeVideo, resolution = (640,480),poligono = poligonoSemaforo,debug = saltarFrames,fps = mifps, periodo = periodoDeSemaforo, gamma = gamma).start()
			time.sleep(1)
			miReporte.info('Archivo de video cargado exitosamente: '+directorioDeVideos+'/'+archivoDeVideo)
		except Exception as currentException:
			miReporte.error('No se pudo cargar el video por '+str(currentException))

	# Se captura la imagen de flujo inicial y se trabaja con la misma
	informacion = miCamara.read()
	
	# Creación de objetos:
	miPoliciaReportando = PoliciaInfractor(informacion['frame'],verticesPartida,verticesLlegada)
	miGrabadora = GeneradorEvidencia(directorioDeReporte,mifps,guardarRecortados)
	miFiltro = IRSwitch()

	#remocionFondo = matches # List like with arrays 
	if mostrarImagen:
		visualLabel = VisualLayer()
		visualLabel.crearMascaraCompleta(size = (240,320))
		visualLabel.crearBarraInformacion(height = 240)
		visualLabel.crearBarraDeProgreso()
		visualLabel.ponerPoligono(np.array(verticesPartida))
	
	frame_number = 0	

	fps = FPS().start()
	informacionTotal = {}
	frame_number  = 0
	tiempoAuxiliar = time.time()
	periodoDeMuestreo = 1.0/mifps

	while True:
		# LEEMOS LA CAMARA DE FLUJO
		
		# Ways to access to the information 

		# information['frame'] ; numpy array containing the low res frame 
		# information['semaforo'] ; list like [self.senalColor, self.colorLiteral, self.flancoSemaforo]
		# information['recortados'] ; list like of tuples  representing listaderecortados from hd frame [(_numpy arrays_)n+1]
		# information['rectangulos'] ; list like of tuples  representing listaderectangulos and centroids in frame [((x,y,h,w),(p1,p2))n+1]
		# n+1 ; represent the 1 by 1 correspndencia de los rectangulos encontrados y imagenes recortadas
		
		informacion = miCamara.read() # Ways to access

		# assing index information to the above infomation

		# Asign number rfame to the information from miCamara.read()		
		informacion['index'] = frame_number

		informacionTotal[frame_number] = informacion.copy() #<------ ese .copy() faltaba
		print('Tamanio buffer: ',total_size(informacionTotal),' en ',len(informacionTotal))
		# Si forzamos por entrada o si estamos en verde botamos la información de los rectangulos:
		if (guardarRecortados == False) | (informacionTotal[frame_number]['semaforo'][0]==0):
			del informacionTotal[frame_number]['recortados']
			informacionTotal[frame_number]['recortados'] = {}

		if frame_number> maximoMemoria:
			try:
				informacionTotal[frame_number - maximoMemoria]['recortados'] = []
				#miReporte.debug('Released memory')
			except Exception as e:
				miReporte.error('No pude liberar por '+ str(e))

		# Si tengo infracciones pendientes las evoluciono
		if informacion['semaforo'][0] >= 1:							# Si estamos en rojo, realizamos una accion
			if informacion['semaforo'][2] == 1:						# esto se inicia al principio de este estado
				print('Here was something---')
				#miReporte.info('SEMAFORO EN ROJO')
				miPoliciaReportando.inicializarAgente()
				del informacionTotal
				informacionTotal = {}
				frame_number = 0

			cambiosImportantes = miPoliciaReportando.seguirObjeto(frame_number,informacion)

		if informacion['semaforo'][0] == 0:							# Si estamos en verde realizamos otra accion
			if informacion['semaforo'][2] == -1:					# Si estamos en verde y en flanco, primer verde, realizamos algo
				miReporte.info('SEMAFORO EN VERDE')
				miReporte.info('Infracciones: '+str(miPoliciaReportando.numeroInfraccionesConfirmadas()))
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

		if mostrarImagen:
			# Draw frame number into image on top
			cv2.putText(informacion['frame'], datetime.datetime.now().strftime('%A %d %B %Y %I:%M:%S%p'), (4,236), font, 0.4,(255,255,255),1,cv2.LINE_AA)
			cv2.putText(informacion['frame'], str(frame_number),(20,20), font, 0.4,(255,255,255),1,cv2.LINE_AA)
			visualizacion = informacion['frame']

			for infraction in miPoliciaReportando.listaDeInfracciones:
				for puntos in infraction['desplazamiento']:
					puntosExtraidos = puntos.ravel().reshape(puntos.ravel().shape[0]//2,2)
					for punto in puntosExtraidos:
						if infraction['estado'] == 'Confirmado':
							cv2.circle(visualizacion, tuple(punto), 1, (0,0,255), -1)
						else:
							cv2.circle(visualizacion, tuple(punto), 1, (255,0,0), -1)

			cv2.polylines(visualizacion, np.array([poligonoSemaforo])//2, True, (200,200,200))
			
			# Configs and displays for the MASK according to the semaforo
			visualLabel.agregarTextoEn(informacion['semaforo'][1], 0)
			visualLabel.agregarTextoEn("F{}".format(frame_number), 1)
			visualLabel.agregarTextoEn("I{}".format(miPoliciaReportando.infraccionesConfirmadas), 2)
			
			if informacion['semaforo'][0] == 1:
				visualLabel.establecerColorFondoDe(backgroudColour = (0,0,255), numeroDeCaja = 0)
			elif informacion['semaforo'][0] == 0:
				visualLabel.establecerColorFondoDe(backgroudColour = (0,255,0), numeroDeCaja = 0)
			elif informacion['semaforo'][0] == 2:
				visualLabel.establecerColorFondoDe(backgroudColour = (0,255,255), numeroDeCaja = 0)
			else:
				visualLabel.establecerColorFondoDe(backgroudColour = (0,0,0), numeroDeCaja = 0)

			# Draw the rectangles
			for rectangulo in informacion['rectangulos']:
				visualLabel.agregarRecangulo((rectangulo[0],rectangulo[1]),rectangulo[2])
				
			visualLabel.establecerMagnitudBarra(magnitude = int(miPoliciaReportando.ultimaVelocidad))

			visualizacion = visualLabel.aplicarMascaraActualAFrame(visualizacion)
			
			# Show Everything
			cv2.imshow('Visual', cv2.resize(visualLabel.aplicarTodo(),(620,480)))		
		
		tiempoEjecucion = time.time() - tiempoAuxiliar
		if tiempoEjecucion>periodoDeMuestreo:
			miReporte.warning('Se sobrepaso el periodo de muestreo a {0:2f}'.format(tiempoEjecucion)+ '[s] en frame {}'.format(frame_number))

		#sys.stdout.write("\033[F")
		while time.time() - tiempoAuxiliar < periodoDeMuestreo:
			True

		if (cambiosImportantes)|(numeroDeObjetos != len(informacion['rectangulos'])):
			miReporte.info('F{} Sema: '.format(frame_number)+informacion['semaforo'][1]+' I: '+str(miPoliciaReportando.numeroInfraccionesConfirmadas())+'/'+str(miPoliciaReportando.numeroInfraccionesTotales())+' Objetos: {}'.format(len(informacion['rectangulos'])))
		numeroDeObjetos = len(informacion['rectangulos'])
		tiempoAuxiliar = time.time()

		frame_number += 1
		if (frame_number >= topeEjecucion) &(topeEjecucion!=0):
			break
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break
		if ch == ord('s'):
			cv2.imwrite(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'.jpg',informacion['frame'])
		fps.update()

	# stop the timer and display FPS information
	fps.stop()

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
		if 'noRec' in input:
			guardarRecortados = False
		if 'gamma' in input:
			gamma = float(input[:-5])

	__main_function__()