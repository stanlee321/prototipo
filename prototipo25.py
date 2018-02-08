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
from ownLibraries.videostream import VideoStream
from ownLibraries.semaforov2 import CreateSemaforo
from ownLibraries.determinacionCruces import PoliciaInfractor
from obtenerHistogramaHorario import exportarInformacionDeHoyO

# Se crean las variables de directorios
directorioDeTrabajo = os.getenv('HOME') + '/trafficFlow/prototipo'
directorioDeVideos  = os.getenv('HOME') + '/trafficFlow/trialVideos'
folderDeInstalacion = directorioDeTrabajo + '/installationFiles'
directorioDeLogo = directorioDeTrabajo + '/watermark'

# Variables diarias:
nombreCarpeta = datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
directorioDeReporte = os.getenv('HOME')+'/'+nombreCarpeta
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
oldFlow = False

generarArchivosDebug = False
mostrarImagen = False
longitudRegistro = 360
font = cv2.FONT_HERSHEY_SIMPLEX

# Temporizaciones
anocheciendo =  17*60+15														# Tiempo 17:30 am + 4 GMT
amaneciendo = 8*60																# Tiempo  7:00 am + 4 GMT
tiempoAhora = datetime.datetime.now().hour*60 +datetime.datetime.now().minute

horaInicioInfraccion = 6*60
horaFinalInfraccion = 22*60

conVideoGrabado = False


def nuevoDia():
	nombreCarpeta = datetime.datetime.now().strftime('%Y-%m-%d')+'_reporte'
	directorioDeReporte = os.getenv('HOME')+'/'+nombreCarpeta
	reporteDiario = directorioDeReporte+'/reporteDiario.npy'
	miReporte.setDirectory(directorioDeReporte)
	miPoliciaReportando.nuevoDia(directorioDeReporte)

