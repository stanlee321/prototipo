# Prueba camara
import os
import sys
import time
import picamera
import numpy as np
import io, time, picamera, cv2
import matplotlib.pyplot as graficaActual

directorioDeReporte = os.getenv('HOME')+'/imagenes'

piCamera = False
resolucion = 5
numeroImagenes = 6
resoluciones = [0.1,0.3,1,1.5,2,5,8]

def __main_function__(resolution):
	resolucion = resolution
	print('Iniciando Prueba')
	ordenada1 = []
	ordenada2 = []
	ordenada3 = []
	# Encontrando la resolucion correspondiente:
	if resolucion == 5: 
		width = 2592
		height = 1944
		fov = 'full'
	elif resolucion == 8:
		width = 3280
		height = 2464
		fov = 'full'
	elif resolucion == 2:
		width = 1920
		height = 1080
		fov = 'partial'
	elif resolucion == 1.5:
		width = 1640
		height = 922
		fov = 'full'
	elif resolucion == 1:
		width = 1280
		height = 720
		fov = 'partial'
	elif resolucion == 0.3:
		width = 640
		height = 480
		fov = 'partial'
	elif resolucion == 0.1:
		width = 320
		height = 240
		fov = 'partial'

	print('Seleccionado ', width,' x ',height,' at ', fov, ' FOV')
	contador = 0
	
	miCamara = cv2.VideoCapture(1) 
	miCamara.set(cv2.CAP_PROP_FRAME_WIDTH, width) 
	miCamara.set(cv2.CAP_PROP_FRAME_HEIGHT, height) 
	for captura in range(numeroImagenes):
		print('captura Numero: ', captura)
		# Read plate
		tiempoAuxiliar = time.time()
		_, placa = miCamara.read()
		tiempoGuardado = time.time()-tiempoAuxiliar
		print('Se guardo en SD en ',tiempoGuardado,' con shape: ', placa.shape)
		ordenada1.append(tiempoGuardado)
		#placaActual = placa[self.primerPunto[1]:self.segundoPunto[1], self.primerPunto[0]: self.segundoPunto[0]]
		#self.input_q.put((placaActual, captura, self.saveDir, self.fechaInfraccion))
	miCamara.release()
	print('Iniciando prueba con Picamera')
	#Prueba con stream
	frames = 0
	stream = io.BytesIO()
	with picamera.PiCamera() as camera:
		camera.resolution = (width, height)
		camera.start_preview()
		time.sleep(2)
		start = time.time()
		for i in range(0, numeroImagenes):
			tiempo = time.time()
			camera.capture(stream, format='jpeg')
			capturadoEn = time.time() - tiempo
			stream.seek(0)
			data = np.fromstring(stream.getvalue(), dtype=np.uint8)
			image = cv2.imdecode(data, 1)
			(h,w,cols) = image.shape
			(xc,yc) = (h/2,w/2)
			frames = frames + 1
			decodeEn = time.time() - tiempo
			print('Capturado en ',capturadoEn,' total por imagen ',decodeEn)
			ordenada2.append(decodeEn)
			#print("%02d center: %s (BGR)" % (frames,image[xc,yc]))

	print('Framerate %.2f fps' %  (frames / (time.time() - start)) )
	# 0.65 fps for 8MP
	# 1.51 fps for 0.3MPx for stream
	print('Iniciando prueba con Picamera direct SD')
	
	camera = picamera.PiCamera()
	camera.led= False
	camera.resolution = (width, height)
	output = np.empty((height, width, 3), dtype=np.uint8)
	while True:
		tiempoAuxiliar = time.time()
		camera.capture(directorioDeReporte+'/piCamMod_{}.jpg'.format(contador))
		#camera.capture(output, 'bgr')
		tiempoGuardado = time.time()-tiempoAuxiliar
		print('Se guardo en SD en ',tiempoGuardado)
		ordenada3.append(tiempoGuardado)
		if contador >= numeroImagenes-1:
			break
		contador +=1
	indice = range(len(ordenada1))
	return [indice,ordenada1,ordenada2,ordenada3]
	

if __name__ == '__main__':
	for input in sys.argv:
		if input == 'picamera':
			piCamera = True
		if 'mp' in input:
			resolucion = float(input[:-2])
			print('Introducido ', resolucion,' MPx')
		if input == 'Show':
			mostrarImagen = True
		if 'pic' in input:
			numeroImagenes = int(input[:-3])
		if input == 'noDraw':
			noDraw = True

	if resolucion == 0:
		print('Modo Manual')
		for i in resoluciones:
			__main_function__(i)

	else:
		vector = __main_function__(resolucion)

		graficaActual.cla()
		ax1 = self.figure.add_subplot(111)
		i = vector[0]#range(len(listaDatos[0]))
		cv0 = vector[1]
		stre = vector[2]
		picam = vector[3]
		graficaActual.title(self.titulo)
		graficaActual.ylabel('$Tiempo [s]$')
		graficaActual.xlabel('Lectura')
		graficaActual.grid()
		graficaActual.plot(i,cv0,label='CV2')
		graficaActual.plot(i,stre,label='Stream')
		graficaActual.plot(i,picam,label='PiCam')
		#graficaActual.plot(t,v,'b.-',label='v',t,c,'y.-',label='i',t,T,'r.-',label='T',t,r,'g.-',label='rpm')
		graficaActual.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),ncol=3, fancybox=True, shadow=True)

		graficaActual.savefig(directorioDeReporte+'_'+self.miTarjetaAdquisicion.fechaHora+'.pdf', bbox_inches='tight')

		graficaActual.gcf().clear()