import numpy as np
import cv2
import time
import random
# Draw a diagonal blue line with thickness of 5 px
from abc import ABCMeta, abstractmethod

class Box():
	"""
	Create a Box where you can put information from text to color.
	Use draw() method for get an array or draw the boxes and text to the exterior world.
	"""

	__metaclass__ = ABCMeta


	def __init__(self, text, p1 = None, p2= None):
		self.text = text
		self.color = None
		self.fillOrSize = 1 # -1 for full, and 1 for empy color
		self.font = cv2.FONT_HERSHEY_SIMPLEX
		self.p1 = p1
		self.p2 = p2

	@staticmethod
	def getCoordenadas(p1,p2):
		coor = (p2[0]  - 35, p2[1] + 15 )
		return coor

	def draw(self, image):
		coordenadas = Box.getCoordenadas(self.p1, self.p2)
		if self.color != None:
			mask = cv2.rectangle(image,(self.p1[0],self.p1[1]+23),(self.p2[0],self.p2[1]+23),self.color,-1)
		
		if len(str(self.text))>1:
			mask = cv2.putText(image, str(self.text), coordenadas, self.font, 0.4,(255,255,255),1,cv2.LINE_AA)
		
			return mask
class InfoBar(Box):
	"""
	Create information Bar from Box method, return set of boxes
	in the form of a dict where his elements id, value  goes from 0 to 7
	and correspond to every box created
	"""

	def __init__(self, height, l = 20):

		self.height = height
		self.lenght = l
		self.setOfBoxes = {}
		self.createBoxes()

	def createBoxes(self):
		for i in range(8):
			p1 = (i*(self.lenght + self.lenght)  , self.height - self.lenght)
			p2 = ((i+1)*(self.lenght + self.lenght) , self.height)
			box = Box(text=i, p1 = p1, p2 = p2)
			self.setOfBoxes[i] = box
		return self.setOfBoxes

	def draw(self, image):

		for k, v in self.setOfBoxes.items():
			mask = v.draw(image)
		return mask

class ProgressBar():
	"""
	Draw a responsibe progress bar, use draw() method to draw or return array to
	the exterior world.
	"""
	def __init__(self, w = 320, h = 280, magnitude = 10):
		self.h = h
		self.magnitude = magnitude
		self.p1 = (0, h-25)
		self.color = (0,255,0)

	def draw(self, image):
		self.image = cv2.line(image, self.p1, (self.magnitude, self.h-25), self.color, 2)
		return self.image

class Poligono():
	"""
	Crate a  weighted poligono , use draw() method to draw it or return an array to
	the exterior world. 

	"""
	def __init__(self, poligono=None) :
		self.data =  poligono
		self.color = (255,0,0)
	def draw(self, image):
		miCapa = image.copy()
		opacity = 0.11
		cv2.fillPoly(miCapa, np.array([self.data]),self.color, 1)
		newImage = cv2.addWeighted(miCapa, opacity, image, 1 - opacity, 0, image)
		return newImage


class CrearPunto():
	def __init__(self, image, center = None,radious = 5, color = (0,0,255)):
		self.image = image
		self.center = center
		self.radious = 5
		self.color = (0,0,255)
	def draw(self):
		self.image = cv2.circle(self.image, tuple(self.center), self.radious, self.color, -1)
		return self.image


class CrearConjuntoDePuntos():
	"""
	Create information Bar from Box method, return set of boxes
	in the form of a dict where his elements id, value  goes from 0 to 7
	and correspond to every box created
	"""

	def __init__(self, image, center = None, list_of_pts = None):
		self.image = image 
		self.setOfPoints = {}
		self.centers = list_of_pts
		self.radious = 10
		self.color = (0,0,255)
		self.numeroDePuntos = len(list_of_pts)
	def createPoints(self):
		centers = self.centers
		radious = self.radious
		color = self.color
		counter = 0
		for i in range(self.numeroDePuntos):
			punto = CrearPunto(image = self.image, center = centers[i], radious = radious, color = color)
			self.setOfPoints[i] = punto
		return self.setOfPoints

