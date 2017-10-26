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
import multiprocessing
import matplotlib.pyplot as plt 

# Se crean las variables de directorios
directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo'
directorioDeVideos = os.getenv('HOME')+'/trafficFlow/trialVideos'
directorioDeLibreriasPropias = directorioDeTrabajo +'/ownLibraries'
nombreCarpetaDeReporte = 'casosReportados'
myReportingDirectory = directorioDeTrabajo+'/'+nombreCarpetaDeReporte
folderDeInstalacion = directorioDeTrabajo+'/installationFiles'
# Se introduce las librerias propias
sys.path.insert(0, directorioDeLibreriasPropias)
from mask import VisualLayer
from mireporte import MiReporte
#from semaforo import CreateSemaforo
from policiainfractor import PoliciaInfractor
from desplazamientoimagen import DesplazamientoImagen
from videostreamv5 import VideoStream
from videostreamv5 import FPS
from BackgroundsubCNT import CreateBGCNT
from generadorevidencia import GeneradorEvidencia

# Se crean las variables de constantes de trabajo del programa
## Parametros de input video
archivoDeVideo = ''
videofps = 30
entradaReal = 'en tiempo real '		# Complementario
## Parametros semaforo
periodoDeSemaforo = 0
semaforoSimuladoTexto = 'real '
## Otros
mifps = 10
generarArchivosDebug = True
mostrarImagen = False
longitudRegistro = 360

