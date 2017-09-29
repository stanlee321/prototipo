import os
import cv2
import time
import numpy as np

directorioDeTrabajo = os.getenv('HOME')+'/trafficFlow/prototipo11'
directorioDeVideos = os.getenv('HOME')+'/trafficFlow/trialVideos'
directorioDeLibreriasPropias = directorioDeTrabajo +'/ownLibraries'
nombreCarpetaDeReporte = 'casosReportados'
myReportingDirectory = directorioDeTrabajo+'/'+nombreCarpetaDeReporte
folderDeInstalacion = directorioDeTrabajo+'/installationFiles'


class PoliciaInfractor():
	"""
	Esta clase recibe una imagen, el estado del semaforo y determina flujo vehicular e infracciones
	"""
	def __init__(self,imagenParaInicializar,poligonoPartida,poligonoLlegada):
		# Tomo la imagen de inicialización y obtengo algunas caracteristicas de la misma
		self.imagenAuxiliar = cv2.cvtColor(imagenParaInicializar, cv2.COLOR_BGR2GRAY)
		try:
			height,width = self.imagenAuxiliar.shape
		except:
			print('No pude obtener data, es una imagen el objeto de inicializacion?')
		
		self.areaDeResguardo = np.array(poligonoPartida)
		self.areaDeConfirmacion = np.array(poligonoLlegada)
		self.lineaDePintadoLK =  np.array([poligonoPartida[0],poligonoPartida[3]])
		self.lineaTraseraLK =  np.array([poligonoPartida[1],poligonoPartida[2]])
		ditanciaEnX = self.lineaDePintadoLK[1][0] - self.lineaDePintadoLK[0][0]
		ditanciaEnY = self.lineaDePintadoLK[1][1] - self.lineaDePintadoLK[0][1]
		self.numeroDePuntos = 9
		self.stepX = ditanciaEnX//self.numeroDePuntos
		self.stepY = ditanciaEnY//self.numeroDePuntos
		self.lk_params = dict(  winSize  = (15,15),
								maxLevel = 7,
								criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
		# erase 4 lines featureparams
		self.feature_params = dict( maxCorners = self.numeroDePuntos+1,
									qualityLevel = 0.3,
									minDistance = 7,
									blockSize = 7 )
		self.lineaDeResguardoDelantera = np.array([self.lineaDePintadoLK[0]])
		self.restablecerLineaLK()

	def inicializar(self,):
		self.restablecerLineaLK()

	def restablecerLineaLK(self,):
		self.lineaDeResguardoDelantera = np.array([[self.lineaDePintadoLK[0]]])
		for numeroDePunto in range(1,self.numeroDePuntos+1):
			self.lineaDeResguardoDelantera = np.append(self.lineaDeResguardoDelantera,[[self.lineaDePintadoLK[0]+numeroDePunto*np.array([self.stepX,self.stepY])]],axis=0)

	def evolucionarLineaVigilancia(self,imagenActual):
		# la imagen introducida esta en RGB, 240,320,3
		huboCambio = False
		imagenActualEnGris = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)
		lineaAcondicionada = []
		for array in self.lineaDeResguardoDelantera:
			lineaAcondicionada.append([list(array[0]*1.0)])
		lineaAcondicionada = np.array(lineaAcondicionada)
		print('lineaAcondicionada ',lineaAcondicionada)
		print('lineaAcondicionada ',type(lineaAcondicionada))
		print('lineaAcondicionada ',lineaAcondicionada.shape)
		goodf = cv2.goodFeaturesToTrack(imagenActualEnGris, mask = None, **self.feature_params)
		print('goodf',goodf)
		print('good',type(goodf))
		print('good',goodf.shape)
		print(self.imagenAuxiliar.shape)
		print(imagenActualEnGris.shape)
		#self.lineaDeResguardoDelantera, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliar, imagenActualEnGris, lineaAcondicionada.astype(int), None, **self.lk_params)
		#self.lineaDeResguardoDelantera = lineaAcondicionada.astype(int)
		#print('Nuevos puntos: ',self.lineaDeResguardoDelantera)
		self.imagenAuxiliar = imagenActualEnGris
		return huboCambio

	def obtenerLinea(self):
		return self.lineaDeResguardoDelantera

if __name__ == '__main__':
	try:
		nombreDeVideo = directorioDeVideos+'/'+sys.arg[1]
		camaraParaFlujo = cv2.VideoCapture(nombreDeVideo)
		archivoParametrosACargar = nombreDeVideo[:-4]+'.npy'
	except:
		nombreDeVideo = directorioDeVideos+'/mySquare.mp4'
		camaraParaFlujo = cv2.VideoCapture(directorioDeVideos+'/mySquare.mp4')
		archivoParametrosACargar = nombreDeVideo[:-4]+'.npy'

	parametrosInstalacion = np.load(archivoParametrosACargar)
	poligonoSemaforo = parametrosInstalacion[0]
	verticesPartida = parametrosInstalacion[1]
	verticesLlegada = parametrosInstalacion[2]
	
	ret, capturaDeFlujoInicial = camaraParaFlujo.read()
	framePrueba = cv2.resize(capturaDeFlujoInicial,(320,240))
	## Creo los objetos:
	miPolicia = PoliciaInfractor(framePrueba,verticesPartida,verticesLlegada)
	tiempoAuxiliar = time.time()

	while True:
		ret, frameActual = camaraParaFlujo.read()
		frameActual = cv2.resize(frameActual,(320,240))
		miPolicia.evolucionarLineaVigilancia(frameActual)
		toPlot = miPolicia.obtenerLinea()
	
		for punto in toPlot:
			frameActual = cv2.circle(frameActual,tuple(punto[0]), 4, (0,0,0), -1)# tuple(map(tuple,toPlot))

		cv2.imshow('Visual',frameActual)
		
		ch = 0xFF & cv2.waitKey(5)
		if ch == ord('q'):
			break
		#print(time.time()-tiempoAuxiliar)
		tiempoAuxiliar = time.time()
		while time.time()-tiempoAuxiliar<0.033:
			True
		#a-=1