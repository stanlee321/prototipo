import os
import sys
import cv2
import time
import numpy as np
from perspective import Perspective
from flowdetector import FlowDetector

class AreaDeResguardo():
	"""
	Includes some extra methods util for automovil track
	"""
	def __init__(self,imagenDeInicializacion,maximoPuntos,poligonoDePartida,poligonoDeLlegada=[[0,0]]):
		# El poligono
		self.imagenAuxiliarEnGrises = cv2.cvtColor(imagenDeInicializacion, cv2.COLOR_BGR2GRAY)
		[self.height,self.width] = imagenDeInicializacion.shape[:2]
		#print('AQUIIIIIIIIIIIIIIII:',self.width,self.height)
		if poligonoDePartida == None:
			#print('No se utilizara mascara')
			self.mascara = None
			self.regionDeInteres = np.array([[0,0],[0,240],[320,240],[320,0]])
		else:
			self.regionDeInteres = np.array(poligonoDePartida)
			self.mascara = np.zeros_like(self.imagenAuxiliarEnGrises)
			cv2.fillPoly(self.mascara,[self.regionDeInteres],255)
			#print('Mascara creada con exito')

		self.poligonoDeLlegada = np.array(poligonoDeLlegada)
		# Auxiliares
		self.feature_params = dict( maxCorners = maximoPuntos,
									qualityLevel = 0.3,
									minDistance = 7,
									blockSize = 7 )

		self.lk_params = dict(  winSize  = (15,15),
								maxLevel = 2,
								criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

		self.color = np.random.randint(0,255,(50,3))		# Se empleara un color nuevo por infraccion
		self.zonaPartida = Perspective(self.regionDeInteres)
		self.imagenAuxiliarZonaPartida = self.zonaPartida.generarRegionNormalizada(imagenDeInicializacion)
		self.flujoEnLaPartida = FlowDetector(180)
		self.flujoEnLaPartida.inicializarClase(self.imagenAuxiliarZonaPartida)
		
	def obtenerPuntosAseguirDe(self,CVImagen):
		self.imagenAuxiliarEnGrises = cv2.cvtColor(CVImagen, cv2.COLOR_BGR2GRAY)
		# Aqui deberiamos agregar un filtro que retire los puntos de afuera del ROI
		caracteristicasASeguir = self.obtenerUltimosPuntosASeguir()
		return caracteristicasASeguir

	def obtenerUltimosPuntosASeguir(self):
		caracteristicasASeguir = cv2.goodFeaturesToTrack(self.imagenAuxiliarEnGrises, mask = self.mascara, **self.feature_params)
		try:
			puntosExtraidos = caracteristicasASeguir.ravel().reshape(caracteristicasASeguir.ravel().shape[0]//2,2)
			#print('PUNTOS CREADOS: ',caracteristicasASeguir)
		except:
			print('NO OBTUVE PUNTOS CARACTERISTICOS')
		#for punto in puntosExtraidos:
		#	cv2.circle(self.imagenAuxiliarEnGrises, tuple(punto), 1, 0, -1)
		#cv2.imshow('PuntosEncontradosVisual',self.imagenAuxiliarEnGrises)
		
		return np.array([caracteristicasASeguir])

	def encontrarObjeto(self,imagenActual,caracteristicasASeguir):
		imagenActualEnGris = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)
		nuevaUbicacion, activo, err = cv2.calcOpticalFlowPyrLK(self.imagenAuxiliarEnGrises, imagenActualEnGris, caracteristicasASeguir, None, **self.lk_params)
		
		return np.array([nuevaUbicacion]), activo, err

	def encontrarObjetoYPaso(self,imagenActual,caracteristicasASeguir):
		nuevaUbicacion, activo, err = self.encontrarObjeto(imagenActual,caracteristicasASeguir)
		self.imagenAuxiliarEnGrises = imagenActualEnGris
		return nuevaUbicacion, activo, err

	def calcularFlujoTotalEnFrame(self,CVImagen):
		self.imagenAuxiliarZonaPartida = self.zonaPartida.generarRegionNormalizada(CVImagen)
		total_flow, modulo, lines = self.flujoEnLaPartida.procesarNuevoFrame(self.imagenAuxiliarZonaPartida) # Obtengo vector y parametros de flujo
		momentumAutomovil, vectorSuave, vectorRuidoso, velocidad, indiceFrameActual = self.flujoEnLaPartida.procesarFlujoEnTiempoReal(total_flow)	# Proyecto y filtroFiltro 
		return vectorRuidoso, velocidad,-indiceFrameActual

	def calcularFlujoTotalEnFrameYPaso(self,CVImagen):
		vectorRuidoso, velocidad, indiceFrameActual = self.calcularFlujoTotalEnFrame(CVImagen)
		self.imagenAuxiliarEnGrises = cv2.cvtColor(CVImagen, cv2.COLOR_BGR2GRAY)
		###### WARNING, DOUBLE CVT TRANSFORM ALERT ######
		return vectorRuidoso, velocidad, indiceFrameActual

	def encontrarObjetosYCalcularFlujo(self,imagenActual,infraccionesListOfDict):
		numeroDeInfracciones = 0
		listoParaTomarFoto = False
		for infraction in infraccionesListOfDict:
			#print(infraction['estado'],' :\t',infraction['desplazamiento'].shape,infraction['frameInicial'],' a ',infraction['frameFinal'],'\t',infraction['name'])
			numeroDeInfracciones+=1
			# Para cada infraccion tomo el ultimo elemento lo proceso con la imagen actual y lo appendo al mismo lugar
			if infraction['estado']=='Candidato':
				nuevoVector,act,err = self.encontrarObjeto(imagenActual,infraction['desplazamiento'][-1])

				nuevoVectorCompleto= np.append(infraction['desplazamiento'],nuevoVector,axis=0)
				infraction['desplazamiento'] = nuevoVectorCompleto
				# Si el nuevo vector esta dentro del poligono de llegada (numero mayor o igual a cero se declara como confirmado)
				numeroDePuntos = len(nuevoVector[0])
				puntosFueraFrame = 0
				puntosFueraPoligonoInicial = 0
				for pattern in nuevoVector[0]:
					#print(pattern)
					x,y = pattern.ravel()
					#print(pattern)
					#print((x,y))
					#print(cv2.pointPolygonTest(self.poligonoDeLlegada,(x,y),True))
					if cv2.pointPolygonTest(self.poligonoDeLlegada,(x,y),True)>=0:
						nuevoItem = {'estado':'Confirmando'}
						infraction.update(nuevoItem)
					if cv2.pointPolygonTest(self.regionDeInteres,(x,y),True)<0:
						puntosFueraPoligonoInicial+=1

					if self.estaFueraDeFrame((x,y)):
						puntosFueraFrame += 1
					#if self.estaFueraDeFrame((x,y)):
					#	nuevoItem = {'estado':'Viro Fuera'}
					#	infraction.update(nuevoItem)
				#print('Puntos adentro del frame: ',numeroDePuntos)
				if nuevoVectorCompleto.shape[0]>250:
					nuevoItem = {'estado':'Timeout'}
					infraction.update(nuevoItem)
				if puntosFueraFrame >= numeroDePuntos:
					nuevoItem = {'estado':'Giro'}
					infraction.update(nuevoItem)
				if puntosFueraPoligonoInicial >= numeroDePuntos-2:
					listoParaTomarFoto = True

		#for i in range(numeroDeInfracciones):
			#sys.stdout.write("\033[F")
			#pass
						
		vectorRuidoso, velocidad, indiceFrameActual = self.calcularFlujoTotalEnFrame(imagenActual)
		imagenActualEnGris = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)
		if listoParaTomarFoto == True:
			indiceFrameActual = -10
		return vectorRuidoso,velocidad,indiceFrameActual

	def encontrarObjetosYCalcularFlujoYPaso(self,imagenActual,infraccionesListOfDict):
		vectorRuidoso, velocidad,indiceFrameActual = self.encontrarObjetosYCalcularFlujo(imagenActual,infraccionesListOfDict)
		self.imagenAuxiliarEnGrises = cv2.cvtColor(imagenActual, cv2.COLOR_BGR2GRAY)
		# Si los puntos estan en el lugar optimo para una infraccion se manda -10
		return vectorRuidoso, velocidad,indiceFrameActual

	def estaFueraDeFrame(self,tupleVector):
		x = tupleVector[0]
		y = tupleVector[1]
		if (x<0) | (y<0) | (x>self.width) | (y>self.height):
			return True
		else:
			return False