class VisualLayer():

	"""
	Interface, this method create a mask to allocate and draw all the above methods

	Atributes:
		self.imageInput: Pointer where you create the interface over which the 
						rest of objects will be are created.
		self.boxes:		Pointer where you will allocate boxes objects created over self.imageInput
		self.bar:		Similar to boxes, this act as a progress bar for the exterior world.
		self.poligono:  Similar to boxes, this draw a transparent rectangle to the self.imageInput

	"""
	def __init__(self):

		self.imageInput = None
		self.height, self.width  = None, None
		self.boxes = None
		self.bar = None
		self.poligono = None
		self.puntos = None
		self.puntosAdibujar = None

		self.list_of_polis = []

	def crearMascaraCompleta(self, size = (240,320)):
		self.height, self.width = size[0], size[1]
		self.imageInput = VisualLayer.crearMascara(size=(self.height, self.width))


	@staticmethod
	def crearMascara(size = (240,320) ):

		"""
		Create zeros like mask with a 10 percent more height that nominal
		for purposes of drawing with some overlaping with ... input frame comming from the
		exterior world .
		"""
		# Create some local width and height for the zeros like image.
		height, width = size[0], size[1]
		# Reemplasing the __init__ .self.height and __init__ .self.width with 
		# this new height and width.

		# Create zeros like mask
		mask = np.zeros((int(height + 0.10 *height), width,3), np.uint8)

		# Reemplze __init__.self.imageInput pointer like with this zeros like mask.
		return  mask



	def crearBarraInformacion(self, height = 240):
		# Create information Boxes

		self.boxes = InfoBar( height = height , l = 20 )
		

	def agregarTextoEn(self, text, numeroDeCaja):
		# Put text into some box[index].text

		self.boxes.setOfBoxes[numeroDeCaja].text = text

	def establecerColorFondoDe(self,backgroudColour = (0,0,255), numeroDeCaja=0, fill = -1):
		
		# Set some text and fill color of some numeroDeCaja box
		self.boxes.setOfBoxes[numeroDeCaja].color = backgroudColour
		self.boxes.setOfBoxes[numeroDeCaja].fillOrSize = fill

	def crearBarraDeProgreso(self):
		# Create progress Bar
		self.bar = ProgressBar(w = self.width, h = int(self.height+0.10*self.height), magnitude = 10)

	def establecerMagnitudBarra(self, magnitude = 10):
		# set new magnitude from the exterior world
		self.bar.magnitude = magnitude

	def ponerPoligono(self, poligono = None):
		# Create and set poligono Object
		if poligono.any() != None:
			self.poligono = Poligono( poligono)
			self.list_of_polis.append(self.poligono)
		else:
			pass

		#return self.poligono.draw()

	def ponerPuntos(self, points = None ):

		self.puntosAdibujar = points
		if points  != None:
			conjuntoDePuntos = CrearConjuntoDePuntos(image = self.imageInput, list_of_pts = self.puntosAdibujar )
			self.puntos = conjuntoDePuntos.createPoints()
		else:
			pass

	def aplicarMascaraActualAFrame(self, frameActual):
		"""
		Inputs one frame from the exterior world and put a MASK 
		over it, once this method is called from the exterior world,
		remplace the pixels from zeros_like (width and height) pointer 
		with the pixels from frameActual.

		"""

		# Refresh the mask
		self.imageInput = VisualLayer.crearMascara()


		# Resize this input frame from the exterior world to normal (320,280)
		# input size.

		frameActual = cv2.resize(frameActual, (self.width, self.height))
		
		width, height, _ = frameActual.shape

		# Fill this pixels with frameActual pixels
		self.imageInput[:width, : height] = frameActual


	def aplicarBarraDeEstados(self, image):
		# iterate over all the boxes and return a mask with 
		# all theses drawed on (mask + frameActual)
		return self.boxes.draw(image)


	def aplicarPolis(self,image):
		# Drw the bottom boxes
		for poli in self.list_of_polis:
			mask = poli.draw(image = image)
		return mask

	def createPoints(self):
		"""IF ERROR HAPPENS HERE Reemplaze the commented line
		""" 
		for index in range(len(self.puntos)):
		#for index in range(len(self.puntos.any())):
			mask = self.puntos[index].draw()
		return mask

	def aplicarRectangulos(self, image, boxes):
		# Draw Rectangles into the debug mask
		for rect in boxes :
			x,y,w,h = rect[0]
			centroid  = rect[1]
			cv2.rectangle(image, (x,y),(x+w-1, y+h-1),(0,0,255),1)
			cv2.circle(image, centroid,2,(0,255,0),-1)



	def aplicarTodo(self):
		# Return all the draw() aviable methos from every 
		# object and draw over (mask + frameActual)

		#self.boxes.image = self.crear()
		mask = self.aplicarBarraDeEstados(image = self.imageInput)
		mask = self.bar.draw(image = self.imageInput)
		#mask = self.poligono.draw(image = self.imageInput)
		mask = self.aplicarPolis(image = self.imageInput)
		
		#mask = self.aplicarRectangulos(self.imageInput, self.boxes)

		# CREATE POINTS
		#if self.puntosAdibujar != None:
		#	mask = self.createPoints()
		#else:
		#	pass
		return mask


	def cleanPoints(self):

		self.puntosAdibujar = None

		self.__delete__()


	def __delete__(self,i):
		""" Delete self.puntos dict object 
		"""
		del self.box[i].text



if __name__ == '__main__':
	cap = cv2.VideoCapture('./mySquare.mp4')
	data = np.load('mySquare.npy')
	data1 = data[0][1]
	data2 = data[0][2]
	vis = VisualLayer()
	vis.crearMascaraCompleta(size = (240,320) )
	vis.crearBarraInformacion(height = 240)
	vis.ponerPuntos( points = [[200,11],[150,100],[200,200]]) # HERE PUT TUPLES INSIDE of LIST 
	vis.crearBarraDeProgreso()
	vis.ponerPoligono(data1)
	vis.ponerPoligono(data2)
	counter  = 0
	mag = 0
	while True:
		_, img = cap.read()
		#time.sleep(0.1)
		t1 = time.time()



		vis.establecerColorFondoDe(backgroudColour = (255,255,0), numeroDeCaja = 0)
		vis.aplicarMascaraActualAFrame(frameActual = img)
		vis.agregarTextoEn(":V", 5)

		cv2.imshow('mask_image',vis.aplicarTodo())
		vis.establecerMagnitudBarra(magnitude = mag)
		mag +=1
		if mag >= 150:
			mag -=2

		counter +=1	
		if counter == 100:
			#vis.cleanPoints()
			vis.agregarTextoEn("odio", 1)
		if counter == 200:
			vis.agregarTextoEn("asdf", 1)
			vis.establecerColorFondoDe(backgroudColour=(255,0,0))

		vis.agregarTextoEn(counter, 2)

		t2 = time.time()

		print('time is:',(t2-t1)*1000)
		ch = 0xFF & cv2.waitKey(5)
		if ch == 27:
			break
	cv2.destroyAllWindows()
	c = cv2.waitKey(0)