# Función principal
def __main_function__():
	# Import some global varialbes
	global archivoDeVideo

	# Creamos el reporte inicial
	miReporte = MiReporte(levelLogging=logging.DEBUG,nombre=__name__)			# Se crea por defecto con nombre de la fecha y hora actual
	miReporte.info('Programa iniciado exitosamente con ingreso de senal video '+archivoDeVideo+entradaReal+' con semaforo '+semaforoSimuladoTexto+str(periodoDeSemaforo) +', corriendo a '+str(mifps)+' Frames por Segundo')
	
	# Is statements
	if generarArchivosDebug: miReporte.info('Generando Archivos de Debug')
	else: miReporte.info('Generando infracciones unicamente (No debug video)')
	if mostrarImagen: miReporte.info('Pantalla de muestra de funcionamiento en tiempo real encendida')
	else: miReporte.info('Pantalla de muestra de funcionamiento en tiempo real apagada')

	# El directorio de reporte debe crearse al inicio del programa
	# Variables de control:
	periodoDeMuestreo = 1.0/mifps # 0.1666667		# 1/mifps
	numeroDeFrame = 0
	maximoInfraccionesPorFrame = 20
	colores = np.random.randint(0,255,(maximoInfraccionesPorFrame,3))

	# Cargando los parametros de instalacion:
	# El archivo de video debe tener como minimo 5 caracteres para estar trnajando en modo simulado, de lo contrario estamos trabajando en modo real
	if len(archivoDeVideo)>4: archivoParametrosACargar = archivoDeVideo[:-4]+'.npy'
	else: archivoParametrosACargar = 'datos.npy'
	parametrosInstalacion = np.load(folderDeInstalacion+'/'+archivoParametrosACargar)
	poligonoSemaforo = parametrosInstalacion[0]
	verticesPartida = parametrosInstalacion[1]
	verticesLlegada = parametrosInstalacion[2]
	angulo = parametrosInstalacion[3]

	try:
		misVerticesExtremos = parametrosInstalacion[4]
	except:
		misVerticesExtremos = [[0,0],[2592,1944]]
		miReporte.error('NO PUDE cargar la configuracion de la camara de placas, tomando la por defecto')

	miReporte.info('Cargado exitosamente parametros de instalacion: '+str(parametrosInstalacion))

	# Arrancando camara
	if len(archivoDeVideo)==0:	# modo real
		if os.uname()[1] == 'alvarohurtado-305V4A':
			miCamara = VideoStream(src = 1, resolution = (640,480),poligono = poligonoSemaforo, draw = mostrarImagen,debug = True,fps = mifps).start()
			time.sleep(1)
		else:
			miCamara = VideoStream(src = 0, resolution = (3296,2512),poligono = poligonoSemaforo, draw = mostrarImagen,debug = True,fps = mifps).start()
			time.sleep(1)
			#miCamara.set(3,3296)
			#miCamara.set(4,2512)
		miReporte.info('Activada Exitosamente cámara en tiempo real')
	else:
		try:
			miCamara = VideoStream(src = directorioDeVideos+'/'+archivoDeVideo, resolution = (640,480),poligono = poligonoSemaforo, draw = mostrarImagen,debug = True,fps = mifps).start()
			time.sleep(1)
			miReporte.info('Archivo de video cargado exitosamente: '+directorioDeVideos+'/'+archivoDeVideo)
		except Exception as currentException:
			archivoDeVideo = input('No se pudo cargar el video, ingresar otro nombre:\n')
			miCamara = cv2.VideoCapture(directorioDeVideos+'/'+archivoDeVideo)

	# Se captura la imagen de flujo inicial y se trabaja con la misma
	informacion = miCamara.read()

	# Si estamos trabajando en la raspberry pi, no necesitamos simular la camara de 8Mp
	miComputadora = os.uname()[1]
	
	# Creación de objetos:
	miPoliciaReportando = PoliciaInfractor(informacion['frame'],verticesPartida,verticesLlegada)
	miRegistroDesplazado = DesplazamientoImagen(longitudRegistro)
	miGrabadora = GeneradorEvidencia(directorioDeTrabajo,mifps)
	#remocionFondo = matches # List like with arrays 

	if mostrarImagen:
		visualLabel = VisualLayer()
		visualLabel.crearMascaraCompleta(size = (240,320))
		visualLabel.crearBarraInformacion(height = 240)
		visualLabel.crearBarraDeProgreso()
		visualLabel.ponerPoligono(np.array(verticesPartida))
		#visualLabel.ponerPoligono(np.array(verticesLlegada))

	#miSemaforo = CreateSemaforo(periodoDeSemaforo)
	tiempoAuxiliar = time.time()
	frame_number = 0	

	#print('ENTERING TO THE WHILE LOOP')

	fps = FPS().start()
	_frame_number_auxiliar = 0
	informacionTotal = []
	frame_number  = -1

	while True:
		# LEEMOS LA CAMARA DE FLUJO

		otroTiempo = time.time()
		if archivoDeVideo=='':
			informacion = miCamara.read()
		else:
			# En caso de modo debug descartamos algunos frames para simular el periodo de muestreo
			#for inciceDescarte in range(videofps//mifps):
			informacion = miCamara.read()
		
		informacion['index'] = frame_number
		# If you want to save the frames to some folder ../frame/

		#for key, value  in  recortados.items():
		#	for i, frame in enumerate(value):
		#		cv2.imwrite('../frames/frame_{}_element_{}.jpg'.format(key,i), frame)

		##print('recortados dict  powered by BGSUBCNT ARE recordados[frame] = [----frames_i---] : ',  recortados)
		# informacion = {'index':int,'informacion['frame']': np.array(320,240),'recortados':list(np.array(x,x)),'semaforo':[informacion['semaforo'][0],informacion['semaforo'][1],informacion['semaforo'][2]]}

		print('Outside number: ',frame_number)
		informacionTotal.append(informacion)
		#print(frame_number)

		##print('Introducido ', sys.getsizeof(capturaAlta),' in ', capturaAlta.shape)
		#informacion['semaforo'][0], informacion['semaforo'][1], informacion['semaforo'][2] = miSemaforo.obtenerColorEnSemaforo(semaforo)
		#print('Semaforo: ',time.time()-otroTiempo)

		otroTiempo = time.time()
		#remocionFondo.alimentar(informacion['frame'])
		#remocionFondo.draw()
		#print('Remocion de fonde: ',time.time()-otroTiempo)
		
		# Si tengo infracciones pendientes las evoluciono
		if informacion['semaforo'][0] >= 1:					# Si estamos en rojo, realizamos una accion
			if informacion['semaforo'][2] == 1:			# esto se inicial al principio de este estado
				miPoliciaReportando.inicializarAgente()
				miRegistroDesplazado.reestablecerDesplazamiento(longitudRegistro)
				#print('RED')
				#miReporte.info('<<<ROJO RED ROJO RED at: '+datetime.datetime.now().strftime('%H-%M-%S')+' ROJO RED ROJO RED>>>')
				otroTiempo = time.time()
				del informacionTotal
				informacionTotal = []
				frame_number = 0
			miPoliciaReportando.evolucionarLineaVigilancia(frame_number,informacion['frame'])
			#print('Policia Reportando: ',time.time()-otroTiempo)

		if informacion['semaforo'][0] == 0:		# Si estamos en verde realizamos otra accion
			try:
				#print('GREEN')#miReporte.info('# Reportando')
				infraccionEnRevision = miPoliciaReportando.popInfraccion()
				print(infraccionEnRevision)
				miGrabadora.generarReporteInfraccion(informacionTotal,infraccionEnRevision)
			except Exception as e:
				print(e)

		indiceColor = 0
		
		otroTiempo = time.time()
		if mostrarImagen:
			visualizacion = informacion['frame']
			for infraction in miPoliciaReportando.listaPorConfirmar:
				for puntos in infraction['desplazamiento']:
					puntosExtraidos = puntos.ravel().reshape(puntos.ravel().shape[0]//2,2)
					for punto in puntosExtraidos:
						cv2.circle(visualizacion, tuple(punto), 1, colores[indiceColor].tolist(), -1)
				indiceColor +=1

			for infraction in miPoliciaReportando.listaDeInfracciones:
				for puntos in infraction['desplazamiento']:
					puntosExtraidos = puntos.ravel().reshape(puntos.ravel().shape[0]//2,2)
					for punto in puntosExtraidos:
						cv2.circle(visualizacion, tuple(punto), 1, (0,0,255), -1)
			cv2.polylines(visualizacion, np.array([poligonoSemaforo])//2, True, (200,200,200))
			visualLabel.agregarTextoEn(informacion['semaforo'][1], 0)
			visualLabel.agregarTextoEn("F{}".format(frame_number), 1)
			visualLabel.agregarTextoEn("I{}".format(miPoliciaReportando.infraccionesConfirmadas), 2)
			#>visualLabel.agregarTextoEn(str(miPoliciaReportando.reporteInfracciones()[0])+'/'+str(miPoliciaReportando.reporteInfracciones()[1]), 3)
			#>visualLabel.agregarTextoEn('G'+str(miPoliciaReportando.reporteInfracciones()[-1]), 4)
			if informacion['semaforo'][0] == 1: visualLabel.establecerColorFondoDe(backgroudColour = (0,0,255), numeroDeCaja = 0)
			elif informacion['semaforo'][0] == 0: visualLabel.establecerColorFondoDe(backgroudColour = (0,255,0), numeroDeCaja = 0)
			elif informacion['semaforo'][0] == 2: visualLabel.establecerColorFondoDe(backgroudColour = (0,255,255), numeroDeCaja = 0)
			else: visualLabel.establecerColorFondoDe(backgroudColour = (0,0,0), numeroDeCaja = 0)
			visualLabel.establecerMagnitudBarra(magnitude = int(miPoliciaReportando.ultimaVelocidad))
			visualizacion = visualLabel.aplicarMascaraActualAFrame(visualizacion)
			cv2.imshow('Visual',visualLabel.aplicarTodo())
		#print('Visualizacion: ',time.time()-otroTiempo)
		# Visualizacion	
		##print('Ciclo: ',str(time.time()-tiempoAuxiliar)[:7],' color: ',informacion['semaforo'][1])
		#sys.stdout.write("\033[F")
		
		
		_frame_number_auxiliar +=1
		#if tiempoEjecucion>periodoDeMuestreo:
		#	miReporte.warning('Se sobrepaso el periodo de muestreo a: '+str(tiempoEjecucion))
		while time.time()-tiempoAuxiliar<periodoDeMuestreo:
			True

		tiempoEjecucion = time.time()-tiempoAuxiliar
		#print('Periodo: ',tiempoEjecucion)
		tiempoAuxiliar = time.time()

		frame_number += 1
		if _frame_number_auxiliar == 4000:
			break
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break
		fps.update()


	# stop the timer and display FPS information
	fps.stop()
	#print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	#print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
# Se introducen los argumentos de control en el formato establecido
if __name__ == '__main__':
	# Tomamos los ingresos para controlar el video
	for input in sys.argv:
		if input == 'NoDebug':
			generarArchivosDebug = False
		if ('.mp4' in input)|('.avi' in input):
			archivoDeVideo = input
			entradaReal = ''
		if '.seg' in input:
			periodoDeSemaforo = int(input[:-4])
			semaforoSimuladoTexto = 'simulado a '
		if input == 'Show':
			mostrarImagen = True
		if '.fps' in input:
			mifps = int(input[:-4])
	__main_function__()