if __name__ == '__main__':
	"""
	Demostracion:
	"""
	directorioDeVideos = os.getenv('HOME')+'/trafficFlow/trialVideos'
	cap = cv2.VideoCapture(directorioDeVideos+'/{}'.format(sys.argv[1]))
	# Create some random colors
	ret, old_frame = cap.read()
	seguimiento = AreaDeResguardo(old_frame,8,0)		#[[10,240],[100,240],[320,0],[240,0]]
	caracteristicasASeguir = seguimiento.obtenerPuntosAseguirDe(old_frame)
	#print(caracteristicasASeguir)
	
	# Create a mask image for drawing purposes
	mask = np.zeros_like(old_frame)
	tiempoAuxiliar = time.time()
	while(1):
	    ret,frame = cap.read()
	    #print(caracteristicasASeguir,type(caracteristicasASeguir))
	    #print('SHAPE',caracteristicasASeguir.shape)
	    nuevaUbicacion, activo, err = seguimiento.encontrarObjeto(frame,caracteristicasASeguir)
	    #print(nuevaUbicacion)

	    # Select good points
	    good_new = nuevaUbicacion#[activo==1]
	    #print(type(nuevaUbicacion),nuevaUbicacion)
	    #print(type(good_new),good_new)
	    good_old = caracteristicasASeguir#[activo==1]
	    # draw the tracks
	    for i,(new,old) in enumerate(zip(good_new,good_old)):
	        #print('Nuevo: ',new)
	        a,b = new.ravel()
	        #print(new.ravel())
	        c,d = old.ravel()
	        mask = cv2.line(mask, (a,b),(c,d), seguimiento.color[i].tolist(), 2)
	        frame = cv2.circle(frame,(a,b),5,seguimiento.color[i].tolist(),-1)
	    img = cv2.add(frame,mask)
	    cv2.imshow('frame',img)
	    k = cv2.waitKey(30) & 0xff
	    if k == ord('q'):
	        break
	    # Now update the previous frame and previous points
	    tiempoAuxiliar = time.time()
	    caracteristicasASeguir = good_new.reshape(-1,1,2)
	    #time.sleep(0.2)
	cv2.destroyAllWindows()
	cap.release()