# Función principal
def __main_function__():
	# Import some global varialbes
	global archivoDeVideo
	global acaboDeIniciarNuevoCiclo
	acaboDeIniciarNuevoCiclo = False
	global tuveInfracciones
	tuveInfracciones = False
	global tiempoEnPuntoParaNormalVideo
	tiempoEnPuntoParaNormalVideo = 7
	global minuto
	global miReporte
	
	minuto = 0

	if not os.path.exists(directorioDeReporte):
		os.makedirs(directorioDeReporte)

	# Creamos el reporte inicial
	if generarArchivosDebug:
		miReporte = MiReporte(levelLogging=logging.DEBUG,nombre=__name__,directorio=directorioDeReporte)			# Se crea por defecto con nombre de la fecha y hora actual
		miReporte.info('Generando DEBUG')
	else:
		miReporte = MiReporte(levelLogging=logging.INFO,nombre=__name__,directorio=directorioDeReporte)			# Se crea por defecto con nombre de la fecha y hora actual
		
	miReporte.info('Programa iniciado exitosamente con ingreso de senal video '+archivoDeVideo+entradaReal+' con semaforo '+semaforoSimuladoTexto+str(periodoDeSemaforo) +', corriendo a '+str(mifps)+' Frames por Segundo')
	
	vectorDeInicio = [[datetime.datetime.now(),0,0,0,0,0]]
	if os.path.isfile(reporteDiario):
		miReporte.info('Continuando reporte')
		#np.save(reporteDiario,np.append(np.load(reporteDiario),vectorDeInicio,0))
	else:
		miReporte.info('Creando reporte desde cero')
		#np.save(reporteDiario,vectorDeInicio)

	# If mostrar Imagenes
	if mostrarImagen:
		miReporte.info('Pantalla de muestra de funcionamiento en tiempo real encendida')
	else:
		miReporte.info('Pantalla de muestra de funcionamiento en tiempo real apagada')

	# Cargando los parametros de instalacion:
	# El archivo de video debe tener como minimo 5 caracteres para estar trnajando en modo simulado, de lo contrario estamos trabajando en modo real
	if len(archivoDeVideo) > 4:
		archivoParametrosACargar = archivoDeVideo[:-4]+'.npy'
	else:
		archivoParametrosACargar = 'datos.npy'
	
	parametrosInstalacion = np.load(folderDeInstalacion+'/'+archivoParametrosACargar)
	miReporte.info('Datos de Instalacion de: '+folderDeInstalacion+'/'+archivoParametrosACargar)

	indicesSemaforo = parametrosInstalacion[0]
	poligonoSemaforo = np.array([indicesSemaforo[0],indicesSemaforo[183],indicesSemaforo[191],indicesSemaforo[7]])
	verticesPartida = parametrosInstalacion[1]
	verticesLlegada = parametrosInstalacion[2]
	verticesDerecha = parametrosInstalacion[3]
	verticesIzquierda = parametrosInstalacion[4]
	angulo = parametrosInstalacion[5][0]
	poligonoEnAlta = parametrosInstalacion[6]

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
	miPoliciaReportando = PoliciaInfractor(frameFlujo,verticesPartida,verticesLlegada,verticesDerecha,verticesIzquierda,mifps,directorioDeReporte,generarArchivosDebug,flujoAntiguo = oldFlow,anguloCarril = angulo)
	
	miFiltro = IRSwitch()
	miFiltro.paralelizar()
	# Prueba sin filtro todo el dia
	
	miAcetatoInformativo = Acetato()
	miSemaforo = CreateSemaforo(periodoDeSemaforo)
	miAcetatoInformativo.colocarPoligono(np.array(poligonoSemaforo)//2)
	miAcetatoInformativo.colocarPoligono(np.array(verticesPartida))
	miAcetatoInformativo.colocarPoligono(np.array(verticesLlegada))
	miAcetatoInformativo.colocarPoligono(np.array(verticesDerecha))
	miAcetatoInformativo.colocarPoligono(np.array(verticesIzquierda))
	miAcetatoInformativo.colocarPoligono(miPoliciaReportando.carrilValido)
	miAcetatoInformativo.establecerLogo(directorioDeLogo+'/dems.png')

	# El historial sera una lista de la siguiente forma:
	# {numeroFrame: {'frame':np.array((320,240)),'data':{"info"}}}
	global historial
	historial = {}
	frame_number  = 0
	tiempoAuxiliar = time.time()
	periodoDeMuestreo = 1.0/mifps

	try: 
		while True:
			# LEEMOS LA CAMARA DE FLUJO
			if conVideoGrabado:
				for i in range(videofps//mifps):
					ret, frameVideo = miCamara.read()
			else:
				ret, frameVideo = miCamara.read()
			
			pixeles = np.array([frameVideo[indicesSemaforo[0][1],indicesSemaforo[0][0]]])
			
			for indiceSemaforo in indicesSemaforo[1:]:
				pixeles = np.append(pixeles,[frameVideo[indiceSemaforo[1],indiceSemaforo[0]]], axis=0)

			tiempoAhora = datetime.datetime.now().hour*60 + datetime.datetime.now().minute
			if (tiempoAhora > horaInicioInfraccion) & (tiempoAhora < horaFinalInfraccion):
				senalSemaforo, semaforoLiteral, flanco, periodo = miSemaforo.obtenerColorEnSemaforo(pixeles)
			else:
				senalSemaforo, semaforoLiteral, flanco, periodo = 0,'MODO CONTEO',0,60
				if datetime.datetime.now().minute>minuto:
					minuto = datetime.datetime.now().minute
					flanco = -1

			frameFlujo = cv2.resize(frameVideo,(320,240))
			
			velocidadEnBruto, velocidadFiltrada, pulsoVehiculos, momentumAEmplear = miPoliciaReportando.seguirImagen(frame_number,frameFlujo,colorSemaforo = senalSemaforo)
			
			if senalSemaforo >= 1 :							# Si estamos en rojo, realizamos una accion
				if flanco == 1:							# esto se inicia al principio de este estado
					miReporte.info('SEMAFORO EN ROJO')
	
			if senalSemaforo <= 0:							# Si estamos en verde realizamos otra accion
				if flanco == -1:					# Si estamos en verde y en flanco, primer verde, realizamos algo
					miReporte.info('SEMAFORO EN VERDE, EL PERIODO ES '+str(periodo)+' a '+datetime.datetime.now().strftime('%Y%m%d_%H%M'))
					cruce = miPoliciaReportando.estadoActual['cruzo']
					salio = miPoliciaReportando.estadoActual['salio']
					derecha = miPoliciaReportando.estadoActual['derecha']
					izquierda = miPoliciaReportando.estadoActual['izquierda']
					infraccion = miPoliciaReportando.estadoActual['infraccion']
					otro = miPoliciaReportando.estadoActual['ruido']
					vectorDeInicio = [[datetime.datetime.now(),periodo,infraccion,cruce,derecha,izquierda,salio,otro]]
					if os.path.isfile(reporteDiario):
						np.save(reporteDiario,np.append(np.load(reporteDiario),vectorDeInicio,0))
					else:
						np.save(reporteDiario,vectorDeInicio)
					miReporte.info(	'GLOBAL STATE: prev:'+str(miPoliciaReportando.estadoActual['previo'])+
									', cru:'+str(miPoliciaReportando.estadoActual['cruzo'])+
									', der:'+str(miPoliciaReportando.estadoActual['derecha'])+
									', izq:'+str(miPoliciaReportando.estadoActual['izquierda'])+
									', out:'+str(miPoliciaReportando.estadoActual['salio'])+
									', inf:'+str(miPoliciaReportando.estadoActual['infraccion']))
					miPoliciaReportando.reestablecerEstado()

				miPoliciaReportando.reportarPasoAPaso(historial)
	
				if generarArchivosDebug:
					if datetime.datetime.now().hour>tiempoEnPuntoParaNormalVideo:
						miPoliciaReportando.generarVideoMuestra(historial)
						tiempoEnPuntoParaNormalVideo = datetime.datetime.now().hour
				if datetime.datetime.now().hour == 7:
					tiempoEnPuntoParaNormalVideo = 7

			# Si el tiempo es el adecuado y el filtro no esta actualizado se actualiza
			tiempoAhora = datetime.datetime.now().hour*60 + datetime.datetime.now().minute
			
			if (tiempoAhora > amaneciendo) & (tiempoAhora < anocheciendo) & ((miFiltro.ultimoEstado == 'Filtro Desactivado')|(miFiltro.ultimoEstado =='Inicializado')):
				miFiltro.colocarFiltroIR()
				miReporte.info('Active Filtro a horas '+ datetime.datetime.now().strftime('%H:%M:%S'))
			if ((tiempoAhora < amaneciendo) | (tiempoAhora > anocheciendo)) & ((miFiltro.ultimoEstado == 'Filtro Activado')|(miFiltro.ultimoEstado =='Inicializado')):
				miFiltro.quitarFiltroIR()
				miReporte.info('Desactive Filtro a horas '+ datetime.datetime.now().strftime('%H:%M:%S'))
			
			if len(historial)> 2*60*mifps:	# Si es mayor a dos minutos en el pasado
				del historial[min(historial)]				

			# Draw frame number into image on top
			for infraction in miPoliciaReportando.listaVehiculos:		
				puntos = infraction['desplazamiento'].ravel()
				puntosExtraidos = puntos.reshape(puntos.shape[0]//2,2)
				miAcetatoInformativo.colocarObjeto(puntosExtraidos,infraction['estado'])

			#for puntoResguardo in miPoliciaReportando.obtenerLineasDeResguardo(False):
			miAcetatoInformativo.colocarPuntos(miPoliciaReportando.obtenerLineasDeResguardo(True),'Referencia')
			
			# Configs and displays for the MASK according to the semaforo
			#miAcetatoInformativo.agregarTextoEn("I{}".format(miPoliciaReportando.infraccionesConfirmadas), 2)
			
			miAcetatoInformativo.colorDeSemaforo(senalSemaforo)

			frameFlujo = miAcetatoInformativo.aplicarConstantes(frameFlujo)

			if generarArchivosDebug:
				#historial[frame_number]['debug'] = frameFlujo.copy()
				frameFlujo = miAcetatoInformativo.aplicarAFrame(frameFlujo)
				historial[frame_number] = {'video':frameFlujo.copy()}
			else:
				historial[frame_number] = {'video':frameFlujo.copy()}
				if mostrarImagen:
					frameFlujo = miAcetatoInformativo.aplicarAFrame(frameFlujo)
			
			if mostrarImagen:
				#cv2.imshow('Visual', miAcetatoInformativo.aplicarAFrame(frameFlujo)[120:239,60:360])
				cv2.imshow('Visual',frameFlujo)

			#else:
			#	historial[frame_number]['frame'] = historial[frame_number]['captura']
			historial[frame_number]['data'] = [velocidadEnBruto, velocidadFiltrada, pulsoVehiculos, momentumAEmplear]
			miAcetatoInformativo.inicializar()
			
			tiempoEjecucion = time.time() - tiempoAuxiliar
			if tiempoEjecucion>periodoDeMuestreo:
				miReporte.warning('\t[f{}'.format(frame_number)+']'+' Periodo Excedido {0:2f}'.format(tiempoEjecucion)+ '[s]')
			
			#sys.stdout.write("\033[F")
			while time.time() - tiempoAuxiliar < periodoDeMuestreo:
				True
			tiempoAuxiliar = time.time()

			#miReporte.info('python3 '+ str(__file__)+' '+str( *sys.argv[1:]))

			if (int(nombreCarpeta[8:10]) != datetime.datetime.now().day):
				miReporte.info('Actualizando por cambio de dia a '+str(datetime.datetime.now().day))# el script por cambio de día')
				exportarInformacionDeHoyO(-1)
				# Esto tiene que estar antes del metodo nuevoDia():
				miReporte.info('Informacion exportada, borrando: '+nombreCarpeta)
				os.system('python3 cleanfolders.py -folder '+nombreCarpeta)
				nuevoDia()
				miReporte.info('Cambio de día exitoso')
				#miPoliciaReportando.apagarCamara()
				#os.execl(sys.executable, 'python3', __file__, *sys.argv[1:])
				# As bug continues we reboot the system:
				#os.system('sudo reboot')

			porcentajeDeMemoria = psutil.virtual_memory()[2]
				
			if (porcentajeDeMemoria > 85)&(os.uname()[1] == 'raspberrypi'):
				miReporte.info('Estado de Memoria: '+str(porcentajeDeMemoria)+'/100')
			"""
			if porcentajeDeMemoria > 96:
				miReporte.warning('Alcanzado 96/100 de memoria, borrando todo e inicializando')
				del historial
				historial = {}
				frame_number = 0
			"""
			frame_number += 1
			
			if (frame_number >= topeEjecucion) &(topeEjecucion!=0):
				miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por indice de auto acabado predeterminado')
				miPoliciaReportando.apagarCamara()
				break

			ch = 0xFF & cv2.waitKey(5)
			if ch == ord('q'):
				miReporte.info('ABANDONANDO LA EJECUCION DE PROGRAMA por salida manual')
				miPoliciaReportando.apagarCamara()
				break
			if ch == ord('s'):
				cv2.imwrite(datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')+'.jpg',frameFlujo)
			
	except KeyboardInterrupt as e:
		miReporte.info('Salida forzada')
		miPoliciaReportando.apagarCamara()


if __name__ == '__main__':
	# Tomamos los ingresos para controlar el video
	for input in sys.argv:
		if input == 'debug':
			generarArchivosDebug = True
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
		if input == 'Old':
			oldFlow = True

	__main_function__()
